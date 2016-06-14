import getpass  # hide bearer token in the console


def get_api_token(text):
    """Get API token."""
    api_token = getpass.getpass('Enter ' + text + ' API token: ')

    return api_token


def check_api_token(test_function):
    """Check API token."""
    while True:  # prompting API token for ProductHunt, looping until it works
        test_request = test_function(kwargs)

        try:  # testing endpoint
            test_request.test()
            break  # exit the loop if successful
        except:
            return get_api_token('a valid')

    print("Correct API token.")
