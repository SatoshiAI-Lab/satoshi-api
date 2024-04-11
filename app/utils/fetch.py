import requests
from concurrent import futures
import json

import logging

logger = logging.getLogger(__name__)


class MultiFetch():

    @classmethod
    def fetch_url(cls, headers, url):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return json.dumps(dict(data={}))

    @classmethod
    def fetch_multiple_urls(cls, headers, urls):
        with futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {executor.submit(cls.fetch_url, headers, url): url for url in urls}
            results = dict()
            for future in futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    results[url] = data
                except Exception as e:
                    logger.error(f"Error fetching URL '{url}': {str(e)}")
        return results


