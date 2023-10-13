from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from rest_framework_simplejwt.authentication import JWTAuthentication


class PreventSuspendedUsersMiddleware(MiddlewareMixin):
    def _reject(self, request, reason):
        return HttpResponse(reason)

    def process_request(self, request):
        auth = JWTAuthentication()
        value = auth.authenticate(request)

        if not value:
            return None

        if value[0].roles.filter(name="Suspended").exists():
            raise PermissionDenied("This user is suspended.")

    def process_view(self, request, callback, callback_args, callback_kwargs):
        pass

    def process_response(self, request, response):
        return response
