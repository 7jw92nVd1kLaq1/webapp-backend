from django.conf import settings
from django.middleware.csrf import get_token

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        value = get_token(request),
        response = Response({'csrftoken': value})

        response.set_cookie(
            key='csrftoken',
            value=value,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        )
        return response
