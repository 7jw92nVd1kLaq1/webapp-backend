from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from veryusefulproject.core.mixins import DynamicFieldsSerializerMixin
from veryusefulproject.core.api.serializers import CustomerSerializerMetaClass
from veryusefulproject.orders.api.serializers import OrderSerializer
from veryusefulproject.users.forms import RegisterForm

from ..models import Role

User = get_user_model()


class RoleSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(DynamicFieldsSerializerMixin, serializers.ModelSerializer):
    role_set = RoleSerializer(many=True, read_only=True)
    orders_as_customer = OrderSerializer(many=True)
    orders_as_intermediary = OrderSerializer(many=True)

    class Meta:
        model = User
        fields = [
            'username',
            'nickname',
            'email',
            'password',
            'second_password',
            'orders_as_customer',
            'orders_as_intermediary',
            'is_staff',
            'role_set',
            'date_joined'
        ]
        read_only_fields = [
            'orders_as_customer',
            'orders_as_intermediary',
            "is_staff",
            "date_joined",
            'role_set',
        ]
        extra_kwargs = {
            'password': {'write_only': True, "required": False},
            'second_password': {'write_only': True, "required": False},
        }

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'], validated_data['password'], second_password=validated_data['second_password'], nickname=validated_data['nickname'])
        return user

    def update(self, instance, validated_data):
        for field in validated_data:
            if not self.fields.get(field, None):
                continue
            if self.fields[field].read_only:
                continue

            if field == "password":
                instance.set_password(validated_data[field])
            elif field == "second_password":
                instance.set_second_password(validated_data[field])

            setattr(instance, field, validated_data[field])

        instance.save()
        return instance


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    nickname = serializers.CharField(max_length=255)
    password = serializers.RegexField(regex=settings.PASSWORD_REQUIREMENT_REGEX, write_only=True)
    password_confirmation = serializers.RegexField(regex=settings.PASSWORD_REQUIREMENT_REGEX, write_only=True)
    second_password = serializers.RegexField(regex=settings.PASSWORD_REQUIREMENT_REGEX, write_only=True)
    second_password_confirmation = serializers.RegexField(regex=settings.PASSWORD_REQUIREMENT_REGEX, write_only=True)

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
