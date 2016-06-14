#!python3
"""This script will call ProductHunt API and gather information.

It'll collect Maker names and from a specific topic by looping through all the
posts of this topic.
"""

# importing libraries
import requests
import time  # for sleep function
import sys
import csv
import tldextract  # to extract main domain address
import pprint
import os  # to create output in the script directory
import getpass  # hide bearer token in the console

# TO DO: keep a list of topics and ids, plus the value of the newest topic to
# reduce API calls


class ProductHuntErrors(Exception):
    """Error class for this script."""

    def __init__(self, value):
        """Initialize the class."""
        self.value = value

    def __str__(self):
        """Return a string representation."""
        return repr(self.value)


class ProductHunterAPI:
    """docstring for ProductHunterAPI."""

    api_token = ""
    base_url = "https://api.producthunt.com/v1/"
    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Host': "api.producthunt.com"}

    def __init__(self, endpoint):
        """Initialize the class."""
        self.params = {"newer": 1,
                       "per_page": 50}
        self.endpoint = endpoint
        self.full_url = ProductHunterAPI.generate_url(self.endpoint)

    def generate_url(endpoint):
        """Build full url from base_url and endpoint."""
        try:
            return ProductHunterAPI.base_url + endpoint
        except UnboundLocalError:
            raise ProductHuntErrors("No endpoint defined.")

    def request(self):
        """Make a HTTP request with the class instance parameters."""
        req = requests.get(self.full_url,
                           params=self.params,
                           headers=self.headers)  # request ProductHunt
        req.raise_for_status()
        resp = req.json()
        time.sleep(0.2)  # sleep 0.2 second between two requests
        return resp

    def test(self):
        """Test the class."""
        try:
            self.request
        except:
            raise ProductHuntErrors("Test unsuccessful")


def get_topics(topic_request):
    """Look up a ProductHunt for a topic and return its id."""
    check = topic_request.params["newer"]  # initialize the loop exit marker

    try:
        topic_request.topics
    except AttributeError:
        topic_request.topics = []
        topic_request.topic_id = 0
        topic_request.counter = 0

    topics = topic_request.request()
    topic_request.topics.extend(topics['topics'])
    max_id = max([topic['id'] for topic in topic_request.topics])
    topic_request.params["newer"] = max_id

    for topic in topics["topics"]:  # search loop to find the topic
        if topic["name"].lower() == topic_request.topic_str.lower():
            topic_request.topic_id = topic["id"]
            break  # break the loop when topic_id is found

    # recursive loop which stops on two conditions: no more results, ID found
    if topic_request.topic_id == 0:
        topic_request.counter += 1  # inform of the progress with a counter
        sys.stdout.write('\rNot in page {:3}'.format(topic_request.counter))
        return get_topics(topic_request)

    elif topic_request.params["newer"] == check:  # no more results
        print('Topic not found, sorry.')
        return None  # return None as topic ID

    else:  # topic found
        pp = pprint.PrettyPrinter(indent=4)  # setting up pprint
        print()
        try:  # print the description of the topic, prevent charmap exceptions
            pp.pprint(topic)
        except UnicodeEncodeError:
            pass
        return topic_request.topic_id


def get_posts(posts_request):
    """Look up a topic and fetch all posts from this topic."""
    check = posts_request.params["newer"]  # initialize the loop exit marker

    try:
        posts_request.posts
    except AttributeError:
        posts_request.posts = []
        posts_request.counter = 0

    ph_posts = posts_request.request()  # get 50 posts
    posts_request.posts.extend(ph_posts['posts'])  # add them to the list
    max_id = max([post['id'] for post in posts_request.posts])
    posts_request.params["newer"] = max_id

    sys.stdout.write('\rposts: {}'.format(posts_request.counter))  # progress
    # recursively call the function, stop when no more results
    if posts_request.params["newer"] != check:
        posts_request.counter += len(ph_posts['posts'])  # count fetched posts
        return get_posts(posts_request)

    else:  # when no more results return the posts
        print('\nPost Fetching finished!')


def data_with_makers_generator(posts):
    """Filter the posts based on maker_inside, ignore post with no maker."""
    extracted_data = {}

    for post in posts:  # loop through the posts
        extracted_data['name'] = post['name']  # get company name
        extracted_data['url'] = url_extractor(post['redirect_url'])
        if post['maker_inside']:  # check for makers
            extracted_data['makers'] = post['makers']
            yield extracted_data, 0  # yield makers, 0 error

        else:
            yield extracted_data, 1  # yield None for no makers, 1 error


def url_extractor(redirect_url):
    """Extract final url from redirect url."""
    # set headers to a browser value
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) A\
    ppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    req = requests.get(redirect_url, headers=headers)  # find final url

    try:  # capture URL Errors
        url_redirected = req.url
        extracted_url = tldextract.extract(url_redirected).registered_domain
    except requests.error.HTTPError as e:
        extracted_url = e  # set the error as the extracted_url
    except requests.error.URLError as e:
        extracted_url = e  # set the error as the extracted_urlUn

    return extracted_url


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
    while True:  # prompting API token for ProductHunt, looping until it works
        api_token = "Bearer " + getpass.getpass(
            'Enter your ProductHunter API token: ')
        ProductHunterAPI.headers["Authorization"] = api_token
        test_request = ProductHunterAPI(endpoint='posts?newer=1')

        try:  # testing endpoint
            test_request.test()
            break  # exit the loop if successful
        except:
            print('Wrong token, please try again.')

    topic_request = ProductHunterAPI(endpoint='topics/?')
    topic_request.topic_str = input(  # get a topic string
        'From which topic do you want to retrieve posts?    ')
    get_topics(topic_request)
    posts_request = ProductHunterAPI(  # get posts from specific topic endpoint
        endpoint='posts/all?search[topic]=' + str(topic_request.topic_id))
    get_posts(posts_request)
    # format the data for writing
    data = data_with_makers_generator(posts_request.posts)
    cwd = os.getcwd()  # getting current working directory
    file_location = cwd + '/' + topic_request.topic_str + '.csv'
    csv_writer(data, file_location, len(posts_request.posts))  # write the data
