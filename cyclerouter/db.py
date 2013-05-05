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
Database configuration

This is separate from the ORM so you can initialize your database and
then use that initialisation for the models.
"""

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from util import classproperty


class NotInitialised(Exception):
    def __init__(self):
        super(Exception, self).__init__("Session is not initialised")


class AlreadyInitialised(Exception):
    def __init__(self):
        super(Exception, self).__init__("Attempted to initialise session twice")


class Session(object):
    """
    Stores all of the database session information.

    The purpose of this class is to allow multiple databases to be used by
    the ORM as required. Specifically to allow a different database to be
    used by the tests.
    """

    _engine = None
    _session = None
    _metadata = None
    _Base = None

    @classmethod
    def initialise(cls, database=None, force=False):
        """
        Initialise the database session

        @database is an SQLAlchemy database URL
        """

        if database is None:
            database = 'postgresql://cyclerouter:bikes@localhost/cyclerouter'

        if cls._engine:
            if force:
                raise AlreadyInitialised()
            else:
                return

        cls._engine = create_engine(database)
        Session = sessionmaker(bind=cls._engine)
        cls._session = Session()

        cls._metadata = MetaData(cls._engine)
        cls._Base = declarative_base(metadata=cls._metadata)

    @classproperty
    @classmethod
    def engine(cls):
        if not cls._engine:
            raise NotInitialised()

        return cls._engine

    @classproperty
    @classmethod
    def session(cls):
        if not cls._session:
            raise NotInitialised()

        return cls._session

    @classproperty
    @classmethod
    def metadata(cls):
        if not cls._metadata:
            raise NotInitialised()

        return cls._metadata

    @classproperty
    @classmethod
    def Base(cls):
        if not cls._Base:
            raise NotInitialised()

        return cls._Base

    @classmethod
    def syncdb(cls):
        """
        Drop defined tables and recreate them.
        """

        cls.metadata.drop_all()
        cls.metadata.create_all()
