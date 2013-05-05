from urlparse import urlparse, parse_qs

import pytest

from flask import request, redirect

from cyclerouter.webapp import FlaskRK, app as realapp
from cyclerouter.rk import AuthenticationException
from cyclerouter.keys import CLIENT_ID


@pytest.fixture
def monkeyRK(monkeypatch):
    """
    A monkeypatched RK
    """

    monkeypatch.setattr(FlaskRK, 'API_URL', '/mock/api')
    monkeypatch.setattr(FlaskRK, 'AUTHORIZATION_URL', '/mock/authorize')
    monkeypatch.setattr(FlaskRK, 'ACCESS_TOKEN_URL', '/mock/token')

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


def test_get_token_no_code(app, monkeyRK):

    with pytest.raises(AuthenticationException) as e:
        rv = app.get('/get-token')

        print rv
        print rv.headers
        print rv.data

    print dir(e)
    assert e.value.message == 'Code was not supplied'
