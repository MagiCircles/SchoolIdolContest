import requests
import random
import datetime

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
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

# Helpers

class ApiRequest(object):
    def __init__(self):
        registry = pyramid.threadlocal.get_current_registry()
        settings = registry.settings
        self.api_url = settings['api_url']
        self.session = requests.Session()

    def get(self, path, *args, **kwargs):
        return self.session.get(self.api_url + path, **kwargs)

def get_current_contest():
    now = datetime.datetime.now()
    contest = DBSession.query(Contest).filter(now <= Contest.end, now >= Contest.begin).first()
    return contest

def is_current_contest(contest):
    now = datetime.date.today()
    return now <= contest.end and now >= contest.begin

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

def pick_two_random_cards_query(params):
    r = ApiRequest()
    cards = r.get('/api/cardids/' + params).json()
    left_id = random.choice(cards)
    right_id = random.choice(cards)
    while (left_id == right_id):
        right_id = random.choice(cards)
    return get_cards(left_id, right_id)

def best_girl_query(contest):
    req = DBSession.query(Vote,func.sum(Vote.counter).label('counter_all')).filter(Vote.id_contest == contest).group_by(Vote.name).order_by('counter_all DESC')
    return req

def best_card_query(contest):
    req = DBSession.query(Vote).filter(Vote.id_contest == contest).order_by('counter DESC')
    return req

def count_by_name(contest=0):
    r = ApiRequest()
    req = best_girl_query(contest).all()
    l = [(i.idolized, r.get('/api/cards/' + str(i.id_card) +
                            '/?imagedefault=True').json(), c) for (i, c) in req[:10]]
    return l

def count_by_id(contest=0):
    r = ApiRequest()
    req = best_card_query(contest).all()
    l = [(i.idolized, r.get('/api/cards/' + str(i.id_card) +
                            '/?imagedefault=True').json(), i.counter) for i in req[:10]]
    return l

def count_contest_votes(contest):
    count = DBSession.query(func.sum(Vote.counter)).filter(Vote.id_contest == contest).first()
    return count[0]

def get_winner_cards(contest):
    r = ApiRequest()
    result_kinds = contest.result_type.split()
    best_card, best_girl = None, None
    for result in result_kinds:
        if result == 'best_girl':
            best_girl_vote = best_girl_query(contest.id).first()[0]
            best_girl = r.get('/api/cards/' + str(best_girl_vote.id_card) + '/?imagedefault=True').json()
        elif result == 'best_card':
            best_card_vote = best_card_query(contest.id).first()
            best_card = r.get('/api/cards/' + str(best_card_vote.id_card) + '/?imagedefault=True').json()
    return best_card, best_girl

# Functions related to views themselves

@view_config(route_name='vote')
def vote_view(request):
    """
    Route validating a vote
    """
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    session = request.session
    forward = settings['url_prefix']
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
            if id_contest != 0:
                forward = forward + 'contest'
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
    return HTTPFound(location=forward)

@view_config(route_name='bestgirl', renderer='templates/bestgirl.jinja2')
def best_girl_view(request):
    """
    The Best Girl page
    """
    list_card = count_by_id()
    list_girl = count_by_name()
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    current_contest = get_current_contest()
    return {
        'current_contest': current_contest,
        'list_card': enumerate(list_card),
        'list_girl': enumerate(list_girl),
        'url_prefix': settings['url_prefix'],
    }

