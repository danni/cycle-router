import json
from glob import glob

import numpy as np

from orm import Track, syncdb, session

def test_create_db():
    syncdb()


def test_import_track():
    filename = glob('tracks/*.json')[6]

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

    filename = glob('tracks/*.json')[6]

    with open(filename) as f:
        data = json.load(f)

    # FIXME: can we get the SPHEROID from the metadata?
    length = session.scalar(track.points.length_spheroid(
        'SPHEROID["WGS 84",6378137,298.257223563]'))

    assert np.abs(data['total_distance'] - length) < 5

def test_request_track():
    track = session.query(Track).filter_by(id=1).first()

    assert track
