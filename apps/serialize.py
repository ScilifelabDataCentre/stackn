import json

import flatten_json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.template import engines
from django.utils.text import slugify
from rest_framework.authtoken.models import Token

from models.models import Model
from projects.models import S3, Environment, Flavor
from studio.utils import get_logger

from .models import AppInstance, Apps

logger = get_logger(__name__)

User = get_user_model()

key_words = [
    "appobj",
    "model",
    "flavor",
    "S3",
    "environment",
    "volumes",
    "apps",
    "logs",
    "permissions",
    "default_values",
    "export-cli",
    "csrfmiddlewaretoken",
    "env_variables",
    "publishable",
]


def serialize_model(form_selection):
    logger.info("SERIALIZING MODEL")
    model_json = dict()
    obj = []
    if "model" in form_selection:
        model_id = form_selection.get("model", None)
        if isinstance(model_id, str):
            model_id = int(model_id)
        obj = Model.objects.filter(pk=model_id)
        logger.info("Fetching selected model:")

        object_type = obj[0].object_type.all()
        if len(object_type) == 1:
            logger.info("OK")
        else:
            logger.info("Currently only supports one object type per model")
            logger.info("Will assume first in list.")
        model_json = {
            "model": {
                "name": obj[0].name,
                "version": obj[0].version,
                "release_type": obj[0].release_type,
                "description": obj[0].description,
                "url": "http://{}".format(obj[0].s3.host),
                "service": obj[0].s3.app.parameters["service"]["name"],
                "port": obj[0].s3.app.parameters["service"]["port"],
                "targetport": obj[0].s3.app.parameters["service"]["targetport"],
                "access_key": obj[0].s3.access_key,
                "secret_key": obj[0].s3.secret_key,
                "bucket": obj[0].bucket,
                "obj": obj[0].uid,
                "path": obj[0].path,
                "type": object_type[0].slug,
            }
        }

    return model_json, obj


def serialize_S3(form_selection, project):
    logger.info("SERIALIZING S3")
    s3_json = dict()
    if "S3" in form_selection:
        s3_id = form_selection.get("S3", None)
        try:
            obj = S3.objects.filter(pk=s3_id)
        except:  # noqa E722 TODO: Add exception
            obj = S3.objects.filter(name=s3_id, project=project)
        s3_json = {
            "s3": {
                "pk": obj[0].pk,
                "name": obj[0].name,
                "host": obj[0].host,
                "service": obj[0].app.parameters["service"]["name"],
                "port": obj[0].app.parameters["service"]["port"],
                "targetport": obj[0].app.parameters["service"]["targetport"],
                "access_key": obj[0].access_key,
                "secret_key": obj[0].secret_key,
                "region": obj[0].region,
            }
        }
    return s3_json


def serialize_flavor(form_selection, project):
    logger.info("SERIALIZING FLAVOR")
    flavor_json = dict()
    if "flavor" in form_selection:
        flavor_id = form_selection.get("flavor", None)
        flavor = Flavor.objects.get(pk=flavor_id, project=project)
        flavor_json["flavor"] = {
            "requests": {
                "cpu": flavor.cpu_req,
                "memory": flavor.mem_req,
                "ephemeral-storage": flavor.ephmem_req,
            },
            "limits": {
                "cpu": flavor.cpu_lim,
                "memory": flavor.mem_lim,
                "ephemeral-storage": flavor.ephmem_lim,
            },
        }
        if flavor.gpu_req and int(flavor.gpu_req) > 0:
            flavor_json["flavor"]["requests"]["nvidia.com/gpu"] = (flavor.gpu_req,)
            flavor_json["flavor"]["limits"]["nvidia.com/gpu"] = flavor.gpu_lim

    return flavor_json


def serialize_environment(form_selection, project):
    logger.info("SERIALIZING ENVIRONMENT")
    environment_json = dict()
    if "environment" in form_selection:
        environment_id = form_selection.get("environment", None)
        try:
            environment = Environment.objects.get(pk=environment_id)
        except:  # noqa E722 TODO: Add exception
            environment = Environment.objects.get(name=environment_id, project=project)
        environment_json["environment"] = {
            "pk": environment.pk,
            "repository": environment.repository,
            "image": environment.image,
            "registry": False,
        }
        if environment.registry:
            environment_json["environment"]["registry"] = environment.registry.parameters
            environment_json["environment"]["registry"]["enabled"] = True
        else:
            environment_json["environment"]["registry"] = {"enabled": False}
    return environment_json


def serialize_apps(form_selection, project):
    logger.info("SERIALIZING DEPENDENT APPS")
    parameters = dict()
    parameters["apps"] = dict()
    app_deps = []
    for key in form_selection.keys():
        if "app:" in key and key[0:4] == "app:":
            app_name = key[4:]
            try:
                app = Apps.objects.filter(name=app_name).order_by("-revision").first()
                if not app:
                    app = Apps.objects.filter(slug=app_name).order_by("-revision").first()
            except Exception:
                logger.error("Failed to fetch app: %s", app_name)
                raise
            if not app:
                logger.info("App not found: %s", app_name)

            parameters["apps"][app.slug] = dict()
            logger.info(app_name)
            logger.info("id: " + str(form_selection[key]))
            try:
                objs = AppInstance.objects.filter(pk__in=form_selection.getlist(key))
            except:  # noqa E722 TODO: Add exception
                objs = AppInstance.objects.filter(name__in=form_selection[key], project=project)

            for obj in objs:
                app_deps.append(obj)
                parameters["apps"][app.slug][slugify(obj.name)] = obj.parameters

    return parameters, app_deps


