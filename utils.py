import requests

def make_request(url):
    """
    Takes in an input url and returns the data as a json object
    """
    response = requests.get(url)
    data = response.json()

    return data

