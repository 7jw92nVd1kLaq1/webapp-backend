from django.contrib.auth import get_user_model
from rest_framework import serializers

from veryusefulproject.users.forms import RegisterForm

User = get_user_model()

password_regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False)
    nickname = serializers.CharField(max_length=255)
    password = serializers.RegexField(regex=password_regex, write_only=True)
    password_confirmation = serializers.RegexField(regex=password_regex, write_only=True)
    second_password = serializers.RegexField(regex=password_regex, write_only=True)
    second_password_confirmation = serializers.RegexField(regex=password_regex, write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'], validated_data['password'], second_password=validated_data['second_password'], nickname=validated_data['nickname'])
        return user

    def validate(self, attrs):
        if attrs['password_confirmation'] or attrs['second_password_confirmation']:
            form = RegisterForm(attrs)
            if not form.is_valid():
                raise serializers.ValidationError(form.errors)

        return attrs
