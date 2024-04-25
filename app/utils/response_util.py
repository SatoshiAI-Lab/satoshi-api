
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        custom_response_data = {
            'status': response.status_code,
            'message': response.data['detail'],
            'data': None,
        }
        response.data = custom_response_data
    return response


def success(data=None, msg='success'):
    return Response(data={'status': status.HTTP_200_OK, 'message': msg, 'data': data})


def error(data=None, msg='error'):
    return Response(data={'status': status.HTTP_400_BAD_REQUEST, 'message': msg, 'data': data})


def miss_param(data=None, msg='miss param'):
    return Response(data={'status': status.HTTP_400_BAD_REQUEST, 'message': msg, 'data': data})


def param_error(data=None, msg='parm error'):
    return Response(data={'status': status.HTTP_400_BAD_REQUEST, 'message': msg, 'data': data})


def web3_error(data=None, msg='web3 error'):
    return Response(data={'status': status.HTTP_421_MISDIRECTED_REQUEST, 'message': msg, 'data': data})


def jwt_timeout(data=None, msg='jwt timeout'):
    return Response(data={'status': status.HTTP_408_REQUEST_TIMEOUT, 'message': msg, 'data': data})


def data_exist(data=None, msg='data exist'):
    return Response(data={'status': status.HTTP_400_BAD_REQUEST, 'message': msg, 'data': data})


def no_data(data=None, msg='no data'):
    return Response(data={'status': status.HTTP_400_BAD_REQUEST, 'message': msg, 'data': data})


def too_high_frequency(data=None, msg='too high frequency'):
    return Response(data={'status': status.HTTP_429_TOO_MANY_REQUESTS, 'message': msg, 'data': data})

