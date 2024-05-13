import collections
import json
import string

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model


from apps.helpers import create_instance_from_form
from studio.utils import get_logger

from .exceptions import ProjectCreationException
from .models import Environment, Flavor, Project

from apps.constants import SLUG_MODEL_FORM_MAP
from apps.models import VolumeInstance, AbstractAppInstance

from apps.tasks import delete_resource

logger = get_logger(__name__)

Apps = apps.get_model(app_label=settings.APPS_MODEL)
AppInstance = apps.get_model(app_label="apps.AppInstance")

User = get_user_model()


@shared_task
def create_resources_from_template(user, project_slug, template):
    logger.info("Create Resources From Project Template...")
    
    ## THIS IS JUST FOR TESTING PURPOSES
    project = Project.objects.get(slug=project_slug)
    logger.critical("CREATING A VOLUME FROM FORM")

         
    
    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    parsed_template = template.replace("'", '"')
    template = decoder.decode(parsed_template)
    alphabet = string.ascii_letters + string.digits
    
    
    
    
    logger.info("Creating Project Flavors...")
    flavor_dict = template.get("flavors", {})
    for flavor_name, resources in flavor_dict.items():
        logger.info("Creating flavor ")
        logger.info(f"Creating flavor: {flavor_name}")
        flavor = Flavor(
            name=flavor_name,
            cpu_req=resources["cpu"]["requirement"],
            cpu_lim=resources["cpu"]["limit"],
            mem_req=resources["mem"]["requirement"],
            mem_lim=resources["mem"]["limit"],
            gpu_req=resources["gpu"]["requirement"],
            gpu_lim=resources["gpu"]["limit"],
            ephmem_req=resources["ephmem"]["requirement"],
            ephmem_lim=resources["ephmem"]["limit"],
            project=project,
        )
        flavor.save()
    
    
    
    apps_dict = template.get("apps", {})
    logger.info("Initiate Creation of Project Apps...")
    form_dict = {}
    for app_slug, data in apps_dict.items():
        logger.info(f"Creating {app_slug} using {data}")
        
        # Handle mounting of volumes
        if "volume" in data:
            try:
                volumes = VolumeInstance.objects.filter(project__pk=project.pk, name=data["volume"])
                data["volume"] = volumes
                logger.info(f"using {data}")
            except VolumeInstance.DoesNotExist:
                raise ProjectCreationException(f"Volume {data['volume']} not found")
            
        if "flavor" in data:
            try:
                flavor = Flavor.objects.filter(project__pk=project.pk, name=data["flavor"]).first()
                data["flavor"] = flavor
                logger.info(f"using {data}")
            except Flavor.DoesNotExist:
                raise ProjectCreationException(f"Flavor {data['flavor']} not found")
            
        model_form_tuple = SLUG_MODEL_FORM_MAP.get(app_slug, None)
        if not model_form_tuple:
            logger.error(f"App {app_slug} not found")
            raise ProjectCreationException(f"App {app_slug} not found")
        
        form = model_form_tuple.Form(data, project_pk=project.pk)
        logger.info(form.errors.as_data())
        if form.is_valid():
            logger.info("Form is valid - Appending form to list")
            form_dict[app_slug] = form   
        else:
            logger.error(f"Form is invalid: {form.errors.as_data()}")
            raise ProjectCreationException(f"Form is invalid: {form.errors.as_data()}")

    logger.info("All forms valid, creating apps...")
    for app_slug, form in form_dict.items():
        create_instance_from_form(form, project, app_slug)
    
    env_dict = template.get("environments", {})
    logger.info("Creating Project Environments...")
    for name, settings in env_dict.items():
        try:
            app = Apps.objects.filter(slug=settings["app"]).order_by("-revision")[0]
        except Exception as err:
            logger.error(
                ("App for environment not found. item.app=%s project_slug=%s " "user=%s err=%s"),
                settings["app"],
                project_slug,
                user,
                err,
                exc_info=True,
            )
            raise
        try:
            environment = Environment(
                name=name,
                project=project,
                repository=settings["repository"],
                image=settings["image"],
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
                name,
                project,
                settings["repository"],
                settings["image"],
                app,
                user,
                err,
                exc_info=True,
            )
          
    project.status = "active"
    project.save()


@shared_task
def delete_project(project_pk):
    logger.info("SCHEDULING DELETION OF ALL INSTALLED APPS")
    project = Project.objects.get(pk=project_pk)
    delete_project_apps(project)

    project.delete()


@shared_task
def delete_project_apps(project):
    
    for subclass in AbstractAppInstance.__subclasses__():
        queryset = subclass.objects.filter(project=project)
        for instance in queryset:
            serialized_instance = instance.serialize()
            delete_resource(serialized_instance)
