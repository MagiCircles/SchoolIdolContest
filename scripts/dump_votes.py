from pyramid.paster import bootstrap
import json

ENV = 'development.ini'

env = bootstrap(ENV)

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func
import transaction

from schoolidolcontest.models import (
    DBSession,
    Vote,
    )

votes = DBSession.query(Vote).all()

dump = list()

for vote in votes:
    dump.append({'id':vote.id,
                 'card':vote.id_card,
                 'contest':vote.id_contest,
                 'counter':vote.counter,
                 'idolized':vote.idolized})

f = open('votes.json', "w")
f.write(json.dumps(dump))
f.close()
