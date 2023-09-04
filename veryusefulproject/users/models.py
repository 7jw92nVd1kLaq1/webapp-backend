from django.apps import apps
from django.contrib.auth.models import AbstractUser, Permission, UserManager
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from veryusefulproject.core.models import BaseModel


class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, second_password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        if not second_password:
            user.set_second_password(get_random_string(255))
        else:
            user.set_second_password(second_password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, second_password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, second_password, **extra_fields)


class User(AbstractUser):
    """
    Default custom user model for veryUsefulProject.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    objects = CustomUserManager()
    nickname = models.CharField(
        _("Nickname of User"),
        blank=True,
        max_length=255,
        unique=True)
    second_password = models.CharField(_("Second password"), max_length=128)
    REQUIRED_FIELDS = ['second_password']

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['nickname']),
            models.Index(fields=['date_joined']),
        ]

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

    def set_unusable_second_password(self):
        self.second_password = make_password(None)

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
    users = models.ManyToManyField(User)


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
