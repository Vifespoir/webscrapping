#!python3

"""Call EmailHunter API and find an email.

This script will find an email using EmailHunter API. It requires: first name,
last name and a domain name.
"""
# importing libraries
import requests
import pprint
import shelve
import re
import shared_functions
import json


class PersonLookUpInfo():
    """docstring for PersonLookUpInfo."""

    base_url = "https://api.emailhunter.co/v1/generate?"

    shelf_file = shelve.open('EmailHunter')
    try:
        eh_logs = shelf_file['eh_logs']
    except KeyError:
        eh_logs = []

    def __init__(self, person):
        """Initialize PersonLookUpInfo."""
        self.get_api_token()
        self.person = person
        self.params = self.set_params()
        self.email = self.eh_get_email()

    def set_params(self):
        self.params = self.person
        self.params['api_key'] = PersonLookUpInfo.api_key
        return self.params

    def get_api_token(self):
        try:
            self.api_key
        except:
            PersonLookUpInfo.api_key =\
                shared_functions.get_api_token("EmailHunter")

    def store_logs():
        """Record info to avoid calling the API twice for the same person."""
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(PersonLookUpInfo.eh_logs)
        eh_logs = PersonLookUpInfo.eh_logs
        eh_logs = [json.dumps(item, sort_keys=True) for item in eh_logs]
        eh_logs = set(eh_logs)
        eh_logs = [json.loads(item) for item in eh_logs]
        PersonLookUpInfo.shelf_file['eh_logs'] = eh_logs

    def test(self):
        """Test the class."""
        self.person = {"domain": "asana.com", "first_name": "Dustin",
                       "last_name": "Moskovitz"}
        self.params
        try:
            self.email
            self.store_logs()
        except:
            print("Test unsuccessful")

    def eh_get_email(self):
        """Call email hunter, return an email.

        Requires the base EmailHunter url & the parameters to be added to the
        url.
        Additionally requires logs to avoid to call twice the API with the same
        parameters.
        """
        if self.params["first_name"]:
            check_if_unique = self.check_if_call_is_unique()
            if check_if_unique:
                s = requests.Session()
                a = requests.adapters.HTTPAdapter(max_retries=10)
                s.mount('http://', a)

                resp = s.get(self.base_url, params=self.params)
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(resp.json())
                try:
                    self.person['email'] = resp.json()['email']
                    self.person['score'] = resp.json()['score']
                    return True
                except KeyError:
                    return False
                finally:
                    self.person.pop("api_key")
                    PersonLookUpInfo.eh_logs.append(self.person)
            else:
                return False
        else:
            print("\nNo Name")

    def check_if_call_is_unique(self):
        """Check parameters against logs return a person or None."""
        person = self.params.copy()
        intersect = set()

        for log in self.eh_logs:
            intersect = set(person.items()).intersection(set(log.items()))
            if len(intersect) >= 1:
                intersect = dict(intersect)
                break

        if len(intersect) == 3:
            print('\nEntry found')
            self.person = log
            PersonLookUpInfo.eh_logs.append(self.person)
        elif len(intersect) >= 1:
            try:
                intersect["first_name"]
                intersect["last_name"]
            except KeyError:
                return True

            print('\nEntry found')
            print(log, '\n', person)
            check = re.match('(y|Y)',
                             input('Look up this person again? (y/n)'))
            try:
                check.groups()
                return True
            except AttributeError as e:
                print(e)
                return False
        else:
            return True
