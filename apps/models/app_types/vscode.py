from django.db import models

from apps.models import AppInstanceManager, BaseAppInstance


class VSCodeInstanceManager(AppInstanceManager):
    model_type = "vscodeinstance"


class VSCodeInstance(BaseAppInstance):
    objects = VSCodeInstanceManager()
    ACCESS_TYPES = (
        ("project", "Project"),
        ("private", "Private"),
    )
    volume = models.ManyToManyField("VolumeInstance", blank=True)
    access = models.CharField(max_length=20, default="project", choices=ACCESS_TYPES)

    def get_k8s_values(self):
        k8s_values = super().get_k8s_values()

        k8s_values["permission"] = str(self.access)
        # Not the nicest perhaps, but it works since the charts assume that the volumes are on this form
        # {apps:
        #   {volumeK8s:
        #       {project-vol:
        #           {release: r1582t9h9

        volumeK8s_dict = {"volumeK8s": {}}
        for object in self.volume.all():
            volumeK8s_dict["volumeK8s"][object.name] = dict(release=object.subdomain.subdomain)
        k8s_values["apps"] = volumeK8s_dict
        return k8s_values

    class Meta:
        verbose_name = "VS Code Instance"
        verbose_name_plural = "VS Code Instances"
        permissions = [("can_access_app", "Can access app service")]
