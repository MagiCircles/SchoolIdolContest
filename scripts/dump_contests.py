from pyramid.paster import bootstrap
import json

ENV = 'development.ini'

env = bootstrap(ENV)

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func
import transaction

from schoolidolcontest.models import (
    DBSession,
    Contest,
    )

votes = DBSession.query(Contest).all()

dump = list()

for vote in votes:
    dump.append({'id':vote.id,
                 'name':vote.name,
                 'params':vote.params,
                 'begin':str(vote.begin),
                 'end':str(vote.end),
                 'result':vote.result_type})

f = open('contests.json', "w")
f.write(json.dumps(dump))
f.close()
