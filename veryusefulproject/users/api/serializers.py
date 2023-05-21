from django.contrib.auth import get_user_model
from rest_framework import serializers

from veryusefulproject.users.forms import RegisterForm

User = get_user_model()

password_regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.RegexField(regex=password_regex)
    password_confirmation = serializers.RegexField(regex=password_regex)
    second_password = serializers.RegexField(regex=password_regex)
    second_password_confirmation = serializers.RegexField(regex=password_regex)

    class Meta:
        model = User
        fields = ["username", "nickname", "password", "email", "password_confirmation",
                  "second_password", "second_password_confirmation", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"},
            "password": {"write_only": True},
            "second_password": {"write_only": True},
            "password_confirmation": {"write_only": True},
            "second_password_confirmation": {"write_only": True},
            "email": {"write_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['password'], validated_data['email'])

        user.set_nickname(validated_data['nickname'])
        user.set_second_password(validated_data['second_password'])
        user.save()

        print(f"User named {validated_data['username']} successfully created!")

        return user

    def validate(self, attrs):
        form = RegisterForm(attrs)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return super().validate(attrs)
