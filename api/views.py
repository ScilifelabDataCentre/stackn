import json
import time
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.helpers import HandleUpdateStatusResponseCode, handle_update_status_request
from apps.models import AppCategories, AppInstance, Apps, AppStatus
from apps.tasks import delete_resource
from models.models import ObjectType
from portal.models import PublishedModel
from projects.models import (
    S3,
    Environment,
    Flavor,
    MLFlow,
    ProjectLog,
    ProjectTemplate,
    ReleaseName,
)
from projects.tasks import create_resources_from_template, delete_project_apps
from studio.utils import get_logger

from .APIpermissions import AdminPermission, ProjectPermission
from .serializers import (
    AppInstanceSerializer,
    AppSerializer,
    EnvironmentSerializer,
    FlavorsSerializer,
    Metadata,
    MetadataSerializer,
    MLflowSerializer,
    MLModelSerializer,
    Model,
    ModelLog,
    ModelLogSerializer,
    ObjectTypeSerializer,
    Project,
    ProjectSerializer,
    ProjectTemplateSerializer,
    ReleaseNameSerializer,
    S3serializer,
    UserSerializer,
)

logger = get_logger(__name__)


# A customized version of the obtain_auth_token view
# It will either create or fetch the user token
# https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class ObjectTypeList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ObjectTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug"]

    def get_queryset(self):
        return ObjectType.objects.all()


class ModelList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "version", "object_type"]

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        return Model.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        model = self.get_object()
        if model.project == project:
            model.delete()
            return HttpResponse("ok", 200)
        else:
            return HttpResponse("User is not allowed to delete object.", 403)

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        logger.info(str(project))

        try:
            model_name = request.data["name"]
            prev_model = Model.objects.filter(name=model_name, project=project).order_by("-version")
            logger.info("Previous Model Objects: %s", prev_model)
            if len(prev_model) > 0:
                logger.info("ACCESS")
                access = prev_model[0].access
                logger.info(access)

            else:
                access = "PR"
            release_type = request.data["release_type"]
            version = request.data["version"]
            description = request.data["description"]
            model_card = request.data["model_card"]
            model_uid = request.data["uid"]
            object_type_slug = request.data["object_type"]
            object_type = ObjectType.objects.get(slug=object_type_slug)
        except Exception as err:
            logger.exception(err, exc_info=True)
            return HttpResponse("Failed to create object: incorrect input data.", 400)

        try:
            new_model = Model(
                uid=model_uid,
                name=model_name,
                description=description,
                release_type=release_type,
                version=version,
                model_card=model_card,
                project=project,
                s3=project.s3storage,
                access=access,
            )
            new_model.save()
            new_model.object_type.set([object_type])

            pmodel = PublishedModel.objects.get(name=new_model.name, project=new_model.project)
            if pmodel:
                # Model is published, so we should create a new
                # PublishModelObject.

                from models.helpers import add_pmo_to_publish

                add_pmo_to_publish(new_model, pmodel)

        except Exception as err:
            logger.exception(err, exc_info=True)
            return HttpResponse("Failed to create object: failed to save object.", 400)
        return HttpResponse("ok", 200)


class ModelLogList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ModelLogSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['id','name', 'version']

    # Not sure if this kind of function is needed for ModelLog?
    def get_queryset(self):
        return ModelLog.objects.filter(project__pk=self.kwargs["project_pk"])

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])

        try:
            run_id = request.data["run_id"]
            trained_model = request.data["trained_model"]
            training_started_at = request.data["training_started_at"]
            execution_time = request.data["execution_time"]
            code_version = request.data["code_version"]
            current_git_repo = request.data["current_git_repo"]
            latest_git_commit = request.data["latest_git_commit"]
            system_details = request.data["system_details"]
            cpu_details = request.data["cpu_details"]
            training_status = request.data["training_status"]
        except Exception as e:
            logger.exception(e, exc_info=True)
            return HttpResponse("Failed to create training session log.", 400)

        new_log = ModelLog(
            run_id=run_id,
            trained_model=trained_model,
            project=project.name,
            training_started_at=training_started_at,
            execution_time=execution_time,
            code_version=code_version,
            current_git_repo=current_git_repo,
            latest_git_commit=latest_git_commit,
            system_details=system_details,
            cpu_details=cpu_details,
            training_status=training_status,
        )
        new_log.save()
        return HttpResponse("ok", 200)


