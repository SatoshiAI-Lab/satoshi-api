from typing import Any
import requests
from concurrent import futures
import json

import logging

logger: logging.Logger = logging.getLogger(name=__name__)


class MultiFetch():

    @classmethod
    def fetch_url(cls, headers: dict, url: str) -> str:
        try:
            response: requests.Response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return dict(data=dict())

    @classmethod
    def fetch_multiple_urls(cls, headers: dict, urls: list[str]) -> dict:
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url: dict = {executor.submit(cls.fetch_url, headers, url): url for url in urls}
            results = dict()
            for future in futures.as_completed(fs=future_to_url):
                url: str = future_to_url[future]
                try:
                    data: Any = future.result()
                    results[url] = data
                except Exception as e:
                    logger.error(msg=f"Error fetching URL '{url}': {str(object=e)}")
        return results


