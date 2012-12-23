from datetime import datetime

import pytest

from matplotlib import pyplot as plt
from matplotlib.mlab import FormatDatetime

import gpx

@pytest.fixture
def xml(request):
    fp = open('RK_gpx _2012-12-18_2012.gpx', 'rb')

    request.addfinalizer(fp.close)

    return fp

def test_import(xml):
    track = gpx.Track(xml)

    assert len(track) == 413

def test_plot_elevation(xml):
    track = gpx.Track(xml)

    fig, ax = plt.subplots(1)

    ax.plot(track.time, track.elev)

    fig.autofmt_xdate()
    plt.show()

def test_plot_speeds(xml):
    track = gpx.Track(xml)

    # validate sanity
    assert len(track.lat[:-1]) == len(track) - 1

    vels = track.calculate_vels()
    assert len(vels) == len(track) - 1

    fig, ax = plt.subplots(1)

    ax.plot(vels.time, vels.vel)

    fig.autofmt_xdate()
    plt.show()
