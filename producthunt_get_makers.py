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
# import time  # for sleep function
# import os  # to create output in the script directory
# import sys
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

    base_url = "https://api.producthunt.com/v1/"
    api_token = ""

    def __init__(self, params, logs, endpoint):
        """Initialize the class."""
        self.params = {"newer": 1,
                       "per_page": 50}
        self.logs = {}
        self.endpoint = ""
        self.full_url = generate_url()
        self.headers = populate_headers()

    def generate_url(self):
        """Build full url from base_url and endpoint."""
        try:
            self.base_url + self.endpoint
            return self
        except UnboundLocalError:
            raise ProductHuntErrors("No endpoint defined.")

    def populate_headers(self, api_token):
        """Add API token to the headers."""
        self.headers = {'Accept': "application/json",
                        'Content-Type': "application/json",
                        'Host': "api.producthunt.com"}
        self.headers["Authorization"] = "Bearer " + api_token
        return self

    def request(self):
        """Make a HTTP request with the class instance parameters."""
        req = requests.get(self.full_url,
                           self.params,
                           self.headers)  # request ProductHunt
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


def topic_id_finder(topic_request):
    """Need a topic name (string type) as an input.

    It'll look up this topic within the topic list of ProductHunt,
    interating through the pages until it finds it.
    It stops on two conditions: no more pages, topic found.
    """
    topic_request.topic_str = input(  # get a topic string
        'From which topic do you want to retrieve posts?    ')
    check = topic_request.params["newer"]  # initialize the loop exit marker

    try:
        topic_request.topics
    except UnboundLocalError:
        topic_request.topics = []
        topic_request.topic_id = 0
        topic_request.counter = 0

    topics = topic_request.request()

    topic_request.topics.extend(topics['topics'])  # add topics to the list
    max_id = max([topic['id'] for topic in topic_request.topics])
    topic_request.params["newer"] = max_id

    for topic in topics["topics"]:  # search loop to find the topic
        if topic["name"].lower() == topic_request.topic_str.lower():
            topic_id = topic["id"]
            break  # break the loop when topic_id is found

    # recursive loop which stops on two conditions: no more results, ID found
    if topic_id == 0:
        topic_request.counter += 1  # inform of the progress with a counter
        sys.stdout.write('\rNot in page {:3}'.format(topic_request.counter))

        return topic_id_finder(topic_request)

    elif topic_request.params["newer"] == check:  # no more results
        print('Topic not found, sorry.')

        return None  # return None as topic ID

    else:  # topic found
        pp = pprint.PrettyPrinter(indent=4)  # setting up pprint
        print()
        try:  # print the description of the topic, prevent charmap exceptions
            pp.pprint(topics['topic'])
        except UnicodeEncodeError:
            pass

        return topic_id


def get_posts(posts_request):
    """Fetch all the posts of a determined topic on ProductHunt.

    It paginates using the newer argument starting from the first post.
    It stops when the paginator can't be incremented anymore.
    It returns all the posts and the number of posts.
    """
    check = posts_request.params["newer"]  # initialize the loop exit marker

    try:
        posts_request.posts
    except UnboundLocalError:
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
        return posts_request.posts, len(posts_request.posts)


def data_with_makers_generator(posts_request):
    """Filter the posts based on maker_inside.

    If there is no maker the post is ignored and the error is counted.
    """
    extracted_data = {}

    for post in posts_request.posts:  # loop through the posts
        extracted_data['name'] = post['name']  # get company name
        extracted_data['url'] = url_extractor(post['redirect_url'])
        if post['maker_inside']:  # check for makers
            extracted_data['makers'] = post['makers']

            yield extracted_data, 0  # yield makers, 0 error

        else:

            yield extracted_data, 1  # yield None for no makers, 1 error


def url_extractor(redirect_url):
    """Extract final url from redirect url.

    ProductHunt only mention redirect_url in its post response.
    This function call the link and follow it until it finds the target URL.
    Finally it processes the target URL to extract the domain.
    """
    # set headers to a browser value
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) A\
    ppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    # find final url
    req = requests.get(redirect_url, headers=headers)

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
    """Write the data into a file. Show the progression.

    Work on a definite set of fieldnames. They must match with the one in
    data_formatter.
    """
    # counter to show the progress
    counter = 0
    # creating a dictionary for error log (used in data_formatter function)
    error = {}

    print('Creating csv file at the script root: ' + file_location,
          'with: \'w\' privileges')

    csvfile = open(file_location, 'w', newline='')

    # fieldnames they match the one in data_formatter
    fieldnames = ['name',
                  'url',
                  'maker',
                  'maker lastname',
                  'headline',
                  'completeness']

    # set the writer, write the headers
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # set variable to track posts without markers
    posts_without_makers = 0

    # loop though the data
    for dataset in data:
        # increment post without marker when it happens
        posts_without_makers += dataset[1]
        # catch empty dataset error
        try:
            dataset is not None
            dataset = dataset[0]
        except:
            pass
        # increment the progress
        counter += 1
        # format the dataset before writing it
        dataset_edit, error = data_formatter(dataset, error)
        writer.writerow(dataset_edit)
        # progress
        sys.stdout.write(
            '\rProgress: {:.2f}%'.format((float(counter)/nb_of_posts)*100)
            )
    # print the data_formatter error log
    error_count = 1
    for e in error:
        print('\rERROR {}\n{}\nNumber of occurence: {}'
              .format(error_count, e, error[e]))
        error_count += 1
    # print the no makers error
    print('\rERROR {}\nposts without makers\nNumber of occurence: {}'
          .format(error_count, posts_without_makers))
    # close the file
    csvfile.close()


if __name__ == '__main__':
    # prompting the API token for ProductHunt, looping until it works
    while True:
        ProductHunterAPI.api_token = "Bearer " + getpass.getpass(
            'Enter your ProductHunter API token: ')
        # testing endpoint
        test_request = ProductHunterAPI(endpoint='posts?newer=1')
        try:
            test_request.test()
            break  # exit the loop if successful
        except:
            print('Wrong token, please try again.')
    # get topic id from the topic string
    topic_request = ProductHunterAPI(endpoint='topics/?')
    # get the posts from topic filtered posts endpoint
    posts_request = ProductHunterAPI(
        endpoint='posts/all?search[topic]=' + str(topic_request.topic_id))
    posts = posts_request.json()

    data = data_with_makers_generator(posts)

    # setting up current working directory and csv file location
    cwd = os.getcwd()
    file_location = cwd + '/' + topic_request.topic_str + '.csv'

    nb_of_posts = len(posts_request.posts)

    csv_writer(data, file_location)
