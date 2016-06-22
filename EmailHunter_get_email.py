#!python3

"""Call EmailHunter API and find an email.

This script will find an email using EmailHunter API. It requires: first name,
last name and a domain name.
"""
# importing libraries
import requests
import shelve
import shared_functions
import logging


logging.basicConfig(
    level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')


class EmailHunterAPI():
    """docstring for PersonLookUpInfo."""

    base_url = "https://api.emailhunter.co/v1/generate?"
    test_passed = False

    def __init__(self, person):
        """Initialize PersonLookUpInfo."""
        assert isinstance(person, dict),\
            'Dictionary expected, wrong input: %s' % person
        self.get_api_token()
        self.person = person
        self.id = ''.join([str(v) for k, v in self.person.items()])
        assert self.id
        logging.debug('EmailHunterAPI Initialized')
        logging.debug('EmailHunterAPI person: %s' % self.person)

    def set_params(self):
        """Add the API token to form complete parameters."""
        logging.debug('EmailHunterAPI.set_params Started')
        self.params = self.person.copy()
        self.params['api_key'] = EmailHunterAPI.api_key
        logging.debug('EmailHunterAPI.set_params params set')

    def get_api_token(self):
        """Obtain the API token and test if it works."""
        logging.debug('EmailHunterAPI.get_api_token Started')
        EmailHunterAPI.api_key =\
            shared_functions.get_api_token('EmailHunter')
        if not self.test_passed:
            logging.debug('EmailHunterAPI.get_api_token wrong API token')
            self.test()
            self.get_api_token()
        else:
            logging.debug(
                'EmailHunterAPI.get_api_token: %s' % 'correct API token')

    def test(self):
        """Test the class."""
        logging.debug('EmailHunterAPI.test Started')
        params = {"domain": "asana.com", "first_name": "Dustin",
                  "last_name": "Moskovitz"}
        params['api_key'] = self.api_key
        resp = requests.get(self.base_url, params=params)
        resp.raise_for_status()
        print(resp.json()['email'])
        logging.debug('EmailHunterAPI.test Successful')
        EmailHunterAPI.test_passed = True

    def get_email(self):
        """Call email hunter, return an email.

        Requires the base EmailHunter url & the parameters to be added to the
        url.
        Additionally requires logs to avoid to call twice the API with the same
        parameters.
        """
        logging.debug('EmailHunterAPI.get_email Started')
        eh_keys = ['domain', 'first_name', 'last_name']
        assert isinstance(self.person, dict) is True, 'not a dict'
        c_keys = [k for k in self.person.keys()]
        assert isinstance(c_keys, list) is True, 'not a list'
        c_keys.sort()
        logging.debug('EmailHunterAPI.get_email keys sort %s' % c_keys)
        assert eh_keys == c_keys, 'Invalid request: {}\nKey needed: {}'.format(
                '   '.join(c_keys), '   '.join(eh_keys))
        self.set_params()
        self.person.setdefault('email', None)
        self.person.setdefault('score', None)

        emailsLogs = EmailHunterLogs('emails')

        if self.id in emailsLogs.data.keys():
            logging.debug('EmailHunterAPI.get_email email found')
        else:
            logging.debug('EmailHunterAPI.get_email email not found')
            resp = requests.get(self.base_url, params=self.params)
            # pp = pprint.PrettyPrinter(indent=4)
            # pp.pprint(resp.json())
            try:
                self.person['email'] = resp.json()['email']
                self.person['score'] = resp.json()['score']
            except KeyError:
                self.person['email'] = None
                self.person['email'] = None
                logging.warning('EmailHunterAPI.get_email Invalid request:\
                    "%s"' % self.person)
            logging.debug('EmailHunterAPI.get_email Email: "%s"'
                          % self.person['email'])
            emailsLogs.data[self.id] = self.person

        emailsLogs.store_logs(emailsLogs.data)


class EmailHunterLogs(shared_functions.WebscrappingLogs):
    """docstring for EmailHunterLogs."""

    shelf_file = shelve.open('EmailHunter')


if __name__ == '__main__':
    etienne = {"domain": "asana.com", "first_name": "Dustin",
               "last_name": "Moskovitz"}
    test = EmailHunterAPI(etienne)
