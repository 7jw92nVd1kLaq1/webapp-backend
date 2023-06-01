from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import GenericViewSet

from veryusefulproject.users.api.serializers import UserSerializer
from veryusefulproject.users.api.authentication import JWTAuthentication

User = get_user_model()


class AdminUsersViewSet(ListModelMixin, UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def _remove_fields(self, data, key, fields_include):
        if isinstance(fields_include, str):
            fields_include = [fields_include]

        if not key in data:
            return data

        if isinstance(data[key], list):
            for each in data[key]:
                for field in each:
                    if not field in fields_include:
                        each.pop(field)
        else:
            for each in data[key]:
                if not each in fields_include:
                    each.pop(each)

        return data

    def list(self, request, *args, **kwargs):
        fields = (
            "username",
            "email",
            "date_joined",
            "is_staff"
        )
        serializer = self.get_serializer_class()(
            self.get_queryset().only(*fields),
            fields=fields,
            many=True
        )

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            self.get_queryset().get(**{self.lookup_field: kwargs.get(self.lookup_field)})
        )

        data = self._remove_fields(
            serializer.data,
            'orders_as_customer',
            ['url_id', 'customer', 'intermediary']
        )

        data = self._remove_fields(
            serializer.data,
            'orders_as_intermediary',
            ['url_id', 'customer', 'intermediary']
        )

        data = self._remove_fields(
            serializer.data,
            'role_set',
            ['name']
        )
        return Response(data=data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            self.get_queryset().get(**{self.lookup_field: kwargs.get(self.lookup_field)}),
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)
