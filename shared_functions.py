import getpass  # hide bearer token in the console


def get_api_token(text):
    """Get API token."""
    if text == "EmailHunter":
        return "f92e50737d8056c27c09596d4b2d8bcf579aa9c6"
    elif text == "ProductHunter":
        return "30dfd116f2ed23fc691f264fd8d09d1714b8395ffc6a42d319095f9b367c19a5"
    else:
        api_token = getpass.getpass('Enter ' + text + ' API token: ')
        return api_token


def check_api_token(test_function):
    """Check API token."""
    while True:  # prompting API token for ProductHunt, looping until it works
        test_request = test_function

        try:  # testing endpoint
            test_request.test()
            break  # exit the loop if successful
        except:
            return get_api_token('a valid')

    print("Correct API token.")