class MetadataList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MetadataSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['id','name', 'version']

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])

        try:
            run_id = request.data["run_id"]
            trained_model = request.data["trained_model"]
            model_details = request.data["model_details"]
            parameters = request.data["parameters"]
            metrics = request.data["metrics"]
        except Exception as e:
            logger.exception(e, exc_info=True)
            return HttpResponse("Failed to create metadata log.", 400)

        new_md = Metadata(
            run_id=run_id,
            trained_model=trained_model,
            project=project.name,
            model_details=model_details,
            parameters=parameters,
            metrics=metrics,
        )
        new_md.save()
        return HttpResponse("ok", 200)


class MembersList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        """
        This view should return a list of all the members
        of the project
        """
        proj = Project.objects.filter(pk=self.kwargs["project_pk"])
        owner = proj[0].owner
        auth_users = proj[0].authorized.all()
        logger.info(owner)
        logger.info(auth_users)
        ids = set()
        ids.add(owner.pk)
        for user in auth_users:
            ids.add(user.pk)
        logger.info(ids)
        users = User.objects.filter(pk__in=ids)
        logger.info(users)
        return users

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        selected_users = request.data["selected_users"]
        for username in selected_users.split(","):
            user = User.objects.get(username=username)
            project.authorized.add(user)
        project.save()
        return HttpResponse("Successfully added members.", status=200)

    def destroy(self, request, *args, **kwargs):
        logger.info("removing user")
        project = Project.objects.get(id=self.kwargs["project_pk"])
        user_id = self.kwargs["pk"]
        logger.info(user_id)
        user = User.objects.get(pk=user_id)
        logger.info("user: %s", str(user))
        if user.username != project.owner.username:
            logger.info("username " + user.username)
            project.authorized.remove(user)
            for role in settings.PROJECT_ROLES:
                return HttpResponse("Successfully removed members.", status=200)
        else:
            return HttpResponse("Cannot remove owner of project.", status=400)
        return HttpResponse("Failed to remove user.", status=400)


class ProjectList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name", "slug"]

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Project.objects.filter(
            Q(owner__username=current_user) | Q(authorized__pk__exact=current_user.pk),
            ~Q(status="archived"),
        ).distinct("name")

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if (request.user == project.owner or request.user.is_superuser) and project.status.lower() != "deleted":
            logger.info("Delete project")
            logger.info("SCHEDULING DELETION OF ALL INSTALLED APPS")
            delete_project_apps(project.slug)

            logger.info("ARCHIVING PROJECT Object")
            objects = Model.objects.filter(project=project)
            for obj in objects:
                obj.status = "AR"
                obj.save()
            project.status = "archived"
            project.save()
        else:
            logger.info("User is not allowed to delete project (must be owner).")
            return HttpResponse(
                "User is not allowed to delete project (must be owner).",
                status=403,
            )

        return HttpResponse("ok", status=200)

    def create(self, request):
        name = request.data["name"]
        description = request.data["description"]
        project = Project.objects.create_project(
            name=name,
            owner=request.user,
            description=description,
        )
        success = True

        try:
            # Create resources from the chosen template
            template_slug = request.data["template"]
            template = ProjectTemplate.objects.get(slug=template_slug)
            project_template = ProjectTemplate.objects.get(pk=template.pk)
            create_resources_from_template.delay(request.user.username, project.slug, project_template.template)

            # Reset user token
            if "oidc_id_token_expiration" in request.session:
                request.session["oidc_id_token_expiration"] = time.time() - 100
                request.session.save()
            else:
                logger.info("No token to reset.")
        except Exception:
            logger.error("could not create project resources", exc_info=True)
            success = False

        if not success:
            project.delete()
            return HttpResponse("Failed to create project.", status=200)
        else:
            l1 = ProjectLog(
                project=project,
                module="PR",
                headline="Project created",
                description="Created project {}".format(project.name),
            )
            l1.save()

            l2 = ProjectLog(
                project=project,
                module="PR",
                headline="Getting started",
                description="Getting started with project {}".format(project.name),
            )
            l2.save()

        if success:
            project.save()
            return HttpResponse(project.slug, status=200)


class ResourceList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "app__category"]

    def create(self, request, *args, **kwargs):
        template = request.data
        # template = {
        #     "apps": request.data
        # }
        logger.info(template)
        project = Project.objects.get(id=self.kwargs["project_pk"])
        create_resources_from_template.delay(request.user.username, project.slug, json.dumps(template))
        return HttpResponse("Submitted request to create app.", status=200)


