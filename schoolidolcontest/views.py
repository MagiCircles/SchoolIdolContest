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
    ret['left'] = r.get('/api/cards/' + str(left_id) + '/?imagedefault=True').json()
    ret['right'] = r.get('/api/cards/' + str(right_id) + '/?imagedefault=True').json()
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
    return get_cards(left_id, right_id)

def pick_two_random_cards():
    r = ApiRequest()
    cards = r.get('/api/cards', params={'page_size': 1}).json()
    left_id = random.randint(1, cards['count'])
    right_id = random.randint(1, cards['count'])
    while (left_id == right_id):
        right_id = random.randint(1, cards['count'])
    return get_cards(left_id, right_id)

def reduce_card(card):
    new = dict()
    new['id'] = card['id']
    new['name'] = card['name']
    new['rarity'] = card['rarity']
    return new

@view_config(route_name='home', renderer='templates/home.jinja2')
def my_view(request):
    session = request.session
    cards = pick_two_random_cards()
    session['left'] = reduce_card(cards['left'])
    session['right'] = reduce_card(cards['right'])
    session['idolized_left'] = cards['idolized_left']
    session['idolized_right'] = cards['idolized_right']
    token = session.new_csrf_token()
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return {
        'cards': cards,
        'url_prefix': settings['url_prefix'],
        'csrf_token': token,
    }

@view_config(route_name='vote')
def vote_view(request):
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    session = request.session
    if ('left' or 'right' in request.params) and ('left' or 'right' in session):
        token = session.get_csrf_token()
        if token != request.POST['csrf_token']:
            return HTTPFound(location=settings['url_prefix'])
        card = session['left'] if 'left' in request.params else session['right']
        idolized = session['idolized_left'] if 'left' in request.params else session['idolized_right']
        session.invalidate()
        card_id = card['id']
        name = card['name']
        rarity = card['rarity']
        id_contest = 0
        try:
            req = DBSession.query(Vote).filter_by(id_card=card_id,
                                               id_contest=id_contest,
                                               idolized=idolized).first()
            if not req:
                model = Vote(id_card=card_id, id_contest=id_contest,
                            name=name, counter=1, rarity=rarity, idolized=idolized)
                DBSession.add(model)
            else:
                req.counter += 1
                DBSession.add(req)
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain',
                            status_int=500)
    return HTTPFound(location=settings['url_prefix'])

def count_by_name():
    r = ApiRequest()
    req = DBSession.query(Vote,
                          func.sum(Vote.counter).label('counter_all')).group_by(Vote.name).order_by('counter_all DESC').all()
    l = [(i.idolized, r.get('/api/cards/' + str(i.id_card) +
                            '/?imagedefault=True').json(), c) for (i, c) in req[:10]]
    return l

def count_by_id():
    r = ApiRequest()
    req = DBSession.query(Vote).order_by('counter DESC').all()
    l = [(i.idolized, r.get('/api/cards/' + str(i.id_card) +
                            '/?imagedefault=True').json(), i.counter) for i in req[:10]]
    return l

@view_config(route_name='bestgirl', renderer='templates/bestgirl.jinja2')
def best_girl_view(request):
    list_card = count_by_id()
    list_girl = count_by_name()
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return {
        'list_card': enumerate(list_card),
        'list_girl': enumerate(list_girl),
        'url_prefix': settings['url_prefix'],
    }


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
