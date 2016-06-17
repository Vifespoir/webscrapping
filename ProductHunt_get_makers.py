#!python3
"""This script will call ProductHunt API and gather information.

It'll collect Maker names and from a specific topic by looping through all the
posts of this topic.
"""

# importing libraries
import requests
import sys
import tldextract  # to extract main domain address
import pprint
import shelve
import shared_functions

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
        topic_request.topics = ProductHunterAPI.shelf_file['ph topics']
    except KeyError:
        topic_request.topic_id = 0
        topic_request.counter = 0
        topic_request.topics = {}

    for topic in topic_request.request()["topics"]:
        topic_request.topics[topic["name"].lower()] = topic

    max_id = max([topic["id"] for topic in topic_request.topics.values()])
    topic_request.params["newer"] = max_id

    ProductHunterAPI.shelf_file['ph topics'] = topic_request.topics

    if topic_request.topic_str in topic_request.topics.keys():
        topic_request.topic_id = \
            topic_request.topics[topic_request.topic_str]["id"]

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
            pp.pprint(topic_request.topics[topic_request.topic_str])
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
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=10)
    s.mount('http://', a)

    req = s.get(redirect_url, headers=headers)  # find final url
    try:  # capture URL Errors
        url_redirected = req.url
        extracted_url = tldextract.extract(url_redirected).registered_domain
    except ConnectionError:
        extracted_url = "ERROR"  # set the error as the extracted_url

    return extracted_url


def generate_ph_data():
    """Execute all the functions to generate preformatted data."""
    ProductHunterAPI.shelf_file = shelve.open('ProductHunter')

    api_token = shared_functions.get_api_token("ProductHunter")
    api_token = "Bearer " + api_token
    ProductHunterAPI.headers["Authorization"] = api_token

    shared_functions.check_api_token(ProductHunterAPI(endpoint='topics/?'))

    topic_request = ProductHunterAPI(endpoint='topics/?')
    topic_request.topic_str = input(  # get a topic string
        'From which topic do you want to retrieve posts?    ').lower()

    get_topics(topic_request)
    posts_request = ProductHunterAPI(  # get posts from specific topic endpoint
        endpoint='posts/all?search[topic]=' + str(topic_request.topic_id))
    get_posts(posts_request)
    # format the data for writing
    data = data_with_makers_generator(posts_request.posts)

    return data, topic_request.topic_str, posts_request.posts