class AppInstanceList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "app__category"]

    def get_queryset(self):
        return AppInstance.objects.filter(~Q(state="Deleted"), project__pk=self.kwargs["project_pk"])

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        app_slug = request.data["slug"]
        data = request.data
        user = request.user
        import apps.helpers as helpers

        app = Apps.objects.filter(slug=app_slug).order_by("-revision")[0]

        (
            successful,
            _,
            _,
        ) = helpers.create_app_instance(
            user=user,
            project=project,
            app=app,
            app_settings=app.settings,
            data=data,
            wait=True,
        )

        if not successful:
            logger.info("create_app_instance failed")
            return HttpResponse("App creation faild", status=400)

        return HttpResponse("App created.", status=200)

    def destroy(self, request, *args, **kwargs):
        appinstance = self.get_object()
        # Check that user is allowed to delete app:
        # Either user owns the app, or is a member of the project
        # (Checked by project permission above)
        # and the app is set to project level permission.
        access = False

        if appinstance.access == "public":
            access = True

        if access:
            delete_resource.delay(appinstance.pk)
        else:
            return HttpResponse("User is not allowed to delete resource.", status=403)
        return HttpResponse("Deleted app.", status=200)


class FlavorsList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = FlavorsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return Flavor.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class EnvironmentList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = EnvironmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return Environment.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class S3List(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = S3serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "host", "region"]

    def get_queryset(self):
        return S3.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class MLflowList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MLflowSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return MLFlow.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class ReleaseNameList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ReleaseNameSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "project"]

    def get_queryset(self):
        return ReleaseName.objects.filter(project__pk=self.kwargs["project_pk"])

    def create(self, request, *args, **kwargs):
        name = slugify(request.data["name"])
        project = Project.objects.get(id=self.kwargs["project_pk"])
        if ReleaseName.objects.filter(name=name).exists():
            if project.status != "archived":
                logger.info("ReleaseName already in use.")
                return HttpResponse("Release name already in use.", status=200)
        status = "active"

        rn = ReleaseName(name=name, status=status, project=project)
        rn.save()
        return HttpResponse("Created release name {}.".format(name), status=200)

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class AppList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        AdminPermission,
    )
    serializer_class = AppSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug", "category"]

    def get_queryset(self):
        return Apps.objects.all()

    def create(self, request, *args, **kwargs):
        logger.info("IN CREATE")
        try:
            name = request.data["name"]
            slug = request.data["slug"]
            category = AppCategories.objects.get(slug=request.data["cat"])
            description = request.data["description"]
            settings = json.loads(request.data["settings"])
            table_field = json.loads(request.data["table_field"])
            priority = request.data["priority"]
            access = "public"
            proj_list = []
            if "access" in request.data:
                try:
                    access = request.data["access"]
                    if access != "public":
                        projs = access.split(",")
                        for proj in projs:
                            tmp = Project.objects.get(slug=proj)
                            proj_list.append(tmp)
                except Exception:
                    logger.error("Invalid access field", exc_info=True)
                    return HttpResponse("Invalid access field.", status=400)

            logger.info(request.data)
            logger.info("SETTINGS")
            logger.info(settings)
            logger.info(table_field)
        except Exception:
            logger.error(request.data, exc_info=True)
            return HttpResponse("Invalid app specification.", status=400)
        logger.info("ADD APP")
        logger.info(name)
        logger.info(slug)
        try:
            app_latest_rev = Apps.objects.filter(slug=slug).order_by("-revision")
            if app_latest_rev:
                revision = app_latest_rev[0].revision + 1
            else:
                revision = 1
            app = Apps(
                name=name,
                slug=slug,
                category=category,
                settings=settings,
                chart_archive=request.FILES["chart"],
                revision=revision,
                description=description,
                table_field=table_field,
                priority=int(priority),
                access=access,
            )
            app.save()
            app.projects.add(*proj_list)
        except Exception as err:
            logger.error(err, exc_info=True)
        return HttpResponse("Created new app.", status=200)

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class ProjectTemplateList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        AdminPermission,
    )
    serializer_class = ProjectTemplateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug"]

    def get_queryset(self):
        return ProjectTemplate.objects.all()

    def create(self, request, *args, **kwargs):
        logger.info(request.data)
        name = "KEY_NAME_MISSING"
        try:
            settings = json.loads(request.data["settings"])
            name = settings["name"]
            slug = settings["slug"]
            description = settings["description"]
            template = settings["template"]
            image = request.FILES["image"]
        except Exception:
            logger.error(request.data, exc_info=True)
            return HttpResponse("Failed to create new template: {}".format(name), status=400)

        try:
            template_latest_rev = ProjectTemplate.objects.filter(slug=slug).order_by("-revision")
            if template_latest_rev:
                revision = template_latest_rev[0].revision + 1
            else:
                revision = 1
            template = ProjectTemplate(
                name=name,
                slug=slug,
                revision=revision,
                description=description,
                template=json.dumps(template),
                image=image,
            )
            template.save()
        except Exception as err:
            logger.error(err, exc_info=True)
        return HttpResponse("Created new template: {}.".format(name), status=200)


