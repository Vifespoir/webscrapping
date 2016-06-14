#!python3
"""Main script."""

import os  # to create output in the script directory
import sys
import csv
from ProductHunt_get_makers import generate_ph_data
from EmailHunter_get_email import PersonLookUpInfo


def data_formatter(dataset, error):
    """Format each dataset into a smaller one containing important information.

    It captures two kind of errors: no makers and empty list of makers.
    It returns the extracted information and an error report.
    """
    try:  # catch exceptions
        dataset['makers'] = {
            x['name']: x['headline'] for x in dataset['makers']}

        for maker in dataset['makers']:  # create a dataset per maker
            name = maker.rsplit()  # break down maker names
            # assign maker, maker lastname & track data completeness
            if len(name) == 2:
                dataset_edit = {
                    'maker': name[0],
                    'maker lastname': name[1],
                    'completeness': 'Full'}
            # when doubt assign maker & concatenate the rest in maker lastname
            elif len(name) > 2:
                dataset_edit = {
                    'maker': name[0],
                    'maker lastname': ' '.join(name[1:]),
                    'completeness': 'Check the name'}
            # when only one word set it in maker
            else:
                dataset_edit = {
                    'maker': ' '.join(name),
                    'maker lastname': None,
                    'completeness': 'Invalid name'
                    }
            # add important keys to the dataset
            dataset_edit['name'] = dataset['name']
            dataset_edit['url'] = dataset['url']
            dataset_edit['headline'] = dataset['makers'][maker]

    except KeyError as e:  # resolve no makers exception
        dataset_edit = {
            'maker': None,
            'maker lastname': None,
            'completeness': 'No name',
            'name': dataset['name'],
            'url': dataset['url'],
            'headline': None
            }
        error.setdefault(str(e), 0)  # create KeyError in error if not present
        error[str(e)] += 1

    finally:
        try:  # catch the empty makers list exception
            type(dataset_edit)
        except UnboundLocalError as e:  # resolve the empty makers list
            dataset_edit = {
                'maker': None,
                'maker lastname': None,
                'completeness': 'No name',
                'name': dataset['name'],
                'url': dataset['url'],
                'headline': None}
            error.setdefault(str(e), 0)  # create DictKey if not present
            error[str(e)] += 1

        return dataset_edit, error


def csv_writer(data, file_location, nb_of_posts):
    """Write the data into a file. Show the progression."""
    counter = 0  # counter to show the progress
    error = {}  # creating dictionary for error log (used in data_formatter())
    print('Creating csv file at the script root: ' + file_location,
          'with: \'w\' privileges')
    csvfile = open(file_location, 'w', newline='')
    fieldnames = ['name',  # fieldnames they match the one in data_formatter
                  'url',
                  'maker',
                  'maker lastname',
                  'email',
                  'headline',
                  'completeness']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)  # set the writer
    writer.writeheader()  # write the headers
    posts_without_makers = 0  # set variable to track posts without markers

    for dataset in data:  # loop though the data
        try:  # catch empty dataset error
            dataset is not None
            dataset = dataset[0]
        except UnboundLocalError:
            posts_without_makers += dataset[1]  # increment post without marker
        counter += 1  # increment the progress
        dataset_edit, error = data_formatter(dataset, error)  # format dataset

        person = {}  # get the email
        person["domain"] = dataset_edit["url"]
        person["first_name"] = dataset_edit["maker"]
        person["last_name"] = dataset_edit["maker lastname"]
        dataset_edit["email"] = PersonLookUpInfo.email

        writer.writerow(dataset_edit)

        sys.stdout.write(  # progress
            '\rProgress: {:.2f}%'.format((float(counter)/nb_of_posts)*100))

    error_count = 1
    for e in error:  # data_formatter error log
        print('\rERROR {}\n{}\nNumber of occurence: {}'
              .format(error_count, e, error[e]))
        error_count += 1

    print('\rERROR {}\nposts without makers\nNumber of occurence: {}'
          .format(error_count, posts_without_makers))  # no makers error
    csvfile.close()  # close the file


if __name__ == '__main__':
    data, topic_str, posts = generate_ph_data()

    cwd = os.getcwd()  # getting current working directory
    file_location = cwd + '/' + topic_str + '.csv'
    csv_writer(data, file_location, len(posts))  # write the data
