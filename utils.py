import requests

def make_request(url):
    response = requests.get(url)
    data = response.json()


    

    return data