@api_view(["GET", "POST"])
@permission_classes(
    (
        IsAuthenticated,
        AdminPermission,
    )
)
def update_app_status(request):
    """
    Manages the app instance status.
    Implemented as a DRF function based view.
    Supports GET and POST verbs.

    The service contract for the POST actions is as follows:
    :param release str: The release id of the app instance, stored in the AppInstance.parameters dict.
    :param new-status str: The new status code.
    :param event-ts timestamp: A JSON-formatted timestamp, e.g. 2024-01-25T16:02:50.00Z.
    :param event-msg json dict: An optional json dict containing pod-msg and/or container-msg.
    :returns: An http status code and status text.
    """

    # POST verb
    if request.method == "POST":
        logger.info("API method update_app_status called with POST verb.")

        utc = pytz.UTC

        try:
            # Parse and validate the input

            # Required input
            release = request.data["release"]

            new_status = request.data["new-status"]

            if len(new_status) > 15:
                logger.debug("Status code is longer than 15 chars so shortening: %s", new_status)
                new_status = new_status[:15]

            event_ts = datetime.strptime(request.data["event-ts"], "%Y-%m-%dT%H:%M:%S.%fZ")
            event_ts = utc.localize(event_ts)

            # Optional
            event_msg = request.data.get("event-msg", None)

        except KeyError as err:
            logger.error("API method called with invalid input. Missing required input parameter: %s", err)
            return Response(f"Invalid input. Missing required input parameter: {err}", 400)

        except Exception as err:
            logger.error("API method called with invalid input:  %s, %s", err, type(err))
            return Response(f"Invalid input. {err}", 400)

        logger.debug(
            "API method update_app_status input: release=%s, new_status=%s, event_ts=%s, event_msg=%s",
            release,
            new_status,
            event_ts,
            event_msg,
        )

        try:
            result = handle_update_status_request(release, new_status, event_ts, event_msg)

            if result == HandleUpdateStatusResponseCode.NO_ACTION:
                return Response(
                    "OK. NO_ACTION. No action performed. Possibly the event time is older \
                    than the currently stored time.",
                    200,
                )

            elif result == HandleUpdateStatusResponseCode.CREATED_FIRST_STATUS:
                return Response("OK. CREATED_FIRST_STATUS. Created a missing AppStatus.", 200)

            elif result == HandleUpdateStatusResponseCode.UPDATED_STATUS:
                return Response(
                    "OK. UPDATED_STATUS. Updated the app status. \
                    Determined that the submitted event was newer and different status.",
                    200,
                )

            elif result == HandleUpdateStatusResponseCode.UPDATED_TIME_OF_STATUS:
                return Response(
                    "OK. UPDATED_TIME_OF_STATUS. Updated only the event time of the status. \
                    Determined that the new and old status codes are the same.",
                    200,
                )

            else:
                logger.error("Unknown return code from handle_update_status_request() = %s", result, exc_info=True)
                return Response(f"Unknown return code from handle_update_status_request() = {result}", 500)

        except ObjectDoesNotExist:
            logger.error("The specified app instance was not found release=%s.", release)
            return Response(f"The specified app instance was not found {release=}.", 404)

        except Exception as err:
            logger.error(
                "Unable to update the status of the specified app instance %s. %s, %s", release, err, type(err)
            )
            return Response(f"Unable to update the status of the specified app instance {release=}.", 500)

    # GET verb
    logger.info("API method update_app_status called with GET verb.")
    return Response({"message": "DEBUG: GET"})
