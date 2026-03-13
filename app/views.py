from http import HTTPStatus

from django.http import HttpRequest, HttpResponse


def healthy(request: HttpRequest) -> HttpResponse:
    return HttpResponse(status=HTTPStatus.OK, content=request.get_host())
