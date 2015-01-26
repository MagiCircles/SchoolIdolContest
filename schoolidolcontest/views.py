import requests
import random

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import pyramid.threadlocal

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func
import transaction

from .models import (
    DBSession,
    Vote,
    )

class ApiRequest(object):
    def __init__(self):
        registry = pyramid.threadlocal.get_current_registry()
        settings = registry.settings
        self.api_url = settings['api_url']
        self.session = requests.Session()

    def get(self, path, *args, **kwargs):
        return self.session.get(self.api_url + path, **kwargs)

def get_cards(left_id, right_id):
    ret = dict()
    r = ApiRequest()
    ret['left'] = r.get('/api/cards/' + str(left_id) + '/').json()
    ret['right'] = r.get('/api/cards/' + str(right_id) + '/').json()
    ret['idolized_left'] = random.choice([True, False])
    ret['idolized_right'] = random.choice([True, False])
    return ret

def filter_two_random_cards(*args, **kwargs):
    r = ApiRequest()
    cards = r.get('/api/cardids', *args, **kwargs).json()
    left_id = random.choice(cards)
    right_id = random.choice(cards)
    while (left_id == right_id):
        right_id = random.choice(cards)
    et['idolized_right'] = random.choice([True, False])
    return get_cards(left_id, right_id)

def pick_two_random_cards():
    r = ApiRequest()
    cards = r.get('/api/cards', params={'page_size': 1}).json()
    left_id = random.randint(1, cards['count'])
    right_id = random.randint(1, cards['count'])
    while (left_id == right_id):
        right_id = random.randint(1, cards['count'])
    return get_cards(left_id, right_id)

@view_config(route_name='home', renderer='templates/home.jinja2')
def my_view(request):
    session = request.session
    cards = pick_two_random_cards()
    session['left'] = cards['left']
    session['right'] = cards['right']
    session['idolized_left'] = cards['idolized_left']
    session['idolized_right'] = cards['idolized_right']
    return cards

@view_config(route_name='vote')
def vote_view(request):
    session = request.session
    if ('left' or 'right' in request.params) and ('left' or 'right' in session):
        card = session['left'] if 'left' in request.params else session['right']
        idolized = session['idolized_left'] if 'left' in request.params else session['idolized_right']
        card_id = card['id']
        name = card['name']
        rarity = card['rarity']
        id_contest = 0
        ip = request.remote_addr
        try:
            model = Vote(id_card=card_id, ip=ip, id_contest=id_contest,
                         name=name, rarity=rarity, idolized=idolized)
            DBSession.add(model)
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain',
                            status_int=500)
    return HTTPFound(location='/')

def count_one_by_field(name):
    r = ApiRequest()
    req = DBSession.query(Vote,
                          func.count(name).label('total')).group_by(name).order_by('total DESC').all()
    l = [(i._asdict()['Vote'].idolized, r.get('/api/cards/' +
                                              str(i._asdict()['Vote'].id_card) +
                                              '/').json()) for i in req[:10]]
    return l

@view_config(route_name='bestgirl', renderer='templates/bestgirl.jinja2')
def best_girl_view(request):
    list_card = count_one_by_field('id_card')
    list_girl = count_one_by_field('name')
    return {'list_card': list_card ,
            'list_girl': list_girl,}


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_SchoolIdolContest_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

