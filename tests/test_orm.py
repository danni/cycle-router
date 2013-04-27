import json
from glob import glob

import numpy as np

from track import RKJSON
from orm import *

def test_create_db():
    syncdb()


def test_import_track():
    filename = glob('tracks/*.json')[6]

    with open(filename) as f:
        data = json.load(f)
        f.seek(0)

        track = RKJSON(f)
        track_obj = Track.from_track(track)

    npoints = session.scalar(track_obj.points.num_points())

    assert len(data['path']) == len(track) == npoints

    # transform to UTM55S -- FIXME: can we do this on the spheroid
    length = session.scalar(track_obj.points.transform(32755).length())

    assert np.abs(data['total_distance'] - length) < 5

    # length = session.scalar(track_obj.points.length_spheroid('SPHEROID["WGS 84",6378137,298.257223563]'))

    # assert data['total_distance'] == length


def test_request_track():
    track = session.query(Track).filter_by(id=1).first()

    assert track
