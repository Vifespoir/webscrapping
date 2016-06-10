#!python3

#importing libraries
import urllib.request, urllib.parse
import time
import os
import sys
import csv
import tldextract
import pprint
import json


def topic_id_finder(topic_str,
                    endpoint='topics/?',
                    topics=[],
                    topic_id=0,
                    paginator='&newer=1',
                    counter=0):
    '''
    This function need a topic name (string type) as an input.
    It'll look up this topic within the topic list of ProductHunt,
    interating through the pages until it finds it.
    It stops on two conditions: no more pages, topic found.
    '''
    check = paginator #initialize the loop exit marker
    ph_topics = ph_iterator(
                ph_base_url = ph_base_url,
                endpoint = endpoint,
                paginator=paginator
                )

    topics.extend(ph_topics['topics']) #add topics to the list
    max_id = max([topic['id'] for topic in topics]) #max_id from topic ids list
    paginator = '&newer=' + str(max_id)

    for topic in ph_topics["topics"]: #search loop to find the topic
        if topic["name"].lower() == topic_str.lower():
            topic_id = topic["id"]
            break #break the loop when topic_id is found

    #recursive loop which stops on two conditions: no more results, ID found
    if topic_id == 0:
        counter += 1 #inform of the progress with a counter
        sys.stdout.write('\rNot in page {:3}'.format(counter))

        return topic_id_finder(
            topic_str = topic_str,
            endpoint = endpoint,
            topics = topics,
            topic_id = topic_id,
            paginator = paginator,
            counter = counter
            )

    elif paginator == check: #no more results
        print('Topic not found, sorry.')

        return None #return None as topic ID

    else: #topic found
        pp = pprint.PrettyPrinter(indent=4) #setting up pprint
        #print the description of the topic
        print()
        try:
            pp.pprint(ph_iterator(ph_base_url, 'topics/' + str(topic_id))['topic'])
        except UnicodeEncodeError:
            pass

        return topic_id


def ph_iterator(ph_base_url, endpoint, paginator='', per_page = '&per_page=50'):
    '''
    This function format a ProductHunt URL for an API call with or without
    pagination.
    It sends a request to the URL and get the response.
    It opens, reads and convert to a json file the response.
    Finally it returns the response.
    '''
    #paginate the url with the highest topic id from previous page
    paginated_url = ph_base_url + endpoint + str(paginator) + per_page

    try: #catch malformated URLs
        req = urllib.request.Request(
                        paginated_url,
                        headers = ph_headers
                        ) #request ProductHunt

        open_req = urllib.request.urlopen(req).read().decode('utf-8')
        resp = json.loads(open_req)
    except:
        print(paginated_url, '\n', '\n'.join([k + ': ' + v for k, v in ph_headers.items()]))

    time.sleep(0.2) #sleep 0.2 second between two requests

    return resp


def get_posts(endpoint, posts=[], paginator='&newer=1', counter=0):
    '''
    This function fetch all the posts of a determined topic on ProductHunt.
    It paginates using the newer argument starting from the first post.
    It stops when the paginator can't be incremented anymore.
    It returns all the posts and the number of posts.
    '''
    check = paginator

    ph_posts = ph_iterator(
                    ph_base_url,
                    endpoint,
                    paginator
                    ) #get 50 posts

    posts.extend(ph_posts['posts']) #add them to the list
    max_id = max([post['id'] for post in posts]) #get max_id from posts list
    paginator = '&newer=' + str(max_id)

    sys.stdout.write('\rposts: {}'.format(counter)) #progress bar
    #recursively call the function, stop when no more results
    if paginator != check:
        counter += len(ph_posts['posts']) #count the number of posts fetched

        return get_posts(
            endpoint = endpoint,
            posts = posts,
            paginator = paginator,
            counter = counter)

    else: #when no more results return the posts
        print('\nPost Fetching finished!')
        return posts, len(posts)


def data_with_makers_generator(posts, extracted_data = {}):
    '''
    This function filter the posts based on maker_inside.
    If there is no maker the post is ignored and the error is counted.
    '''
    for post in posts: #loop through the posts
        extracted_data['name'] = post['name'] #get company name
        extracted_data['url'] = url_extractor(post['redirect_url']) #extract URL
        if post['maker_inside']: #check for makers
            extracted_data['makers'] = post['makers']

            yield extracted_data, 0 #yield makers, 0 error

        else:

            yield extracted_data, 1 #yield None for no makers, 1 error


def url_extractor(redirect_url):
    '''ProductHunt only mention redirect_url in its post response.
    This function call the link and follow it until it finds the target URL.
    Finally it processes the target URL to extract the domain.'''

    #set headers to a browser value
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4)\
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    #find final url
    req = urllib.request.Request(redirect_url, headers = headers)

    try: #capture URL Errors
        resp = urllib.request.urlopen(req)
        url_redirected = resp.geturl()
        extracted_url = tldextract.extract(url_redirected).registered_domain
    except urllib.error.HTTPError as e:
        extracted_url = e #set the error as the extracted_url
    except urllib.error.URLError as e:
        extracted_url = e #set the error as the extracted_urlUn

    return extracted_url


