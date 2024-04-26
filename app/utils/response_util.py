
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
    return Response(data={'status': status, 'message': message, 'data': data})


class ResponseUtil():

    @staticmethod
    def success(data=None, msg='success'):
        return resp(status.HTTP_200_OK, msg, data)
    
    @staticmethod
    def param_error(data=None, msg='miss param'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)

    @staticmethod
    def param_error(data=None, msg='param error'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)
    
    @staticmethod
    def no_data(data=None, msg='data does not exist'):
        return resp(status.HTTP_400_BAD_REQUEST, msg, data)

    @staticmethod
    def request_timeout(data=None, msg='request timeout'):
        return resp(status.HTTP_408_REQUEST_TIMEOUT, msg, data)

    @staticmethod
    def data_exist(data=None, msg='data already exists'):
        return resp(status.HTTP_409_CONFLICT, msg, data)
    
    @staticmethod
    def web3_error(data=None, msg='web3 error'):
        return resp(status.HTTP_421_MISDIRECTED_REQUEST, msg, data)

    @staticmethod
    def too_high_frequency(data=None, msg='too high frequency'):
        return resp(status.HTTP_429_TOO_MANY_REQUESTS, msg, data)
    
    # @staticmethod
    # def user_exists(data=None):
    #     return resp(10001, 'user already exists', data)
    