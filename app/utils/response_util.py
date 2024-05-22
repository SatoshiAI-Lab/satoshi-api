
from typing import Any
from rest_framework.response import Response
from rest_framework import status as code_status
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Any, context: str) -> Response | None:
    response: Response | None = exception_handler(exc=exc, context=context)
    if response is not None:
        custom_response_data: dict[str, Any] = {
            'code': response.status_code,
            'message': response.data['detail'],
            'data': None,
        }
        response.data = custom_response_data
    return response


def resp(status: int, message: str, data: dict | None) -> Response:
    return Response(status=status, data={'code': status, 'message': message, 'data': data})


class ResponseUtil():

    @staticmethod
    def success(data: dict | None=None, msg: str='OK') -> Response:
        return resp(status=code_status.HTTP_200_OK, message=msg, data=data)
    
    @staticmethod
    def miss_field(data: dict | None=None, msg: str='This field is required.') -> Response:
        return resp(status=code_status.HTTP_400_BAD_REQUEST, message=msg, data=data)

    @staticmethod
    def field_error(data: dict | None=None, msg: str='This field error.') -> Response:
        return resp(status=code_status.HTTP_400_BAD_REQUEST, message=msg, data=data)
    
    @staticmethod
    def no_data(data: dict | None=None, msg: str='Record does not exist.') -> Response:
        return resp(status=code_status.HTTP_400_BAD_REQUEST, message=msg, data=data)
    
    @staticmethod
    def data_exist(data: dict | None=None, msg: str='Record already exists.') -> Response:
        return resp(status=code_status.HTTP_400_BAD_REQUEST, message=msg, data=data)

    @staticmethod
    def request_timeout(data: dict | None=None, msg: str='Request timeout.') -> Response:
        return resp(status=code_status.HTTP_408_REQUEST_TIMEOUT, message=msg, data=data)
    
    @staticmethod
    def web3_error(data: dict | None=None, msg: str='Web3 request error.') -> Response:
        return resp(status=code_status.HTTP_421_MISDIRECTED_REQUEST, message=msg, data=data)

    @staticmethod
    def too_high_frequency(data: dict | None=None, msg: str='Too high frequency.') -> Response:
        return resp(status=code_status.HTTP_429_TOO_MANY_REQUESTS, message=msg, data=data)
    
    @staticmethod
    def custom(status: int, data: dict | None, msg: str) -> Response:
        return resp(status=status, message=msg, data=data)
    