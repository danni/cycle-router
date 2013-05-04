import json

import numpy as np

from orm import User, Track
from tests.util import get_test_resource


def test_import_user(session):
    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 1,
            }

        token = 'TOKEN'

    obj = User.from_rk(FakeRk())

    assert obj

    updated = obj.updated
    created = obj.created

    assert session.query(User).count() == 1
    assert obj.user_id == 1
    assert obj.token == 'TOKEN'

    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 1,
            }

        token = 'TOKEN2'

    obj = User.from_rk(FakeRk())

    assert session.query(User).count() == 1
    assert obj.user_id == 1
    assert obj.token == 'TOKEN2'
    assert obj.updated > updated
    assert obj.created == created

    class FakeRk(object):
        def get_user(self):
            return {
                'userID': 2,
            }

        token = 'TOKEN3'

    obj = User.from_rk(FakeRk())

    assert session.query(User).count() == 2
    assert obj.user_id == 2
    assert obj.token == 'TOKEN3'


def test_api_obj_from_user(session):
    obj = session.query(User).filter(User.user_id == 1).one()

    assert obj

    rk = obj.to_rk()

    assert rk.token == 'TOKEN2'


def test_import_track(session):
    filename = get_test_resource('json/97684385.json')

    with open(filename) as f:
        data = json.load(f)

    # we need to insert this user_id into the database
    session.add(User(user_id=data['userID']))
    session.commit()

    track = Track.from_rk_json(data)

    assert session.query(Track).count() == 1

    npoints = session.scalar(track.points.num_points())

    assert len(data['path']) == npoints

    # FIXME: how to determine the UTM zone automatically?
    length = session.scalar(track.points.transform(32755).length())

    assert np.abs(data['total_distance'] - length) < 10 # within 10m


def test_reimport_track(session):
    updated = session.query(Track).one().updated

    filename = get_test_resource('json/97684385.json')

    with open(filename) as f:
        data = json.load(f)

    track = Track.from_rk_json(data)

    assert session.query(Track).count() == 1
    assert track.updated > updated


def test_backref(session):
    user = User.get_user('11271062')

    assert len(user.tracks) == 1

    track = user.tracks[0]

    assert track.track_id == '/fitnessActivities/97684385'


def test_extra_func_length_spheroid(session):
    track = session.query(Track).filter_by(id=1).first()

    filename = get_test_resource('json/97684385.json')

    with open(filename) as f:
        data = json.load(f)

    # FIXME: can we get the SPHEROID from the metadata?
    length = session.scalar(track.points.length_spheroid(
        'SPHEROID["WGS 84",6378137,298.257223563]'))

    assert np.abs(data['total_distance'] - length) < 10 # within 10m


def test_request_track(session):
    track = session.query(Track).filter_by(id=1).first()

    assert track


def test_cascade(session):
    track = session.query(Track).get(1)
    session.delete(track.user)
    session.commit()

    assert session.query(User).count() == 2
    assert session.query(Track).count() == 0
