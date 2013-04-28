import json
from glob import glob

import numpy as np

from orm import User, Track, syncdb, session
from tests.util import get_test_resource

def test_create_db():
    syncdb()


def test_import_user():
    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 'badger',
            }

        token = 'TOKEN'

    obj = User.from_rk(FakeRk())

    assert obj

    assert session.query(User).count() == 1
    assert obj.user_id == 'badger'
    assert obj.token == 'TOKEN'

    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 'badger',
            }

        token = 'TOKEN2'

    obj = User.from_rk(FakeRk())

    assert session.query(User).count() == 1
    assert obj.user_id == 'badger'
    assert obj.token == 'TOKEN2'

    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 'snake',
            }

        token = 'TOKEN3'

    obj = User.from_rk(FakeRk())

    assert session.query(User).count() == 2
    assert obj.user_id == 'snake'
    assert obj.token == 'TOKEN3'


def test_api_obj_from_user():
    obj = session.query(User).filter(User.user_id == 'badger').one()

    assert obj

    rk = obj.to_rk()

    assert rk.token == 'TOKEN2'


def test_import_track():
    filename = glob(get_test_resource('json/*.json'))[6]

    with open(filename) as f:
        data = json.load(f)

    track = Track.from_rk_json(data)

    npoints = session.scalar(track.points.num_points())

    assert len(data['path']) == npoints

    # FIXME: how to determine the UTM zone automatically?
    length = session.scalar(track.points.transform(32755).length())

    assert np.abs(data['total_distance'] - length) < 5


def test_extra_func_length_spheroid():
    track = session.query(Track).filter_by(id=1).first()

    filename = glob(get_test_resource('json/*.json'))[6]

    with open(filename) as f:
        data = json.load(f)

    # FIXME: can we get the SPHEROID from the metadata?
    length = session.scalar(track.points.length_spheroid(
        'SPHEROID["WGS 84",6378137,298.257223563]'))

    assert np.abs(data['total_distance'] - length) < 5


def test_request_track():
    track = session.query(Track).filter_by(id=1).first()

    assert track
