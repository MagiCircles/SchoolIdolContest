from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean,
    Date,
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
    id_card = Column(Integer)
    name = Column(Text)
    rarity = Column(Text)
    id_contest = Column(Integer)
    counter = Column(Integer)
    idolized = Column(Boolean)

class Contest(Base):
    __tablename__ = 'contest'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    params = Column(Text)
    begin = Column(Date)
    end = Column(Date)
    best_girl = Column(Boolean)


#Index('my_index', Vote.name, unique=True, mysql_length=255)
