#!python3
"""Main script."""

import os  # to create output in the script directory
import sys
import csv
from ProductHunt_get_makers import generate_ph_data
from EmailHunter_get_email import EmailHunterAPI


def ProductHunter_to_EmailHunter(dataset):
    """Format each dataset into a smaller one containing important information.

    It captures two kind of errors: no makers and empty list of makers.
    It returns the extracted information and an error report.
    """
    for data in dataset:
        format_name = format_names(dataset[data]['name'])
        dataset[data]['first_name'] = format_name[0]
        dataset[data]['last_name'] = format_name[1]
        dataset[data]['completeness'] = format_name[3]
        dataset[data]['domain'] = dataset[data].pop("url")

        if format_name[2]:
            data_cp = dataset[data].copy()
            eh_keys = ['first_name', 'last_name', 'domain']
            data_cp = {k: v for k, v in data_cp.items() if k in eh_keys}
            email_resp = get_email(data_cp)
            if email_resp[0] is not None:
                print(email_resp)
                dataset[data]['email'] = email_resp[0]
                dataset[data]['score'] = email_resp[1]
            else:
                data_cp['domain'] = dataset[data]['website_url']
                data_cp.pop('email')
                data_cp.pop('score')
                email_resp = get_email(data_cp)

                dataset[data]['email'] = email_resp[0]
                dataset[data]['score'] = email_resp[1]
        else:
            dataset[data]['email'] = None
            dataset[data]['score'] = None

    return dataset


def get_email(data):
    """Use EmailHunter_get_email module to find an email from data."""
    email_request = EmailHunterAPI(data)
    email_request.get_email()
    email = email_request.person['email']
    score = email_request.person['score']
    print(str(email) + '  ' + str(score))
    return email, score


def format_names(name):
    """Take a name and return a first & last name version of it."""
    name = name.rsplit()  # break down maker name
    if len(name) == 2:  # assign maker and maker lastname
        return (name[0], name[1], True, 'Full')
    elif len(name) > 2:  # first word as maker, the rest as lastname
        return (name[0], name[1:], True, 'Check the name')
    else:  # when only one word set it in maker
        return (name[0], None, False, 'Invalid name')


def csv_writer(dataset, file_location):
    """Write the data into a file. Show the progression."""
    counter = 0  # counter to show the progress
    print('Creating csv file at the script root: ' + file_location +
          'with: \'w\' privileges')
    csvfile = open(file_location, 'w', newline='')
    fieldnames = ['company',  # fieldnames they match the one in data_formatter
                  'domain',
                  'first_name',
                  'last_name',
                  'email',
                  'score',
                  'headline',
                  'completeness',
                  'website_url',
                  'twitter_username']

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)  # set the writer
    writer.writeheader()  # write the headers

    for data in dataset.data:  # loop though the data
        sys.stdout.write(  # progress
            '\r{:20}  {:20}  {:20}   Progress: {:.2f}%'.format(
                str(dataset.data[data]["first_name"]),
                str(dataset.data[data]["last_name"]),
                str(dataset.data[data]["email"]),
                (float(counter)/len(dataset.data))*100))
        dataset.data[data].pop('id')
        dataset.data[data].pop('name')
        writer.writerow(dataset.data[data])
        counter += 1  # increment the progress


if __name__ == '__main__':
    data, topic_str = generate_ph_data()
    print("Generate ProductHunt data finished!")

    cwd = os.getcwd()  # getting current working directory
    file_location = cwd + '/' + topic_str + '.csv'
    ProductHunter_to_EmailHunter(data.data)
    csv_writer(data, file_location)  # write the data
