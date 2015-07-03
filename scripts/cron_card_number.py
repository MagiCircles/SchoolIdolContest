import requests

API_URL = 'http://schoolido.lu/api/'

FILEPATH = '/tmp/contest_cards_count'

cards = requests.get(API_URL + 'cards/', params={'page_size': 1}).json()
with open(FILEPATH, 'wr') as f:
    f.write(str(cards['count']))
