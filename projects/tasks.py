import collections
import json
import secrets
import string

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

import apps.tasks as apptasks
from apps.controller import delete
from apps.helpers import create_app_instance
from studio.utils import get_logger

from .exceptions import ProjectCreationException
from .models import S3, Environment, Flavor, MLFlow, Project

logger = get_logger(__name__)

Apps = apps.get_model(app_label=settings.APPS_MODEL)
AppInstance = apps.get_model(app_label=settings.APPINSTANCE_MODEL)

User = get_user_model()


@shared_task
def create_resources_from_template(user, project_slug, template):
    logger.info("Create Resources From Project Template...")
    
    ## THIS IS JUST FOR TESTING PURPOSES
    project = Project.objects.get(slug=project_slug)
    logger.critical("CREATING A VOLUME FROM FORM")
    from apps.forms import VolumeForm
    from apps.models import Subdomain, AppStatusNew
    from apps.tasks import deploy_resource_new
    from django.core import serializers
    
    data = {
        "name": "project-vol",
        "size": 5
    }
    form = VolumeForm(data)
    if form.is_valid():
        logger.critical("FORM IS VALID YEEHOOO")
        
        instance = form.save(commit=False)
        
        # THIS COULD ALL BE A FUNCTION I GUESS
        subdomain, created = Subdomain.objects.get_or_create(subdomain=form.cleaned_data.get("subdomain"), project=project)
        status = AppStatusNew.objects.create()
        
        instance.app = Apps.objects.get(slug="volumeK8s")
        instance.chart = instance.app.chart # Keep history of the chart used, since it can change in App.
        instance.project = project
        
        user_obj = User.objects.get(username=user)
        instance.owner = user_obj
        instance.subdomain = subdomain
        instance.app_status = status
        instance.save()

        form.save_m2m()
        
        instance.set_k8s_values()
        ####
        
        # If your model form uses many-to-many fields, you might need to call save_m2m()
        

        serialized_instance = serializers.serialize("json", [instance])
        
        deploy_resource_new.delay(serialized_instance)
        
        
    else:
        logger.critical("FORM IS INVALID NOOOOOOOOOOOOOOOOOOOOO!!!!!")             
    
    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    parsed_template = template.replace("'", '"')
    template = decoder.decode(parsed_template)
    alphabet = string.ascii_letters + string.digits
    
    logger.info("Parsing template...")
    count = 0
    for key, item in template.items():
        logger.info("Key %s", key)
        if "flavors" == key:
            flavors = item
            logger.info("Flavors: %s", flavors)
            # TODO: potential bug. This for statement overrides variables in the outer loop.
            for key, item in flavors.items():
                flavor = Flavor(
                    name=key,
                    cpu_req=item["cpu"]["requirement"],
                    cpu_lim=item["cpu"]["limit"],
                    mem_req=item["mem"]["requirement"],
                    mem_lim=item["mem"]["limit"],
                    gpu_req=item["gpu"]["requirement"],
                    gpu_lim=item["gpu"]["limit"],
                    ephmem_req=item["ephmem"]["requirement"],
                    ephmem_lim=item["ephmem"]["limit"],
                    project=project,
                )
                flavor.save()
        elif "environments" == key:
            environments = item
            logger.info("Environments: %s", environments)
            for key, item in environments.items():
                try:
                    app = Apps.objects.filter(slug=item["app"]).order_by("-revision")[0]
                except Exception as err:
                    logger.error(
                        ("App for environment not found. item.app=%s project_slug=%s " "user=%s err=%s"),
                        item["app"],
                        project_slug,
                        user,
                        err,
                        exc_info=True,
                    )
                    raise
                try:
                    environment = Environment(
                        name=key,
                        project=project,
                        repository=item["repository"],
                        image=item["image"],
                        app=app,
                    )
                    environment.save()
                except Exception as err:
                    logger.error(
                        (
                            "Failed to create new environment: "
                            "key=%s "
                            "project=%s "
                            "item.repository=%s "
                            "image=%s "
                            "app=%s "
                            "user%s "
                            "err=%s"
                        ),
                        key,
                        project,
                        item["repository"],
                        item["image"],
                        app,
                        user,
                        err,
                        exc_info=True,
                    )
                    
        elif "apps" == key:
            apps = item
            logger.info("Apps: %s", apps)
            for key, item in apps.items():
                app_name = key
                data = {"app_name": app_name, "app_action": "Create"}
                if "credentials.access_key" in item:
                    item["credentials.access_key"] = "".join(secrets.choice(alphabet) for i in range(8))
                if "credentials.secret_key" in item:
                    item["credentials.secret_key"] = "".join(secrets.choice(alphabet) for i in range(14))
                if "credentials.username" in item:
                    item["credentials.username"] = "admin"
                if "credentials.password" in item:
                    item["credentials.password"] = "".join(secrets.choice(alphabet) for i in range(14))

                data = {**data, **item}
                logger.info("DATA TEMPLATE")
                logger.info(data)

                user_obj = User.objects.get(username=user)

                app = Apps.objects.filter(slug=item["slug"]).order_by("-revision")[0]

                (
                    successful,
                    _,
                    _,
                ) = create_app_instance(
                    user=user_obj,
                    project=project,
                    app=app,
                    app_settings=app.settings,
                    data=data,
                    wait=True,
                )

                if not successful:
                    logger.error("create_app_instance failed")
                    raise ProjectCreationException

        elif "settings" == key:
            logger.info("PARSING SETTINGS")
            logger.info("Settings: %s", settings)
            if "project-S3" in item:
                logger.info("SETTING DEFAULT S3")
                s3storage = item["project-S3"]
                # Add logics: here it is referring to minio basically.
                # It is assumed that minio exist, but if it doesn't
                # then it blows up of course
                s3obj = S3.objects.get(name=s3storage, project=project)
                project.s3storage = s3obj
                project.save()
            if "project-MLflow" in item:
                logger.info("SETTING DEFAULT MLflow")
                mlflow = item["project-MLflow"]
                mlflowobj = MLFlow.objects.get(name=mlflow, project=project)
                project.mlflow = mlflowobj
                project.save()
        else:
            logger.error("Template has either not valid or unknown keys")
            raise ProjectCreationException

    project.status = "active"
    project.save()


@shared_task
def delete_project_apps(project_slug):
    project = Project.objects.get(slug=project_slug)
    apps = AppInstance.objects.filter(project=project)
    for app in apps:
        apptasks.delete_resource.delay(app.pk)


@shared_task
def delete_project(project_pk):
    logger.info("SCHEDULING DELETION OF ALL INSTALLED APPS")
    project = Project.objects.get(pk=project_pk)
    delete_project_apps_permanently(project)

    project.delete()


@shared_task
def delete_project_apps_permanently(project):
    apps = AppInstance.objects.filter(project=project)

    for app in apps:
        helm_output = delete(app.parameters)
        logger.info(helm_output.stderr.decode("utf-8"))
