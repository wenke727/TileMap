import os
import requests


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63"


def get_proxy(proxy_url=None):
    if proxy_url is None:
        return None
    
    try:
        response = requests.get(proxy_url)
        if response.status_code == 200:
            return {'http': response.text} 
    except requests.exceptions.ConnectionError:
        return None


def http_retryer(url, wait, max_retries, proxy=None):
    """
    Retry a url many times in attempt to get a tile

    Arguments
    ---------
    tile_url : str
        string that is the target of the web request. Should be
        a properly-formatted url for a tile provider.
    wait : int
        if the tile API is rate-limited, the number of seconds to wait
        between a failed request and the next try
    max_retries : int
        total number of rejected requests allowed before contextily
        will stop trying to fetch more tiles from a rate-limited API.

    Returns
    -------
    request object containing the web response.
    """
    try:
        request = requests.get(url, headers={"user-agent": USER_AGENT}, proxies=proxy)
        request.raise_for_status()
    except requests.HTTPError:
        if request.status_code == 404:
            raise requests.HTTPError(
                "Tile URL resulted in a 404 error. "
                "Double-check your tile url:\n{}".format(url)
            )
        elif request.status_code == 104:
            if max_retries > 0:
                os.wait(wait)
                max_retries -= 1
                request = http_retryer(url, wait, max_retries, proxy)
            else:
                raise requests.HTTPError("Connection reset by peer too many times.")
    return request

