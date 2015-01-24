from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    ip = Column(Text)
    id_card = Column(Integer)
    name = Column(Text)
    rarity = Column(Text)
    id_contest = Column(Integer)
    idolized = Column(Boolean)

#Index('my_index', Vote.name, unique=True, mysql_length=255)