@view_config(route_name='result', renderer='templates/bestgirl.jinja2')
def contest_result_view(request):
    """
    The contest result
    """
    di = request.matchdict
    id = di.get("id", None)
    if id and id.isdigit():
        id = int(id)
    contest = DBSession.query(Contest).filter(Contest.id == id).first()
    columns = contest.result_type.split()
    list_girl, list_card = None, None
    for col in columns:
        if col == 'best_girl':
            list_girl = enumerate(count_by_name(contest.id))
        elif col == 'best_card':
            list_card = enumerate(count_by_id(contest.id))
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    is_current = is_current_contest(contest)
    delta = datetime.datetime.combine(contest.end, datetime.datetime.min.time()) - datetime.datetime.now() if is_current else None
    current_contest = contest if is_current else get_current_contest()
    return {
        'contest': contest,
        'is_current': is_current,
        'current_contest': current_contest,
        'title': contest.name,
        'begin': contest.begin,
        'end': contest.end,
        'delta': delta,
        'list_card': list_card,
        'list_girl': list_girl,
        'url_prefix': settings['url_prefix'],
    }

def vote_page_view(request, contest=None):
    """
    Function used to get informations used to generate voting pages
    """
    session = request.session
    now = datetime.datetime.now()
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
    """
    The main page, random voting on the whole collection
    """
    cards, settings, token = vote_page_view(request)
    current_contest = get_current_contest()
    title = 'Which card is better?'
    return {
        'current_contest': current_contest,
        'title': title,
        'cards': cards,
        'url_prefix': settings['url_prefix'],
        'csrf_token': token,
    }

@view_config(route_name='contest', renderer='templates/home.jinja2')
def contest_vote_view(request):
    """
    The contest voting page: vote for the current contest
    """
    now = datetime.datetime.now()
    contest = get_current_contest()
    if not contest:
        raise pyramid.exceptions.NotFound
    cards, settings, token = vote_page_view(request, contest=contest)
    delta = datetime.datetime.combine(contest.end, datetime.datetime.min.time()) - datetime.datetime.now()
    return {
        'contest': contest,
        'current_contest': contest,
        'title': contest.name,
        'cards': cards,
        'begin': contest.begin,
        'end': contest.end,
        'delta': delta,
        'url_prefix': settings['url_prefix'],
        'csrf_token': token,
    }


@view_config(route_name='results', renderer='templates/contests_listing.jinja2')
def list_results_view(request):
    """
    List the old contests results
    """
    current_contest = get_current_contest()
    contests = DBSession.query(Contest).filter(Contest.end < datetime.datetime.now()).order_by('-end')
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    contests = [{ 'contest': contest, 'total':  count_contest_votes(contest.id), 'winners': get_winner_cards(contest) } for contest in contests]
    return {
        'current_contest': current_contest,
        'contests': contests,
        'url_prefix': settings['url_prefix'],
        'title': 'Contests listing',
    }


@view_config(route_name='json_id', renderer='json')
def json_id_view(request):
    di = request.matchdict
    id = di.get("id", None)
    if id and id.isdigit():
        id = int(id)
    vote = DBSession.query(Vote).filter(Vote.id_contest == 0, Vote.id_card == id).first()
    if not vote:
        return {}
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return {'id': id, 'count': vote.counter}

@view_config(route_name='json_name', renderer='json')
def json_name_view(request):
    di = request.matchdict
    name = di.get("name", None)
    vote, count = DBSession.query(Vote,func.sum(Vote.counter).label('counter_all')).filter(Vote.id_contest == 0, Vote.name == name).first()
    if not vote:
        return {}
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return {'name': name, 'count': count}

@view_config(route_name='json_contest', renderer='json')
def json_contest_view(request):
    di = request.matchdict
    id = di.get("id", None)
    if not id:
        return {}
    contest = DBSession.query(Contest).filter(Contest.id == id).first()
    if not contest:
        return {}
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    is_current = is_current_contest(contest)
    return {'name': contest.name, 'begin': str(contest.begin), 'end': str(contest.end),
            'id': contest.id, 'params': contest.params, 'current': is_current}

@view_config(route_name='json_current_contest', renderer='json')
def json_current_contest_view(request):
    contest = get_current_contest()
    if not contest:
        return {}
    registry = pyramid.threadlocal.get_current_registry()
    settings = registry.settings
    return {'name': contest.name, 'begin': str(contest.begin), 'end': str(contest.end),
            'id': contest.id, 'params': contest.params, current: True}
