from pyramid.paster import bootstrap
import datetime

ENV = 'production.ini'

env = bootstrap(ENV)

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func
import transaction

from schoolidolcontest.models import (
    DBSession,
    Vote,
    VoteSession,
    Contest,
    )

onedaybefore = datetime.datetime.now() - datetime.timedelta(hours=24)
oldsessions = DBSession.query(VoteSession).filter(VoteSession.created <= onedaybefore).all()

for session in oldsessions:
    DBSession.delete(session)
