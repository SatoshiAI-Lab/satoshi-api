
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        custom_response_data = {
            'code': response.status_code,
            'message': response.data['detail'],
            'data': None,
        }
        response.data = custom_response_data
    return response


def resp(status, message, data):
    return Response(data={'code': status, 'message': message, 'data': data})


class ResponseUtil():

    @staticmethod
    def success(data=None, msg='OK'):
        return resp(status.HTTP_200_OK, msg, data)
    
    @staticmethod
    def param_error(data=None, msg='This field is required.'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)

    @staticmethod
    def param_error(data=None, msg='Param error.'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)
    
    @staticmethod
    def no_data(data=None, msg='Data does not exist.'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)

    @staticmethod
    def request_timeout(data=None, msg='Request timeout.'):
        return resp(status.HTTP_408_REQUEST_TIMEOUT, msg, data)

    @staticmethod
    def data_exist(data=None, msg='Data already exists.'):
        return resp(status.HTTP_409_CONFLICT, msg, data)
    
    @staticmethod
    def web3_error(data=None, msg='Web3 request error.'):
        return resp(status.HTTP_421_MISDIRECTED_REQUEST, msg, data)

    @staticmethod
    def too_high_frequency(data=None, msg='Too high frequency.'):
        return resp(status.HTTP_429_TOO_MANY_REQUESTS, msg, data)
    