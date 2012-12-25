
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
