from django import forms
from django.forms.forms import ValidationError
from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


import re

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up sectionscreen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100, strip=True)
    password = forms.CharField(max_length=100)
    password_confirmation = forms.CharField(max_length=100)
    second_password = forms.CharField(max_length=100)
    second_password_confirmation = forms.CharField(max_length=100)
    email = forms.EmailField()
    nickname = forms.CharField(max_length=255)

    def clean_username(self):
        data = self.cleaned_data['username']

        if len(data) < 5 or len(data) > 150:
            raise ValidationError(_("The length of your username must be somewhere between 6 and 150 characters."))
        if re.search('\W', data):
            raise ValidationError(_("Your username contains one or more non-alphanumeric characters."))

        if User.objects.filter(username=data).exists():
            return ValidationError(_("The username already exists."))

        return data

    def clean_password(self):
        data = self.cleaned_data['password']

        if not re.search("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", data):
            raise ValidationError(
                _("Your password must contain at least one uppercase, lowercase, special, and numeric characters."))

        return data

    def clean_password_confirmation(self):
        data = self.cleaned_data["password_confirmation"]
        password = self.cleaned_data["password"]

        if data != password:
            raise ValidationError(_("Your password and re-typed password don't match."))

    def clean_second_password(self):
        data = self.cleaned_data['second_password']

        if not re.search("^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", data):
            raise ValidationError(
                _("Your second password must contain at least one uppercase, lowercase, special, and numeric characters."))

        return data

    def clean_second_password_confirmation(self):
        data = self.cleaned_data["second_password_confirmation"]
        password = self.cleaned_data["second_password"]

        if data != password:
            raise ValidationError(_("Your second password and re-typed second password don't match."))

        return data

    def clean_nickname(self):
        data = self.cleaned_data['nickname']

        if len(data) <= 4:
            raise ValidationError(_("Your nickname must not be shorter than 5 characters"))

        return data
