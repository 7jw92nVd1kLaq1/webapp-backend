from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import Response

from veryusefulproject.users.api.serializers import UserSerializer

User = get_user_model()


class AdminListUsersView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        fields = (
            "username",
            "email",
            "date_joined",
            "is_staff"
        )
        serializer = self.get_serializer(self.get_queryset(), fields=fields, many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)
