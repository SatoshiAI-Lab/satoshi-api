import requests
from concurrent import futures


class MultiFetch():

    @classmethod
    def fetch_url(cls, headers, url):
        response = requests.get(url, headers=headers)
        return response.text

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
                    print(f"Error fetching URL '{url}': {str(e)}")
        return results


