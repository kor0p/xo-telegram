import sqlalchemy as db

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_mixins import AllFeaturesMixin
from .config import path_to_db

engine = db.create_engine(path_to_db, convert_unicode=True)
session = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine))
metadata = db.MetaData(bind=engine)


class Base(declarative_base(metadata=metadata), AllFeaturesMixin):
    __abstract__ = True

    # @classmethod
    # def getColumns(cls):
    #     return cls.__table__.columns

    @classmethod
    def whereAll(cls, _f=None, **kwargs):
        if _f is None:
            _f = cls.raw
        return list(map(_f, cls.where(**kwargs).all()))

    def update(self, **kwargs):
        res = super().update(**kwargs)
        return res

    def raw(self):
        return {str(k): v for k, v in self.to_dict(nested=True).items()}


class XOTEXTDB(Base):
    __tablename__ = 'xo_text'
    id = db.Column(db.String, primary_key=True)
    isX = db.Column(db.SmallInteger)
    b = db.Column(db.String)
    deleted_at = db.Column(db.DateTime)


class XODB(Base):
    __tablename__ = 'xo'
    id = db.Column(db.String, primary_key=True)
    plX = db.Column(db.JSON)
    plO = db.Column(db.JSON)
    giveup_user = db.Column(db.JSON)
    tie_id = db.Column(db.String)
    queue = db.Column(db.SmallInteger)
    b = db.Column(db.String)
    deleted_at = db.Column(db.DateTime)


Base.set_session(session)
metadata.create_all()
