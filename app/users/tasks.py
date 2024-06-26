import json
import logging

from django.db.models.manager import BaseManager
from django.urls import reverse
from django.test import RequestFactory
from .models import WalletLog

from app.celery import app
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.utils import timezone

from w3.wallet import WalletHandler

logger: logging.Logger = get_task_logger(name=__name__)


@app.task()
def check_hash() -> None:
    minutes_ago: datetime = timezone.now() - timedelta(minutes=3)
    WalletLog.objects.filter(status = 0, added_at__lt=minutes_ago).update(status = 2)

    wallet_handler: WalletHandler = WalletHandler()

    objs: BaseManager[WalletLog] = WalletLog.objects.filter(status = 0, added_at__gte=minutes_ago)
    if not objs:
        return
    objs_dict: dict[str, BaseManager[WalletLog]] = dict()
    for obj in objs:
        if not objs_dict.get(obj.chain):
            objs_dict[obj.chain] = [obj]
        else:
            objs_dict[obj.chain].append(obj)
    
    if 'solana' in objs_dict:
        sol_objs: BaseManager[WalletLog] = objs_dict.pop('solana')
        check_res: list | None = wallet_handler.check_hash(chain='solana', data_list=[dict(trxHash=obj.hash_tx, trxTimestamp=int(obj.added_at.timestamp())) for obj in sol_objs])
        for index, res in enumerate(iterable=check_res):
            if res.get('isPending') == False and res.get('isSuccess') == True: # succeed
                sol_objs[index].status = 1
                sol_objs[index].save()
                break
            elif res.get('isPending') == False and res.get('isSuccess') == False: # failed
                sol_objs[index].status = 3
                sol_objs[index].save()

    if not objs_dict:
        return
    data: dict = dict()
    for chain, objs in objs_dict.items():
        data[chain] = [dict(trxHash=obj.hash_tx, trxTimestamp=int(obj.added_at.timestamp())) for obj in objs]
    check_res: dict | None = wallet_handler.multi_check_hash(hash_data=data)
    if not check_res:
        return
    for chain, vals in check_res.items():
        for index, res in enumerate(iterable=vals):
            if res.get('isPending') == False and res.get('isSuccess') == True: # succeed
                objs_dict[chain][index].status = 1
                objs_dict[chain][index].save()
                break
            elif res.get('isPending') == False and res.get('isSuccess') == False: # failed
                objs_dict[chain][index].status = 3
                objs_dict[chain][index].save()



