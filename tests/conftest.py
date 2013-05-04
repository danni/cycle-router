import pytest

from sqlalchemy.exc import OperationalError

from db import Session


Session.initialise('postgresql://cyclerouter:bikes@localhost/cycleroutertest')

@pytest.fixture(scope='session')
def session():
    try:
        Session.syncdb()
    except OperationalError:
        print "You probably forgot to run ./create-postgis-db.sh cycleroutertest"
        raise

    return Session.session
