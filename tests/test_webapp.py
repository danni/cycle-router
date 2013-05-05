from copy import deepcopy
from urlparse import urlparse, parse_qs

import pytest

from flask import request, redirect

from cyclerouter.webapp import FlaskRK, app as realapp
from cyclerouter.rk import AuthenticationException
from cyclerouter.keys import CLIENT_ID
from cyclerouter.orm import User


# taken from the HealthGraph examples
REPLIES = {
    '/user': [
        {
            "userID": 1234567890,
            "profile": "/profile",
            "settings": "/settings",
            "fitness_activities": "/fitnessActivities",
            "strength_training_activities": "/strengthTrainingActivities",
            "background_activities": "/backgroundActivities",
            "sleep": "/sleep",
            "nutrition": "/nutrition",
            "weight": "/weight",
            "general_measurements": "/generalMeasurements",
            "diabetes": "/diabetes",
            "records": "/records",
            "team": "/team"
        },
    ],
    '/profile': [
        {
            "name": "John Doe",
            "location": "Sometown, USA",
            "athlete_type": "Ultra Marathoner",
            "gender": "M",
            "birthday": "Sat, Jan 1 2011 00:00:00",
            "elite": True,
            "profile": "http://www.runkeeper.com/user/JohnDoe",
            "small_picture": "/user/JohnDoe/small.jpg",
            "normal_picture": "/user/JohnDoe/normal.jpg",
            "medium_picture": "/user/JohnDoe/medium.jpg",
            "large_picture": "/user/JohnDoe/large.jpg",
        },
    ],
    '/fitnessActivities': [
        {
            "size": 40,
            "items": [
            {
               "type": "Running",
               "start_time": "Tue, 1 Mar 2011 07:00:00",
               "total_distance": 70,
               "duration": 10,
               "source": "RunKeeper",
               "entry_mode": "API",
               "has_map": "true",
               "uri": "/activities/40"
            },
            {
               "type": "Running",
               "start_time": "Thu, 3 Mar 2011 07:00:00",
               "total_distance": 70,
               "duration": 10,
               "source": "RunKeeper",
               "entry_mode": "Web",
               "has_map": "true",
               "uri": "/activities/39"
            },
            {
               "type": "Running",
               "startTime": "Sat, 5 Mar 2011 11:00:00",
               "total_distance": 70,
               "duration": 10,
               "source": "RunKeeper",
               "entry_mode": "API",
               "has_map": "true",
               "uri": "/activities/38"
            },
            {
               "type": "Running",
               "startTime": "Mon, 7 Mar 2011 07:00:00",
               "total_distance": 70,
               "duration": 10,
               "source": "RunKeeper",
               "entry_mode": "API",
               "has_map": "false",
               "uri": "/activities/37"
            },
            ],
            "previous": "https://api.runkeeper.com/user/1234567890/activities?page=2"
        },
    ],
}


@pytest.fixture
def monkeyRK(monkeypatch):
    """
    A monkeypatched RK
    """

    monkeypatch.setattr(FlaskRK, 'API_URL', '/mock/api')
    monkeypatch.setattr(FlaskRK, 'AUTHORIZATION_URL', '/mock/authorize')
    monkeypatch.setattr(FlaskRK, 'ACCESS_TOKEN_URL', '/mock/token')

    def request_token(self):
        self.token = 'TOKEN1'

        return self.token

    def _request(self, path, **kwargs):
        """
        Return the next reply on the queue.
        """

        return self.replies[path].pop(0)

    monkeypatch.setattr(FlaskRK, 'request_token', request_token)
    monkeypatch.setattr(FlaskRK, '_request', _request)

    @realapp.route('/mock/authorize')
    def mock_authorize():

        print request

        return redirect(request.args['redirect_uri'])

    return FlaskRK


def test_index(app):
    rv = app.get('/')

    print rv.data

    assert '<title>Cycle Router</title>' in rv.data
    assert '0 contributors.' in rv.data
    assert '0.0 kilometers.' in rv.data


def test_authorize(app):
    """
    Check that visiting /authorize redirects us to RunKeeper
    """

    rv = app.get('/authorize')

    print rv
    print rv.headers

    assert rv.status_code == 302
    assert rv.headers['Location'] == 'https://runkeeper.com/apps/authorize?redirect_uri=http%3A%2F%2Flocalhost%2Fauthorized&response_type=code&client_id={}'.format(CLIENT_ID)


def test_authorize_redirects(app, monkeyRK):
    """
    Check that visiting /authorize redirects to /authorized
    """

    rv = app.get('/authorize', follow_redirects=True)

    print rv
    print rv.headers
    print rv.data

    assert '<title>Cycle Router</title>' in rv.data
    assert '<h1>Please wait while we transfer you!</h1>' in rv.data


def test_monkey_rk(monkeyRK):

    monkeyRK.replies = deepcopy(REPLIES)

    rk = monkeyRK()

    assert rk.extract_code('/get-token?code=1234') == '1234'
    assert rk.request_token() == 'TOKEN1'
    assert rk.get_profile() == REPLIES['/profile'][0]

def test_get_token_no_code(app, monkeyRK):

    with pytest.raises(AuthenticationException) as e:
        rv = app.get('/get-token')

        print rv
        print rv.headers
        print rv.data

    print dir(e)
    assert e.value.message == 'Code was not supplied'


def test_get_token(app, db, monkeyRK):

    # ensure the database is clean
    db.session.query(User).filter(User.user_id == 1234567890).delete()

    rv = app.get('/get-token?code=1234')

    monkeyRK.replies = deepcopy(REPLIES)

    print rv.data

    datachunks = rv.data.strip().split('\n\n')

    print datachunks

    assert 'Accessing profile' in rv.data

    # check formatting
    assert all([s.startswith('data: {') for s in datachunks])

    # check we finish on the right state
    assert 'CARRIER TERMINATED' not in rv.data
    assert '"state": "complete"' in datachunks[-1]

    # check our user is now in the database
    assert db.session.query(User).filter(User.user_id == 1234567890,
                                         User.token == 'TOKEN1').one()
