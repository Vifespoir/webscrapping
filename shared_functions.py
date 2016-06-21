import getpass  # hide bearer token in the console
import requests
import tldextract  # to extract main domain address
import shelve
import logging


def get_api_token(text):
    """Get API token."""
    logging.debug("get_api_token Started")
    if text == "EmailHunter":
        return "f92e50737d8056c27c09596d4b2d8bcf579aa9c6"
    elif text == "ProductHunter":
        return "30dfd116f2ed23fc691f264fd8d09d1714b8395ffc6a42d319095f9b367c19a5"
    else:
        logging.debug("get_api_token Invalid API token")
        api_token = getpass.getpass('Enter ' + text + ' API token: ')
        return api_token


def url_extractor(redirect_url):
    """Extract final url from redirect url."""
    # set headers to a browser value
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) A\
    ppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=5)
    s.mount('http://', a)

    try:  # capture URL Errors
        req = s.get(redirect_url, headers=headers)  # find final url
        extracted_url = tldextract.extract(req.url).registered_domain
    except requests.exceptions.ConnectionError as e:
        print("requests.exceptions.ConnectionError")
        print(redirect_url)
        print(e)
        extracted_url = 'Url Extractor Error'

    return extracted_url


class WebscrappingLogs():
    """docstring for ProductHunterLog."""
    shelf_file = shelve.open('Webscrapping')

    def __init__(self, name):
        logging.debug(
            'Initialized WebscrappingLogs Class, log name: %s' % name)
        self.name = name
        self.load_logs()

    def load_logs(self):
        try:
            self.shelf_file[self.name]
            status = 'Logs found'
        except KeyError:
            self.shelf_file[self.name] = {}
            status = 'Logs not found'
        finally:
            logging.info('ProductHunterLogs.load_logs %s' % status)
            self.data = self.shelf_file[self.name]

    def store_logs(self, item_to_log):
        """Record info to avoid calling the API twice for the same person."""
        logging.info(
            'ProductHunterLogs.store_logs "%s" stored' % self.name)
        self.shelf_file[self.name] = item_to_log
