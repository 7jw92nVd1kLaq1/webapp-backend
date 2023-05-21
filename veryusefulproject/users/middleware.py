from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import _get_failure_view


class PreventSuspendedUsersMiddleware(MiddlewareMixin):
    def _reject(self, request, reason):
        return HttpResponse(reason)

    def process_request(self, request):
        pass

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.user.is_authenticated:
            return None

        if request.user.role_set.filter(name="Suspended").exists():
            return self._reject(request, "User is suspended")

        return None

    def process_response(self, request, response):
        return response
