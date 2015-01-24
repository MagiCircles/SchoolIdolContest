import requests
import random

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func
import transaction

from .models import (
    DBSession,
    Vote,
    )


@view_config(route_name='home', renderer='templates/home.pt')
def my_view(request):
    response = requests.get('http://127.0.0.1:3333/api/cards/')
    content = response.json()
    r1 = random.randint(500, 510)
    r2 = random.randint(500, 510)
    print r1, r2
    response1 = requests.get('http://127.0.0.1:3333/api/cards/' + str(r1) + '/')
    response2 = requests.get('http://127.0.0.1:3333/api/cards/' + str(r2) + '/')
    return {'card2': response1.json(), 'card1': response2.json()}


@view_config(route_name='vote')
def vote_view(request):
    if 'card1' or 'card2' in request.params:
        if 'card1' in request.params:
            card_id = request.params['card1_id']
        else:
            card_id = request.params['card2_id']
        id_contest = 0
        ip = request.remote_addr
        try:
            model = Vote(id_card=card_id, ip=ip, id_contest=id_contest)
            DBSession.add(model)
        except DBAPIError:
            return Response(conn_err_msg, content_type='text/plain',
                            status_int=500)
    return HTTPFound(location='/')

@view_config(route_name='bestgirl', renderer='templates/bestgirl.pt')
def best_girl_view(request):
    one = DBSession.query(Vote,
                           func.count('id_card').label('total')).group_by('id_card').order_by('total DESC').first()
    #one = DBSession.query(Vote, func.count('id_card')).group_by('id_card').first()
    best_girl = one._asdict()['Vote'].id_card
    response = requests.get('http://127.0.0.1:3333/api/cards/' + str(best_girl) + '/')
    return {'best_girl': response.json()}


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

