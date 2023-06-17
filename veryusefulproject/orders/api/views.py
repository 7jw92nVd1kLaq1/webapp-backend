from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from ..tasks import get_product_info

from veryusefulproject.users.api.authentication import JWTAuthentication


class RequestItemInfoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        url = request.data.get("url", None)

        print(url)
        if not url:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"reason": "You forgot to provide an URL."})

        get_product_info.delay(url, request.user.get_username())
        return Response(status=status.HTTP_200_OK)


