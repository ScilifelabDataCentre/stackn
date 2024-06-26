import ast
import logging
import os
import subprocess
import uuid
from collections import defaultdict

import markdown
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from guardian.decorators import permission_required_or_403
from guardian.mixins import PermissionRequiredMixin

from .forms import EnvironmentForm, ModelForm, UploadModelCardHeadlineForm
from .helpers import add_pmo_to_publish, set_artifact
from .models import Metadata, Model, ModelLog, ObjectType

new_data = defaultdict(list)  # type: ignore
logger = logging.getLogger(__name__)

Apps = apps.get_model(app_label=settings.APPS_MODEL)
BaseAppInstance = apps.get_model(app_label="apps.BaseAppInstance")

Project = apps.get_model(app_label=settings.PROJECTS_MODEL)
ProjectLog = apps.get_model(app_label=settings.PROJECTLOG_MODEL)
Environment = apps.get_model(app_label=settings.ENVIRONMENT_MODEL)

PublishedModel = apps.get_model(app_label=settings.PUBLISHEDMODEL_MODEL)


class ModelCreate(LoginRequiredMixin, PermissionRequiredMixin, View):
    template = "models/model_create.html"
    model_uid = str(uuid.uuid1().hex)
    permission_required = "can_view_project"
    return_403 = True

    def get_object(self):
        self.obj = get_object_or_404(Project, slug=self.kwargs["project"])
        return self.obj

    def get(self, request, user, project):
        # all below will become locals() context fields

        form = ModelForm()
        # For showing the persistent volumes currently
        # available within the project
        volumeK8s_set = Apps.objects.get(slug="volumeK8s")
        volumes = BaseAppInstance.objects.filter(Q(app=volumeK8s_set), Q(app_status__status="Running"))

        # Passing the current project to the view/template
        project = (
            Project.objects.filter(
                Q(owner=request.user) | Q(authorized=request.user),
                status="active",
                slug=project,
            )
            .distinct()
            .first()
        )

        # Showing all the available model object types
        # (e.g. Tensorflow, PyTorch, etc...)
        object_types = ObjectType.objects.all()

        # For showing the app instances where a folder
        # with trained models can be fetched
        # for the time being is hard-coded to
        # jupyter-lab where usually models are trained
        app_set = Apps.objects.get(slug="jupyter-lab")
        apps = BaseAppInstance.objects.filter(Q(app=app_set), Q(app_status__status="Running"))

        return render(request, self.template, locals())

    def post(self, request, user, project):
        # For redirection after successful POST
        # (and avoiding refresh of same POST)
        # We use reverse_lazy() because we are
        # in "constructor attribute" code
        # that is run before urls.py is completely loaded
        # redirect_url = reverse_lazy("models:list", args=[user, project])
        redirect_url = reverse_lazy("projects:details", args=[user, project])

        # Fetching current project and setting default object type
        model_project = (
            Project.objects.filter(
                Q(owner=request.user) | Q(authorized=request.user),
                status="active",
                slug=project,
            )
            .distinct()
            .first()
        )

        # Extracting form fields
        form = ModelForm(request.POST)

        # if valid it saves model in S3 storage,
        # create object in the db and redirect
        if form.is_valid():
            model_name = form.cleaned_data["name"]
            model_description = form.cleaned_data["description"]
            model_release_type = form.cleaned_data["release_type"]
            model_version = form.cleaned_data["version"]
            model_folder_name = form.cleaned_data["path"]
            model_type = request.POST.get("model-type")

            model_file = ""
            model_card = ""
            model_S3 = model_project.s3storage
            is_file = True
            # TO DO: find a clever way to understand whether
            # we are using a self-signed cert or not
            secure_mode = False
            building_from_current = False

            # Copying folder from PVC that contains trained model
            # The minio sidecar does this.
            # First find the minio release name
            minio_set = Apps.objects.get(slug="minio")
            minio = BaseAppInstance.objects.filter(
                Q(app=minio_set), Q(project=model_project), Q(app_status__status="Running")
            ).first()

            minio_release = minio.parameters["release"]  # e.g 'rfc058c6f'
            # Now find the related pod
            cmd = f'kubectl get po -n {settings.NAMESPACE} -l release="{minio_release}" -o jsonpath="{{.items[0].metadata.name}}"'
            try:
                result = subprocess.check_output(cmd, shell=True)
                # because the above subprocess run returns a byte-like object
                app_pod = result.decode("utf-8")
            except subprocess.CalledProcessError:
                messages.error(
                    request,
                    "Something went wrong: the model object was not created!",
                )
                return redirect(redirect_url)

            # Copy model folder from pod to a temp location within studio pod
            temp_folder_path = os.path.join(str(settings.BASE_DIR), "media", "tmp")  # which should be /app/media/tmp
            # Create and move into the new directory
            try:
                os.mkdir(temp_folder_path)
                os.chdir(temp_folder_path)
                os.getcwd()
            except OSError as error:
                logger.error(str(error), exc_info=True)
            # Note: default namespace is assumed here
            cmd = (
                f"kubectl cp -n {settings.NAMESPACE} "
                + app_pod
                + ":/data/"
                + model_folder_name
                + " "
                + "./"
                + model_folder_name
                + " -c "
                + minio_release
                + "-minio-sidecar"
            )
            try:
                result = subprocess.check_output(cmd, shell=True)
                logger.info(
                    "SUBPROCESS - FOLDER COPY WITH KUBECTL: %s",
                    result.decode("utf-8"),
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                messages.error(
                    request,
                    "Something went wrong: Models folder could not be copied",
                )
                return redirect(redirect_url)

            # Creating new file to be compressed as a tar
            if model_file == "":
                building_from_current = True

                model_file = "{}.tar.gz".format(self.model_uid)
                f = open(model_file, "w")
                f.close()

                try:
                    result = subprocess.run(
                        [
                            "tar",
                            "--exclude={}".format(model_file),
                            "-czvf",
                            model_file,
                            model_folder_name,
                        ],
                        stdout=subprocess.PIPE,
                        check=True,
                    )
                    logger.info("SUBPROCESS - ARCHIVE CREATION: %s", result)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    messages.error(
                        request,
                        ("Something went wrong: " "The archive for the model folder was not created!"),
                    )
                    # Clean up
                    os.system("rm {}.tar.gz".format(self.model_uid))
                    os.system("rm -rf {}".format(temp_folder_path))
                    return redirect(redirect_url)

            if model_card == "" or model_card is None:
                model_card_html_string = ""
            else:
                with open(model_card, "r") as f:
                    model_card_html_string = f.read()

            # Method from helpers.py, where S3 related methods exists
            artifact_name = model_name + "_" + self.model_uid + ".tar"
            status = set_artifact(
                artifact_name,
                model_file,
                model_folder_name,
                model_S3,
                is_file=is_file,
                secure_mode=secure_mode,
            )

            if not status:
                messages.error(
                    request,
                    ("Something went wrong: " "failed to upload model to S3 storage!"),
                )
                return redirect(redirect_url)

            new_model = Model(
                uid=artifact_name,
                name=model_name,
                bucket=model_folder_name,
                description=model_description,
                release_type=model_release_type,
                version=model_version,
                model_card="",
                path=model_folder_name,
                project=model_project,
                s3=model_S3,
                access="PR",
            )
            new_model.save()

            # Setting the model object type based on form input from user
            object_type = ObjectType.objects.get(name=model_type)
            new_model.object_type.set([object_type])

            # Cleaning up generated tar for uploading artifact to S3 storage
            try:
                if building_from_current:
                    os.system("rm {}.tar.gz".format(self.model_uid))
                    os.system("rm -rf {}".format(temp_folder_path))
                    os.chdir(settings.BASE_DIR)
            except OSError as error:
                logger.error(error, exc_info=True)

            # Finally, we redirect
            return redirect(redirect_url)
        else:
            # Otherwise when form is not valid,
            # it will then show error and the entered inputs
            return render(request, self.template, locals())


# Published models visible under the "Catalogs" menu
def index(request, user=None, project=None, id=0):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active")
    except Exception:
        logger.error("User not logged in.")

    if project:
        project = Project.objects.filter(slug=project).first()
        published_models = Model.objects.filter(project=project).distinct("name")

        return render(request, "models/index.html", locals())
    else:
        # TODO move tags to separate djapp

        # create session object to store info about model and their tag counts
        if "model_tags" not in request.session:
            request.session["model_tags"] = {}
        # tag_count from the get request helps set num_tags
        # which helps set the number of tags to show in the template
        if "tag_count" in request.GET:
            # add model id to model_tags object
            if "model_id_add" in request.GET:
                num_tags = int(request.GET["tag_count"])
                id = int(request.GET["model_id_add"])
                request.session["model_tags"][str(id)] = num_tags
            # remove model id from model_tags object
            if "model_id_remove" in request.GET:
                num_tags = int(request.GET["tag_count"])
                id = int(request.GET["model_id_remove"])
                if str(id) in request.session["model_tags"]:
                    request.session["model_tags"].pop(str(id))

        # reset model_tags if Model Tab on Sidebar pressed
        if id == 0:
            if "tf_add" not in request.GET and "tf_remove" not in request.GET:
                request.session["model_tags"] = {}

        media_url = settings.MEDIA_URL
        published_models = PublishedModel.objects.all()

        # create session object to store ids for
        # tag seacrh if it does not exist
        if "tag_filters" not in request.session:
            request.session["tag_filters"] = []
        if "tf_add" in request.GET:
            tag = request.GET["tf_add"]
            if tag not in request.session["tag_filters"]:
                request.session["tag_filters"].append(tag)
        elif "tf_remove" in request.GET:
            tag = request.GET["tf_remove"]
            if tag in request.session["tag_filters"]:
                request.session["tag_filters"].remove(tag)
        elif "tag_count" not in request.GET:
            tag = ""
            request.session["tag_filters"] = []
        logger.info("tag_filters: %s", request.session["tag_filters"])

        # changed list of published model only if tag filters are present
        if request.session["tag_filters"]:
            tagged_published_models = []
            for model in published_models:
                model_objs = model.model_obj.order_by("-model__version")
                # 20230922: This fixes uncaught exception:
                if len(model_objs) > 0:
                    latest_model_obj = model_objs[0]
                    mymodel = latest_model_obj.model
                    for t in mymodel.tags.all():
                        if t in request.session["tag_filters"]:
                            tagged_published_models.append(model)
                            break
            published_models = tagged_published_models

        request.session.modified = True

        return render(request, "models/index.html", locals())


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def list(request, user, project):
    template = "models/models_list.html"

    # Will be added to locals() which create a
    # dict context with local variables
    menu = dict()
    menu["objects"] = "active"
    projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active")
    project = (
        Project.objects.filter(
            Q(owner=request.user) | Q(authorized=request.user),
            status="active",
            slug=project,
        )
        .distinct()
        .first()
    )
    models = Model.objects.filter(project=project).order_by("name", "-version")

    return render(request, template, locals())


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def unpublish_model(request, user, project, id):
    # TODO: Check that user has access to this particular model.
    model = Model.objects.get(pk=id)

    try:
        # TODO: refactoring. Shouldn't this be transaction?
        pmodel = PublishedModel.objects.get(name=model.name, project=model.project)
        pmos = pmodel.model_obj.all()
        pmos.delete()
        pmodel.delete()
    except Exception as err:
        logger.error(err)
    model.access = "PR"
    model.save()
    return HttpResponseRedirect(reverse("models:list", kwargs={"user": user, "project": project}))


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def publish_model(request, user, project, id):
    logger.info("PUBLISHING MODEL")

    # TODO: Check that user has access to this particular model.
    model = Model.objects.get(pk=id)

    # Default behavior is that all versions of a model are published.
    models = Model.objects.filter(id=id, name=model.name, project=model.project)

    pmodel = PublishedModel(name=model.name, project=model.project)
    pmodel.save()

    # Copy files to public location
    for mdl in models:
        add_pmo_to_publish(mdl, pmodel)

    model.access = "PU"
    model.save()

    return HttpResponseRedirect(reverse("models:list", kwargs={"user": user, "project": project}))


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def change_access(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()

    if request.method == "POST":
        visibility = request.POST.get("access", "")
        if visibility != model.access:
            model.access = visibility
            model.save()
            project_obj = Project.objects.get(slug=project)
            log = ProjectLog(
                project=project_obj,
                module="MO",
                headline="Model - {name}".format(name=model.name),
                description=("Changed Access Level from {previous} to {current}").format(
                    previous=previous, current=model.get_access_display()
                ),
            )
            log.save()

    return HttpResponseRedirect(reverse("models:details_public", kwargs={"id": id}))


@login_required
def add_tag(request, published_id, id):
    model = Model.objects.filter(pk=id).first()
    _ = model.get_access_display()
    if request.method == "POST":
        new_tag = request.POST.get("tag", "")
        logger.info("New Tag: %s", new_tag)
        model.tags.add(new_tag)
        model.save()
    return HttpResponseRedirect(reverse("models:details_public", kwargs={"id": published_id}))


@login_required
def remove_tag(request, published_id, id):
    model = Model.objects.filter(pk=id).first()
    _ = model.get_access_display()
    if request.method == "POST":
        logger.info(request.POST)
        new_tag = request.POST.get("tag", "")
        logger.info("Remove Tag: %s", new_tag)
        model.tags.remove(new_tag)
        model.save()

    return HttpResponseRedirect(reverse("models:details_public", kwargs={"id": published_id}))


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def add_tag_private(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    _ = model.get_access_display()
    if request.method == "POST":
        new_tag = request.POST.get("tag", "")
        logger.info("New Tag: %s", new_tag)
        model.tags.add(new_tag)
        model.save()

    return HttpResponseRedirect(
        reverse(
            "models:details_private",
            kwargs={"user": user, "project": project, "id": id},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def remove_tag_private(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    _ = model.get_access_display()
    if request.method == "POST":
        logger.info(request.POST)
        new_tag = request.POST.get("tag", "")
        logger.info("Remove Tag: %s", new_tag)
        model.tags.remove(new_tag)
        model.save()

    return HttpResponseRedirect(
        reverse(
            "models:details_private",
            kwargs={"user": user, "project": project, "id": id},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def upload_model_headline(request, user, project, id):
    if request.method == "POST":
        form = UploadModelCardHeadlineForm(request.POST, request.FILES)
        if form.is_valid():
            model = Model.objects.get(pk=id)
            model.model_card_headline = request.FILES["file"]
            model.save()

            project_obj = Project.objects.get(slug=project)
            log = ProjectLog(
                project=project_obj,
                module="MO",
                headline="Model - {name}".format(name=model.name),
                description="Uploaded new headline image.",
            )
            log.save()

            return HttpResponseRedirect("/")
    else:
        form = UploadModelCardHeadlineForm()

    return render(request, "models_upload_headline.html", {"form": form})


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def add_docker_image(request, user, project, id):
    model = Model.objects.get(pk=id)

    if request.method == "POST":
        form = EnvironmentForm(request.POST)

        if form.is_valid():
            registry = form.cleaned_data["registry"]
            username = form.cleaned_data["username"]
            repository = form.cleaned_data["repository"]
            image = form.cleaned_data["image"]
            tag = form.cleaned_data["tag"]

            environment = Environment(
                name=registry + "/" + username,
                slug=None,
                project=model.project,
                repository=repository,
                image=image + ":" + tag,
                registry=None,
                appenv=None,
                app=None,
            )
            environment.save()

            model.docker_image = environment
            model.save()

            project_obj = Project.objects.get(slug=project)
            log = ProjectLog(
                project=project_obj,
                module="MO",
                headline="Model - {name}".format(name=model.name),
                description="Added reference to a Docker image.",
            )
            log.save()

            return HttpResponseRedirect(reverse("models:details_public", kwargs={"id": id}))
    else:
        form = EnvironmentForm()

    return render(request, "models_docker_image.html", {"form": form})


@login_required
def details(request, user, project, id):
    all_tags = Model.tags.tag_model.objects.all()
    project = Project.objects.filter(slug=project).first()
    model = Model.objects.filter(id=id).first()
    model_access_choices = ["PU", "PR", "LI"]
    model_access_choices.remove(model.access)

    # Note: Removed commented code related to Report

    log_objects = ModelLog.objects.filter(project=project.name, trained_model=model)
    model_logs = []
    for log in log_objects:
        model_logs.append(
            {
                "id": log.id,
                "trained_model": log.trained_model,
                "training_status": log.training_status,
                "training_started_at": log.training_started_at,
                "execution_time": log.execution_time,
                "code_version": log.code_version,
                "current_git_repo": log.current_git_repo,
                "latest_git_commit": log.latest_git_commit,
                "system_details": ast.literal_eval(log.system_details),
                "cpu_details": ast.literal_eval(log.cpu_details),
            }
        )

    md_objects = Metadata.objects.filter(project=project.name, trained_model=model)
    if md_objects:
        metrics = get_chart_data(md_objects)

    filename = None
    readme = None
    import requests as r

    url = "http://{}-file-controller/models/{}/readme".format(project.slug, model.name)
    try:
        response = r.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload["status"] == "OK":
                filename = payload["filename"]

                md = markdown.Markdown(extensions=["extra"])
                readme = md.convert(payload["readme"])
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    return render(request, "models_details.html", locals())


def get_chart_data(md_objects):
    new_data.clear()
    metrics_pre = []
    metrics = []
    for md_item in md_objects:
        metrics_pre.append(
            {
                "run_id": md_item.run_id,
                "metrics": ast.literal_eval(md_item.metrics),
                "parameters": ast.literal_eval(md_item.parameters),
            }
        )
    for m in metrics_pre:
        for key, value in m["metrics"].items():
            new_data[key].append([m["run_id"], value, m["parameters"]])
    for key, value in new_data.items():
        data = []
        labels = []
        params = []
        run_id = []
        run_counter = 0
        for item in value:
            run_counter += 1
            labels.append("Run {}".format(run_counter))
            run_id.append(item[0])
            data.append(item[1])
            params.append(item[2])
        metrics.append(
            {
                "metric": key,
                "details": {
                    "run_id": run_id,
                    "labels": labels,
                    "data": data,
                    "params": params,
                },
            }
        )
    return metrics


def import_model(request, id):
    logger.info("IMPORTING MODEL")


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def details_private(request, user, project, id):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active")
    except Exception:
        logger.error("User not logged in.")
    base_template = "base.html"

    project_slug = project

    try:
        project = Project.objects.filter(
            Q(owner=request.user) | Q(authorized=request.user),
            status="active",
            slug=project_slug,
        ).first()
        # base_template = "projects/base.html"
        base_template = "base.html"
    except Exception as err:
        project = []
        logger.error(str(err), exc_info=True)
    if not project:
        base_template = "base.html"

    media_url = settings.MEDIA_URL
    # TODO: Check that user has access to this model
    # (though already checked that user has access to project)
    model = Model.objects.get(pk=id)
    all_tags = Model.tags.tag_model.objects.all()
    private = True
    logger.info("MY TAGS: %s %s", model.tags, user)
    # published_model = PublishedModel(pk=id)
    # model_objs = published_model.model_obj.order_by('-model__version')
    # latest_model_obj = model_objs[0]
    # model = latest_model_obj.model
    # print(model_objs)
    # print(latest_model_obj)
    bucket = model.bucket
    uid = model.uid

    return render(request, "models/models_details_private.html", locals())


def details_public(request, id):
    private = False
    all_tags = Model.tags.tag_model.objects.all()
    logger.info("Details tag ID:%s", id)
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active")
    except Exception:
        logger.error("User not logged in.", exc_info=True)
    base_template = "base.html"
    if "project" in request.session:
        project_slug = request.session["project"]
        if request.user.is_authenticated:
            # if is_authorized:
            try:
                project = Project.objects.filter(
                    Q(owner=request.user) | Q(authorized=request.user),
                    status="active",
                    slug=project_slug,
                ).first()
                # base_template = "projects/base.html"
                base_template = "base.html"
            except Exception as err:
                project = []
                logger.error(str(err), exc_info=True)
            if not project:
                base_template = "base.html"
    else:
        base_template = "base.html"

    media_url = settings.MEDIA_URL
    logger.info(media_url)
    published_model = PublishedModel(pk=id)
    logger.info(published_model)
    model_objs = published_model.model_obj.order_by("-model__version")
    latest_model_obj = model_objs[0]
    model = latest_model_obj.model
    logger.info(model_objs)
    logger.info(latest_model_obj)

    return render(request, "models/models_details_public.html", locals())


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def delete(request, user, project, id):
    project = Project.objects.get(slug=project)
    model = Model.objects.get(id=id)

    log = ProjectLog(
        project=project,
        module="MO",
        headline="Model",
        description="Model {name} has been removed".format(name=model.name),
    )
    log.save()

    model.delete()

    return HttpResponseRedirect(reverse("models:list", kwargs={"user": user, "project": project.slug}))
