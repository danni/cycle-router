import pytest

from sqlalchemy.exc import OperationalError
from cyclerouter.webapp import app as application
from cyclerouter.orm import db as alchemydb


@pytest.fixture(scope='session')
def db():
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = \
        'postgresql://cyclerouter:bikes@localhost/cycleroutertest'
    try:
        alchemydb.drop_all()
        alchemydb.create_all()
    except OperationalError:
        print "You probably forgot to run ./create-postgis-db.sh cycleroutertest"
        raise

    return alchemydb


@pytest.fixture(scope='session')
def app(db):
    return application.test_client()
