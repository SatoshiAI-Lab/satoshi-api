
from typing import Any
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context) -> Response | None:
    response: Response | None = exception_handler(exc=exc, context=context)
    if response is not None:
        custom_response_data: dict[str, Any] = {
            'code': response.status_code,
            'message': response.data['detail'],
            'data': None,
        }
        response.data = custom_response_data
    return response


def resp(status, message, data) -> Response:
    return Response(status=status, data={'code': status, 'message': message, 'data': data})


class ResponseUtil():

    @staticmethod
    def success(data=None, msg='OK') -> Response:
        return resp(status=status.HTTP_200_OK, message=msg, data=data)
    
    @staticmethod
    def miss_field(data=None, msg='This field is required.') -> Response:
        return resp(status=status.HTTP_400_BAD_REQUEST, message=msg, data=data)

    @staticmethod
    def field_error(data=None, msg='This field error.') -> Response:
        return resp(status=status.HTTP_400_BAD_REQUEST, message=msg, data=data)
    
    @staticmethod
    def no_data(data=None, msg='Record does not exist.') -> Response:
        return resp(status=status.HTTP_400_BAD_REQUEST, message=msg, data=data)
    
    @staticmethod
    def data_exist(data=None, msg='Record already exists.') -> Response:
        return resp(status=status.HTTP_400_BAD_REQUEST, message=msg, data=data)

    @staticmethod
    def request_timeout(data=None, msg='Request timeout.') -> Response:
        return resp(status=status.HTTP_408_REQUEST_TIMEOUT, message=msg, data=data)
    
    @staticmethod
    def web3_error(data=None, msg='Web3 request error.') -> Response:
        return resp(status=status.HTTP_421_MISDIRECTED_REQUEST, message=msg, data=data)

    @staticmethod
    def too_high_frequency(data=None, msg='Too high frequency.') -> Response:
        return resp(status=status.HTTP_429_TOO_MANY_REQUESTS, message=msg, data=data)
    