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


def eh_get_email(person):
    """Call email hunter, return an email.

    Requires the base EmailHunter url & the parameters to be added to the
    url.
    Additionally requires logs to avoid to call twice the API with the same
    parameters.
    """
    url = person.base_url
    params = person.params
    logs = person.logs
    # TEST eh_params = api_params_test
    person = PersonLookUpInfo.check_if_call_is_unique(
        params=params, logs=logs)
    if person:
        resp = requests.get(url, params=params)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(resp.json())
        person['email'] = resp.json()['email']
        person['score'] = resp.json()['score']

        return person
    else:
        return None


def check_if_call_is_unique(params, logs):
    """Check parameters against logs return a person or None."""
    person = params.copy()
    person.pop('api_key')
    if logs:
        for log in logs:
            intersect = set(person.items()).intersection(set(log.items()))
            if intersect:
                print('intersect', intersect)
            print('')
            print('log', str(log), type(str(log)))
            if len(intersect) == 3:
                print('Entry found:')
                print(log)
                return None
            elif intersect and not log['email']:
                print('Entry found:')
                print(log, '\n', person)
                check = re.match('(y|Y)',
                                 input('Look up this person again? (y/n)'))
                try:
                    check.groups()
                    return person
                except AttributeError:
                    return None
            else:
                return person
    else:
        print('No logs found')
        return person


class PersonLookUpInfo():
    """docstring for PersonLookUpInfo."""

    base_url = "https://api.emailhunter.co/v1/generate?"

    api_key = shared_functions.get_api_token("EmailHunter")
    test_data = {"domain": "asanag.com",
                 "first_name": "Dustin",
                 "last_name": "Moskovitz"}
    test_data["api_key"] = api_key
    shared_functions.check_api_token(eh_get_email(test_data))

    shelf_file = shelve.open('EmailHunter')
    try:
        eh_logs = shelf_file['eh_logs']
    except KeyError:
        eh_logs = []

    def __init__(self, person):
        """Initialize PersonLookUpInfo."""
        self.person = person
        self.person['api_key'] = PersonLookUpInfo.api_key
        self.logs = PersonLookUpInfo.logger(self.person)
        self.email = eh_get_email(self.person)

    def logger(email):
        """Record info to avoid calling the API twice for the same person."""
        if email:
            logs = PersonLookUpInfo.eh_logs
            logs.append(email[0])
            PersonLookUpInfo.shelf_file['eh_logs'] = logs