def data_formatter(dataset, error):
    '''This function format each dataset into a smaller one containing only
    important information.
    It captures two kind of errors: no makers and empty list of makers.
    It returns the extracted information and an error report.'''

    try: #catch exceptions
        dataset['makers'] = {x['name']:x['headline'] for x in dataset['makers']}

        for maker in dataset['makers']: #create a dataset per maker
            name = maker.rsplit() #break down maker names
            #assign maker, maker lastname & track data completeness
            if len(name) == 2:
                dataset_edit = {
                    'maker': name[0],
                    'maker lastname': name[1],
                    'completeness': 'Full'
                    }
            #when doubt assign maker and concatenate the rest in maker lastname
            elif len(name) > 2:
                dataset_edit = {
                    'maker': name[0],
                    'maker lastname': ' '.join(name[1:]),
                    'completeness': 'Check the name'
                    }
            #when only one word set it in maker
            else:
                dataset_edit = {
                    'maker': ' '.join(name),
                    'maker lastname': None,
                    'completeness': 'Invalid name'
                    }
            #add important keys to the dataset
            dataset_edit['name'] = dataset['name']
            dataset_edit['url'] = dataset['url']
            dataset_edit['headline'] = dataset['makers'][maker]

    except KeyError as e: #resolve no makers exception
        dataset_edit = {
            'maker': None,
            'maker lastname': None,
            'completeness': 'No name',
            'name': dataset['name'],
            'url': dataset['url'],
            'headline': None
            }
        error.setdefault(str(e), 0) #create KeyError in error if not present
        error[str(e)] += 1

    finally:
        try: #catch the empty makers list exception
            type(dataset_edit)
        except UnboundLocalError as e: #resolve the empty makers list
            dataset_edit = {
                'maker': None,
                'maker lastname': None,
                'completeness': 'No name',
                'name': dataset['name'],
                'url': dataset['url'],
                'headline': None
                }
            error.setdefault(str(e), 0) #create KeyError in error if not present
            error[str(e)] += 1

        return dataset_edit, error


def csv_writer(data, file_location):
    '''
    Write the data into a file. Show the progression.
    Work on a definite set of fieldnames. They must match with the one in
    data_formatter.
    '''
    #counter to show the progress
    counter = 0
    #creating a dictionary for error log (used in data_formatter function)
    error = {}

    print('Creating csv file at the script root: ' + file_location,
        'with: \'w\' privileges')

    csvfile = open(file_location, 'w', newline='')

    #fieldnames they match the one in data_formatter
    fieldnames = ['name',
                  'url',
                  'maker',
                  'maker lastname',
                  'headline',
                  'completeness']

    #set the writer, write the headers
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    #set variable to track posts without markers
    posts_without_makers = 0

    #loop though the data
    for dataset in data:
        #increment post without marker when it happens
        posts_without_makers += dataset[1]
        #catch empty dataset error
        try:
            dataset is not None
            dataset = dataset[0]
        except:
            pass
        #increment the progress
        counter += 1
        #format the dataset before writing it
        dataset_edit, error = data_formatter(dataset, error)
        writer.writerow(dataset_edit)
        #progress
        sys.stdout.write(
            '\rProgress: {:.2f}%'.format((float(counter)/nb_of_posts)*100)
            )
    #print the data_formatter error log
    error_count = 1
    for e in error:
        print('\rERROR {}\n{}\nNumber of occurence: {}'\
                                .format(error_count, e, error[e]))
        error_count += 1
    #print the no makers error
    print('\rERROR {}\nposts without makers\nNumber of occurence: {}'\
                                .format(error_count, posts_without_makers))
    #close the file
    csvfile.close()

if __name__ == '__main__':
    #setting up API calls
    ph_base_url = "https://api.producthunt.com/v1/"
    ph_headers = {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Host': "api.producthunt.com"
        }
    #prompting the API token for ProductHunt, looping until it works
    while True:
        ph_token = input('Enter your ProductHunter API token: ')
        #adding bearer as requested in ProductHunt API doc
        ph_headers['Authorization'] = "Bearer " + ph_token
        #testing endpoint
        endpoint = 'posts?newer=1'
        try:
            #sending a request to ProductHunt
            ph_iterator(ph_base_url, endpoint, per_page = '&per_page=1')
            #exit the loop if successful
            break
        except:
            print('Wrong token, please try again.')

    #get a topic string
    topic_str = input('From which topic do you want to retrieve posts?    ')
    #get topic id from the topic string
    topic_id = topic_id_finder(topic_str)
    ###get the posts from topic filtered posts endpoint
    endpoint = 'posts/all?search[topic]=' + str(topic_id)
    posts = get_posts(endpoint)[0]
    nb_of_posts = len(posts)

    data = data_with_makers_generator(posts)

    #setting up current working directory and csv file location
    cwd = os.getcwd()
    file_location = cwd + '/' + topic_str + '.csv'

    csv_writer(data, file_location)
