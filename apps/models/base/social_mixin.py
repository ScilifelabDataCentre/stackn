from django.db import models
from tagulous.models import TagField


class SocialMixin(models.Model):
    tags = TagField(blank=True)
    note_on_linkonly_privacy = models.TextField(blank=True, null=True, default="")
    collections = models.ManyToManyField("portal.Collection", blank=True, related_name="%(class)s")
    source_code_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True, default="")

    class Meta:
        abstract = True
