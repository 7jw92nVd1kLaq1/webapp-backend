from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract: bool = True

    @property
    def created_at_formatted(self):
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def modified_at_formatted(self):
        return self.modified_at.strftime("%Y-%m-%d %H:%M:%S")

    def save(
            self,
            request=None,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None) -> None:
        return super().save(force_insert, force_update, using, update_fields)
