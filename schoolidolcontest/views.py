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


@view_config(route_name='home', renderer='templates/home.pt')
def my_view(request):
    r = ApiRequest()
    session = request.session
    response = r.get('/api/cards/')
    content = response.json()
    r1 = random.randint(1, content['count'])
    r2 = random.randint(1, content['count'])
    while (r1 == r2):
        r2 = random.randint(1, content['count'])
    card_left = r.get('/api/cards/' + str(r1) + '/').json()
    card_right = r.get('/api/cards/' + str(r2) + '/').json()
    session['left'] = card_left
    session['right'] = card_right
    return {'right': card_right, 'left': card_left}


@view_config(route_name='vote')
def vote_view(request):
    session = request.session
    if ('left' or 'right' in request.params) and ('left' or 'right' in session):
        card = session['left'] if 'left' in request.params else session['right']
        card_id = card['id']
        name = card['name']
        rarity = card['rarity']
        id_contest = 0
        ip = request.remote_addr
        try:
            model = Vote(id_card=card_id, ip=ip, id_contest=id_contest,
                         name=name, rarity=rarity)
            DBSession.add(model)
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain',
                            status_int=500)
    return HTTPFound(location='/')

def count_one_by_field(name):
    r = ApiRequest()
    req = DBSession.query(Vote, func.count(name).label('total')).group_by(name).order_by('total DESC').first()
    card = req._asdict()['Vote'].id_card
    response = r.get('/api/cards/' + str(card) + '/')
    return response.json()

@view_config(route_name='bestgirl', renderer='templates/bestgirl.pt')
def best_girl_view(request):
    best_card = count_one_by_field('id_card')
    best_girl = count_one_by_field('name')
    return {'best_card': best_card, 'best_girl': best_girl}


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