def serialize_primitives(form_selection):
    logger.info("SERIALIZING PRIMITIVES")
    parameters = dict()
    keys = form_selection.keys()
    for key in keys:
        if key not in key_words and "app:" not in key:
            parameters[key] = form_selection[key].replace("\r\n", "\n")
            if parameters[key] == "False":
                parameters[key] = False
            elif parameters[key] == "True":
                parameters[key] = True
    logger.info(parameters)
    return flatten_json.unflatten(parameters, ".")


def serialize_permissions(form_selection):
    logger.info("SERIALIZING PERMISSIONS")
    parameters = dict()
    parameters["permissions"] = {
        "public": False,
        "project": False,
        "private": False,
    }

    permission = form_selection.get("permission", None)
    parameters["permissions"][permission] = True
    logger.info(parameters)
    return parameters


def serialize_appobjs(form_selection):
    logger.info("SERIALIZING APPOBJS")
    parameters = dict()
    appobjs = []
    if "appobj" in form_selection:
        appobjs = form_selection.getlist("appobj")
        parameters["appobj"] = dict()
        for obj in appobjs:
            app = Apps.objects.get(pk=obj)
            parameters["appobj"][app.slug] = True
    logger.info(parameters)
    return parameters


def serialize_default_values(aset):
    parameters = []
    if "default_values" in aset:
        parameters = dict()
        logger.info(aset["default_values"])
        parameters["default_values"] = aset["default_values"]
        for key in parameters["default_values"].keys():
            if parameters["default_values"][key] == "False":
                parameters["default_values"][key] = False
            elif parameters["default_values"][key] == "True":
                parameters["default_values"][key] = True

    return parameters


def serialize_project(project):
    parameters = dict()
    if project.mlflow:
        parameters["mlflow"] = {
            "url": project.mlflow.mlflow_url,
            "host": project.mlflow.host,
            "service": project.mlflow.app.parameters["service"]["name"],
            "port": project.mlflow.app.parameters["service"]["port"],
            "targetport": project.mlflow.app.parameters["service"]["targetport"],
            "s3url": "https://" + project.mlflow.s3.host,
            "s3service": project.mlflow.s3.app.parameters["service"]["name"],
            "s3port": project.mlflow.s3.app.parameters["service"]["port"],
            "s3targetport": project.mlflow.s3.app.parameters["service"]["targetport"],
            "access_key": project.mlflow.s3.access_key,
            "secret_key": project.mlflow.s3.secret_key,
            "region": project.mlflow.s3.region,
            "username": project.mlflow.basic_auth.username,
            "password": project.mlflow.basic_auth.password,
        }
    return parameters


def serialize_cli(username, project, aset):
    user = User.objects.get(username=username)
    token, created = Token.objects.get_or_create(user=user)
    parameters = dict()
    if "export-cli" in aset and aset["export-cli"] == "True":
        parameters["cli_setup"] = {
            "url": settings.STUDIO_URL,
            "project": project.name,
            "user": username,
            "token": token.key,
            "secure": "False",
        }
    return parameters


def serialize_env_variables(username, project, aset):
    logger.info("SERIALIZING ENV VARIABLES")
    parameters = dict()
    parameters["app_env"] = dict()
    logger.info("fetching apps")
    try:
        apps = AppInstance.objects.filter(
            ~Q(state="Deleted"),
            Q(owner__username=username) | Q(access__in=["project", "public"]),
            project=project,
        )
    except Exception as err:
        logger.error(err, exc_info=True)
    logger.info("Creating template engine")
    django_engine = engines["django"]
    # TODO: refactor potential bug. If there is an exception thrown by query statement above, then `apps` is not defined
    logger.info(apps)
    for app in apps:
        params = app.parameters
        appsettings = app.app.settings
        if "env_variables" in appsettings:
            tmp = json.dumps(appsettings["env_variables"])
            env_vars = json.loads(django_engine.from_string(tmp).render(params))
            for key in env_vars.keys():
                parameters["app_env"][slugify(key)] = env_vars[key]
    logger.info(parameters)

    return parameters


def serialize_app(form_selection, project, aset, username):
    logger.info("SERIALIZING APP")
    parameters = dict()

    model_params, model_deps = serialize_model(form_selection)
    parameters.update(model_params)

    app_params, app_deps = serialize_apps(form_selection, project)
    parameters.update(app_params)

    prim_params = serialize_primitives(form_selection)
    parameters.update(prim_params)

    flavor_params = serialize_flavor(form_selection, project)
    parameters.update(flavor_params)

    environment_params = serialize_environment(form_selection, project)
    parameters.update(environment_params)

    s3params = serialize_S3(form_selection, project)
    parameters.update(s3params)

    permission_params = serialize_permissions(form_selection)
    parameters.update(permission_params)

    appobj_params = serialize_appobjs(form_selection)
    parameters.update(appobj_params)

    default_values = serialize_default_values(aset)
    parameters.update(default_values)

    project_values = serialize_project(project)
    parameters.update(project_values)

    cli_values = serialize_cli(username, project, aset)
    parameters.update(cli_values)

    env_variables = serialize_env_variables(username, project, aset)
    parameters.update(env_variables)

    return parameters, app_deps, model_deps
