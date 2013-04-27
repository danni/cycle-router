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

from sqlalchemy import Column, Integer, String, \
                       MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from geoalchemy import GeometryColumn, LineString, GeometryDDL, \
                       WKTSpatialElement
from geoalchemy.dialect import DialectManager
from geoalchemy.functions import BaseFunction
from geoalchemy.postgis import pg_functions

from util import monkeypatchclass


engine = create_engine('postgresql://cyclerouter:bikes@localhost/cyclerouter')
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData(engine)
Base = declarative_base(metadata=metadata)


def syncdb():
    """
    Drop defined tables and recreate them.
    """

    metadata.drop_all()
    metadata.create_all()


# monkeypatch in extra functions
@monkeypatchclass(pg_functions)
class more_pg_functions:
    class length_spheroid(BaseFunction):
        pass


dialect = DialectManager.get_spatial_dialect(metadata.bind.dialect)
dialect._get_function_mapping().update({
    more_pg_functions.length_spheroid: 'ST_Length_Spheroid',
})


class Track(Base):
    """
    Represents a Track in a PostGIS database.
    """

    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(128))
    track_id = Column(String(128))
    points = GeometryColumn(LineString(4))

    @classmethod
    def from_rk_json(cls, json, commit=True):
        user_id = json['userID']
        track_id = json['uri']

        points = 'LINESTRING({})'.format(','.join(
            ('{longitude} {latitude} {altitude} {timestamp}'.format(**p)
             for p in json['path'])
            ))

        obj = cls(user_id=user_id,
                  track_id=track_id,
                  points=WKTSpatialElement(points))

        if commit:
            session.add(obj)
            session.commit()

        return obj

GeometryDDL(Track.__table__)
