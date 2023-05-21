from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from veryusefulproject.core.models import BaseModel


class User(AbstractUser):
    """
    Default custom user model for veryUsefulProject.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    nickname = models.CharField(
        _("Nickname of User"),
        blank=True,
        max_length=255,
        unique=True)
    second_password = models.CharField(_("Second password"), max_length=128)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def set_nickname(self, nickname) -> bool:
        if len(nickname) > 255:
            return False
        if not nickname.isalnum():
            return False
        if User.objects.filter(nickname=nickname).exists():
            return False

        self.nickname = nickname
        return True

    def get_nickname(self) -> models.CharField:
        return self.nickname

    def set_second_password(self, raw_password) -> bool:
        self.second_password = make_password(raw_password)
        return self.check_second_password(raw_password)

    def check_second_password(self, raw_password) -> bool:
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_second_password(raw_password)
            self.save(update_fields=["second_password"])

        return check_password(raw_password, self.second_password, setter)


class Role(BaseModel):
    name = models.CharField(max_length=128)
    desc = models.TextField()
    permissions = models.ManyToManyField(Permission)
    roles = models.ManyToManyField(User)


class UserActivityType(BaseModel):
    name = models.CharField(max_length=128)
    desc = models.TextField()


class UserActivity(BaseModel):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    ip_address = models.GenericIPAddressField()
    activity = models.ForeignKey(UserActivityType, on_delete=models.RESTRICT)
    table_name = models.TextField()
    entity_id = models.TextField()


class UserAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.TextField()
    address1 = models.TextField()
    address2 = models.TextField()
    city = models.TextField()
    state = models.TextField()
    zipcode = models.TextField()
    country = models.TextField()


class UserChat(BaseModel):
    users = models.ManyToManyField(User)


class UserChatMessage(BaseModel):
    chat = models.ForeignKey(UserChat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()


class UserKYCAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.TextField()
    address1 = models.TextField()
    address2 = models.TextField()
    city = models.TextField()
    state = models.TextField()
    zipcode = models.TextField()
    country = models.TextField()


class UserKYCInfo(BaseModel):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    address = models.OneToOneField(UserKYCAddress, on_delete=models.RESTRICT)
    user_id_file = models.FileField(upload_to="kyc_uploads/%Y/%m/%d/")
