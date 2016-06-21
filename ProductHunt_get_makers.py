#!python3
"""This script will call ProductHunt API and gather information.

It'll collect Maker names and from a specific topic by looping through all the
posts of this topic.
"""

# importing libraries
import requests
import pprint
import shelve
import shared_functions
import logging

# TO DO: keep a list of topics and ids, plus the value of the newest topic to
# reduce API calls
logging.basicConfig(
    level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')


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
    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Host': "api.producthunt.com"}

    def __init__(self, endpoint):
        """Initialize the class."""
        logging.debug('Initialized ProductHunterAPI, endpoint: "%s"'% endpoint)
        self.get_api_token()
        self.params = {"newer": 1,
                       "per_page": 50}
        self.endpoint = endpoint
        self.full_url = ProductHunterAPI.generate_url(self.endpoint)

    def get_api_token(self):
        """Obtain the API token and test if it works."""
        while True:
            try:
                self.api_key
                ProductHunterAPI.headers["Authorization"] =\
                    "Bearer " + self.api_key
                self.test()
                break
            except:
                ProductHunterAPI.api_key =\
                    shared_functions.get_api_token("ProductHunter")
        logging.info(
            'ProductHunterAPI.get_api_token: %s' % 'correct API token')

    def generate_url(endpoint):
        """Build full url from base_url and endpoint."""
        try:
            full_url = ProductHunterAPI.base_url + endpoint
            logging.debug('ProductHunterAPI.generate_url %s' % full_url)
            return full_url
        except UnboundLocalError:
            raise ProductHuntErrors("No endpoint defined.")

    def request(self):
        """Make a HTTP request with the class instance parameters."""
        req = requests.get(self.full_url,
                           params=self.params,
                           headers=self.headers)  # request ProductHunt
        try:
            req.raise_for_status()
        except:
            logging.debug('request {} \nParams: {} \nHeaders: {}'.format(
                self.full_url, self.params, self.headers))

        logging.debug('ProductHunterAPI.request %s' % req.url)
        return req

    def test(self):
        """Test the class."""
        try:
            self.request
        except:
            raise ProductHuntErrors("Test unsuccessful")

    def set_newer_to_max_id(self, ClassVariable):
        assert isinstance(ClassVariable, dict) is True, 'Dictionary expected'
        try:
            max_id = max([ClassVariable[item]['id'] for item in ClassVariable])
        except KeyError:
            max_id = 1
        self.params["newer"] = max_id

    def set_logs(self, logs):
        logging.debug('get_topics %s' %
            'Checking for "' + logs.name + '" in logs')
        assert isinstance(logs.data, dict) is True, 'Logs must be a dictionary'
        logs.counter = 0

        try:  # get only posts newer than the one in the logs
            self.set_newer_to_max_id(logs.data)
        except ValueError:
            pass

        logs.newer = self.params["newer"]  # loop exit marker


class ProductHunterLogs():
    """docstring for ProductHunterLog."""
    shelf_file = shelve.open('ProductHunter')

    def __init__(self, name):
        logging.debug(
            'Initialized ProductHunterLogs, log name: %s' % name)
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


def search_topic(data, search_log, topic_str):
    topic_id = 0
    if isinstance(data, ProductHunterLogs):
        data, dataname = data.data, data.name
    else:
        dataname = 'topic request'
    for topic in data:
        if topic == topic_str:
            search_log.data[topic_str] = data[topic]['id']
            topic_id = search_log.data[topic_str]
            logging.debug('search_topic topic found in "%s"' % dataname)
            break

    return topic_id


def get_topics(query):
    """Look up a ProductHunt for a topic and return its id."""
    topicsLogs = ProductHunterLogs('topics')
    query.set_logs(topicsLogs)
    topic_str, topics = query.topic_str, topicsLogs.data
    topicsIDs = ProductHunterLogs('searches')

    query.topic_id = search_topic(topicsIDs, topicsIDs, topic_str)
    query.topic_id = search_topic(topicsLogs, topicsIDs, topic_str)
    topicsIDs.store_logs(topics)

    # recursive loop which stops on two conditions: no more results, ID found
    if query.topic_id == 0:
        topicsLogs.counter += 1  # inform of progress with a counter
        logging.debug('get_topics %s' %
            'Checking in page: ' + str(topicsLogs.counter))

        topics = {i['name'].lower():i for i in query.request().json()['topics']}
        query.topic_id = search_topic(topics, topicsLogs, topic_str)
        query.set_newer_to_max_id(topics)
        topicsLogs.store_logs(topics)
        topicsIDs.store_logs(topics)

        return get_topics(query)

    elif query.params["newer"] == topicsLogs.newer and not query.topic_id:
        logging.info('get_topics Topic not found, sorry...')
        return None  # return None as topic ID

    else:  # topic found
        query.topic_id
        assert isinstance(query.topic_id, int) is True, 'id: %s'%query.topic_id
        logging.info('get_topics topic found: \n%s' % pprint.pformat(
            topics[topic_str], indent=4))


def get_posts(query):
    """Look up a topic and fetch all posts from this topic."""
    logging.debug('get_posts Checking for posts in logs')
    postsLogs = ProductHunterLogs('posts')
    query.set_logs(postsLogs)

    for post in query.request().json()['posts']:
        postsLogs.data[post['id']] = skim_post(post)

    postsLogs.store_logs(postsLogs.data)
    query.set_newer_to_max_id(postsLogs.data)

    # recursively call the function, stop when no more results
    if query.params['newer'] != postsLogs.newer:
        postsLogs.counter += len(postsLogs.data)  # posts nb
        logging.debug('get_posts: %s posts fetched' % postsLogs.counter)
        return get_posts(query)

    else:  # when no more results return the posts
        postsLogs.counter = len(postsLogs.data)
        logging.info('get_posts total posts fetched: %s' % postsLogs.counter)
        return postsLogs

# change URL in logs!!!
# extract_makers output incorrect need to nest dicts
def extract_makers(posts):
    """Filter the posts based on maker_inside, ignore post with no maker."""
    logging.debug('extract_makers Start')
    makersLogs = ProductHunterLogs('makers')
    cntr = [0, 0, len(posts.data)]

    for post in posts.data:  # loop through the posts
        logging.info(
            'extract_makers progress: {:.0%}, makers {:.0%}'\
                .format(cntr[0]/cntr[2], cntr[1]/cntr[2]))
        posts.data[post].setdefault('maker_inside', False)
        if posts.data[post]['maker_inside']:  # check for makers
            for maker in posts.data[post]['makers']:
                mkrKey = maker['name'] + str(posts.data[post]['id'])
                makersLogs.data[mkrKey] = maker
                makersLogs.data[mkrKey]['company'] = posts.data[post]['name']
                if not 'url' in posts.data[post].keys():
                    makersLogs.data[mkrKey]['url'] = shared_functions.\
                        url_extractor(posts.data[post]['redirect_url'])
                    posts.data[post]['url'] = makersLogs.data[mkrKey]['url']
                else:
                    makersLogs.data[mkrKey]['url'] = posts.data[post]['url']
            cntr[1] += 1
        cntr[0] += 1
    posts.store_logs(posts.data)
    makersLogs.store_logs(makersLogs.data)

    return makersLogs


def skim_post(post):
    """Skim the information contained in the post response."""
    post_pops = ['screenshot_url', 'thumbnail', 'user', 'discussion_url',
                 'votes_count', 'exclusive', 'category_id',
                 'current_user', 'comments_count', 'created_at',
                 'product_state', 'featured', 'platforms', 'tagline']
    maker_pops = ['image_url', 'created_at', 'username', 'profile_url']

    for post_pop in post_pops:
        try:
            post.pop(post_pop)
        except AttributeError as e:
            logging.warning('skim_posts, error: %s' % e, post)
    for maker in post['makers']:
        for maker_pop in maker_pops:
            maker.pop(maker_pop)

    return post


def generate_ph_data():
    """Execute all the functions to generate preformatted data."""
    topic_request = ProductHunterAPI(endpoint='topics/?')
    topic_request.topic_str = input(  # get a topic string
        'From which topic do you want to retrieve posts?    ').lower()
    get_topics(topic_request)
    posts_request = ProductHunterAPI(  # get posts from specific topic endpoint
        endpoint='posts/all?search[topic]=' + str(topic_request.topic_id))
    raw_posts = get_posts(posts_request)
    # format the data for writing
    data = extract_makers(raw_posts)

    return data, topic_request.topic_str

if __name__ == '__main__':
    logging.info('RESULTS: \n%s' % pprint.pformat(
        generate_ph_data()[0].data, indent=4))
