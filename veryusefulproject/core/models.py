from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(
            self,
            request=None,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None) -> None:
        return super().save(force_insert, force_update, using, update_fields)
