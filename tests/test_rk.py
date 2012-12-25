
import pytest

from rk import RK

@pytest.fixture(scope='session')
def rk(request):
    rk = RK()
    token = rk.authorize()
    assert token != ''

    return rk

def test_get_user(rk):
    resp = rk.get_user()

    print resp

    assert 'profile' in resp
    assert 'nutrition' in resp

def test_get_profile(rk):
    resp = rk.get_profile()

    print resp

    assert 'profile' in resp
    assert 'name' in resp
