# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Danielle Madeley <danielle@madeley.id.au>

"""
Model definitions for an SQLAlchemy ORM
"""

from datetime import datetime

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

from geoalchemy import GeometryColumn, LineString, GeometryDDL, \
                       WKTSpatialElement
from geoalchemy.functions import BaseFunction
from geoalchemy.dialect import SpatialDialect
from geoalchemy.postgis import pg_functions

from webapp import app
from rk import RK
from util import monkeypatch, monkeypatchclass


# Flask-SQLAlchemy object
db = SQLAlchemy(app)


# monkeypatch in extra functions
@monkeypatchclass(pg_functions)
class more_pg_functions:
    """
    Additional functions to support for PostGIS
    """

    class length_spheroid(BaseFunction):
        _method = 'ST_Length_Spheroid'


@monkeypatch(SpatialDialect)
def get_function(self, function_cls):
    """
    Add support for the _method attribute
    """

    try:
        return function_cls._method
    except AttributeError:
        return self.__super__get_function(function_cls)


class User(db.Model):
    """
    Represents a user we've connected with.
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    # the RunKeeper user_id
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)
    service = db.Column(db.String(128), default='RunKeeper', nullable=False)
    token = db.Column(db.String(128))

    tracks = db.relationship('Track', cascade="all, delete, delete-orphan")

    @classmethod
    def from_rk(cls, rk, commit=True):
        """
        CREATE or UPDATE a user object from an RK API object
        """

        assert rk.token

        json = rk.get_user()

        user_id = json['userID']
        token = rk.token

        # look to see if we already have this user
        try:
            obj = User.get_user(user_id)
            obj.token = rk.token
        except NoResultFound:
            obj = cls(user_id=user_id,
                      token=token)

        if commit:
            db.session.add(obj)
            db.session.commit()

        return obj

    @classmethod
    def get_user(cls, user_id):
        return db.session.query(cls).filter(cls.user_id == user_id).one()

    def to_rk(self):
        """
        Return an RK API object from a User
        """

        return RK(token=self.token)


class Track(db.Model):
    """
    Represents a Track in a PostGIS database.
    """

    __tablename__ = 'tracks'

    id = db.Column(db.Integer, primary_key=True)
    user_pk = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    track_id = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    updated = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow, onupdate=datetime.utcnow)
    points = GeometryColumn(LineString(4), nullable=False)

    user = db.relationship('User')

    def __init__(self, *args, **kwargs):
        """
        Turn user_id into a User model
        """

        if 'user_id' in kwargs:
            user_id = kwargs.pop('user_id')
            user = User.get_user(user_id)

            kwargs['user'] = user

        super(Track, self).__init__(*args, **kwargs)


    @classmethod
    def from_rk_json(cls, json, commit=True):
        """
        CREATE or UPDATE a Track from RK JSON format
        """

        user_id = json['userID']
        track_id = json['uri']
        # FIXME: timezone? does RK care?
        activity_date = datetime.strptime(json['start_time'],
                                          '%a, %d %b %Y %H:%M:%S')

        points = 'LINESTRING({})'.format(','.join(
            ('{longitude} {latitude} {altitude} {timestamp}'.format(**p)
             for p in json['path'])
            ))
        points = WKTSpatialElement(points)

        # look to see if we already have this track
        try:
            obj = Track.get_track(user_id, track_id)
            obj.points = points
        except NoResultFound:
            obj = cls(user_id=user_id,
                      track_id=track_id,
                      date=activity_date,
                      points=points)

        if commit:
            db.session.add(obj)
            db.session.commit()

        return obj

    @classmethod
    def get_track(self, user, track_id):
        if isinstance(user, User):
            user_id = user.user_id
        else:
            user_id = user

        return db.session.query(Track).join(User).filter(
            User.user_id == user_id,
            Track.track_id == track_id).one()

GeometryDDL(Track.__table__)
