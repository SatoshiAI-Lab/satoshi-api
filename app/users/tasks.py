import json

from django.urls import reverse
from django.test import RequestFactory
from .models import WalletLog

from app.celery import app
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.utils import timezone

from w3.wallet import WalletHandler

logger = get_task_logger(__name__)


@app.task()
def check_solana_hash():
    ten_minutes_ago = timezone.now() - timedelta(minutes=3)
    WalletLog.objects.filter(status = 0, added_at__lt=ten_minutes_ago).update(status = 3)
    objs = WalletLog.objects.filter(status = 0, added_at__gte=ten_minutes_ago)
    if not objs:
        return

    wallet_handler = WalletHandler()
    check_res = wallet_handler.check_hash('Solana', [dict(trxHash=obj.hash_tx, trxTimestamp=int(obj.added_at.timestamp())) for obj in objs])
    if not check_res:
        return
    for index, res in enumerate(check_res):
        if res.get('isPending') == False and res.get('isSuccess') == True: # succeed
            objs[index].status = 1
            objs[index].save()
            break
        elif res.get('isPending') == False and res.get('isSuccess') == True: # failed
            objs[index].status = 3
            objs[index].save()


