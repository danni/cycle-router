import os
import pytest

from rk import CommandLineClient as RK


NO_NET = not (os.environ.get('NET', 'no') == 'yes')


@pytest.fixture(scope='session')
def rk(request):
    rk = RK()
    token = rk.authorize()
    assert token != ''

    return rk


@pytest.mark.skipif('NO_NET')
def test_get_user(rk):
    resp = rk.get_user()

    print resp

    assert 'profile' in resp
    assert 'nutrition' in resp


@pytest.mark.skipif('NO_NET')
def test_get_profile(rk):
    resp = rk.get_profile()

    print resp

    assert 'profile' in resp
    assert 'name' in resp


@pytest.mark.skipif('NO_NET')
def test_get_fitness_activities(rk):
    resp = rk.get_fitness_activities()

    assert 'items' in resp

    for item in resp['items']:
        assert 'uri' in item


@pytest.mark.skipif('NO_NET')
def test_get_fitness_items(rk):
    for item in rk.get_fitness_items():
        print item


@pytest.mark.skipif('NO_NET')
def test_get_fitness_item(rk):
    item = rk.get_fitness_items().next()

    print item

    item = rk.get_fitness_item(item['uri'])

    print item

    assert 0
