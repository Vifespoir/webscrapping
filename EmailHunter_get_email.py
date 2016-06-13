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


def eh_get_email(url, params, logs):
    """Call email hunter, return an email.

    Requires the base EmailHunter url & the parameters to be added to the url.
    Additionally requires logs to avoid to call twice the API with the same
    parameters.
    """
    # TEST eh_params = api_params_test
    person = check_if_call_is_unique(params=params, logs=logs)
    if person:
        resp = requests.get(url, params=params)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(resp.json())
        person['email'] = resp.json()['email']
        person['score'] = resp.json()['score']
        eh_logs.append(person)

        return eh_logs, person
    else:
        return eh_logs, None


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


if __name__ == '__main__':
    shelf_file = shelve.open('EmailHunter')
    try:
        eh_logs = shelf_file['eh_logs']
    except KeyError:
        eh_logs = []

    eh_base_url = "https://api.emailhunter.co/v1/generate?"

    api_params_test = {
        "api_key": "f92e50737d8056c27c09596d4b2d8bcf579aa9c6",
        "domain": "asanag.com",
        "first_name": "Dustin",
        "last_name": "Moskovitz"}
    test = eh_get_email(
        url=eh_base_url,
        params=api_params_test,
        logs=eh_logs)

    shelf_file['eh_logs'] = test[0]
    print(test[1])
