import requests
import random
import datetime

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
    VoteSession,
    Contest,
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
    cards = r.get('/api/cards/', params={'page_size': 1}).json()
    left_id = random.randint(1, cards['count'])
    right_id = random.randint(1, cards['count'])
    while (left_id == right_id):
        right_id = random.randint(1, cards['count'])
    return get_cards(left_id, right_id)

@view_config(route_name='vote')
def vote_view(request):
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    session = request.session
    if ('left' or 'right' in request.params) and 'id' in session:
        token = session.get_csrf_token()
        if token != request.POST['csrf_token']:
            return HTTPFound(location=settings['url_prefix'])
        with transaction.manager:
            vote = DBSession.query(VoteSession).filter_by(id=session['id']).first()
            if not vote:
                return HTTPFound(location=settings['url_prefix'])
            card_id = vote.left_id if 'left' in request.params else vote.right_id
            name = vote.left_name if 'left' in request.params else vote.right_name
            rarity = vote.left_rarity if 'left' in request.params else vote.right_rarity
            idolized = vote.left_idolized if 'left' in request.params else vote.right_idolized
            id_contest = vote.contest
            DBSession.delete(vote)
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
    session.invalidate()
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

def pick_two_random_cards_query(params):
    r = ApiRequest()
    cards = r.get('/api/cardids/' + params).json()
    left_id = random.choice(cards)
    right_id = random.choice(cards)
    while (left_id == right_id):
        right_id = random.choise(cards)
    return get_cards(left_id, right_id)

def vote_page_view(request, contest=None):
    session = request.session
    now = datetime.datetime.now()
    #contest = DBSession.query(Contest).filter(now <= Contest.end, now >= Contest.begin).first()
    if contest:
        cards = pick_two_random_cards_query(contest.params)
    else:
        cards = pick_two_random_cards()
    with transaction.manager:
        model = VoteSession(left_id = cards['left']['id'],
                            right_id = cards['right']['id'],
                            left_name = cards['left']['name'],
                            right_name = cards['right']['name'],
                            left_rarity = cards['left']['rarity'],
                            right_rarity = cards['right']['rarity'],
                            left_idolized = cards['idolized_left'],
                            right_idolized = cards['idolized_right'],
                            created = now,
                            contest = contest.id if contest else 0)
        DBSession.add(model)
        DBSession.flush()
        session['id'] = model.id
    token = session.new_csrf_token()
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return cards, settings, token

@view_config(route_name='home', renderer='templates/home.jinja2')
def main_vote_view(request):
   cards, settings, token = vote_page_view(request)
   return {
        'cards': cards,
        'url_prefix': settings['url_prefix'],
        'csrf_token': token,
    }

@view_config(route_name='contest', renderer='templates/home.jinja2')
def contest_vote_view(request):
    contest = DBSession.query(Contest).filter(now <= Contest.end, now >= Contest.begin).first()
    cards, settings, token = vote_page_view(request, contest=contest)
    return {
        'cards': cards,
        'url_prefix': settings['url_prefix'],
        'csrf_token': token,
    }
