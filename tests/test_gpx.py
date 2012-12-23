from datetime import datetime

import pytest

from matplotlib import pyplot as plt
from matplotlib.mlab import FormatDatetime

import gpx

@pytest.fixture(params=[
    'RK_gpx _2012-12-16_1734.gpx',
    'RK_gpx _2012-12-18_2012.gpx',
])
def xml(request):
    fp = open(request.param, 'rb')

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

    longsmoo = gpx.smooth(vels.vel, window_len=len(vels) / 2)
    shortsmoo = gpx.smooth(vels.vel)
    assert len(longsmoo) == len(shortsmoo) == len(vels)

    fig, ax = plt.subplots(1)

    ax.plot(vels.time, shortsmoo, vels.time, longsmoo)

    fig.autofmt_xdate()
    plt.show()

def test_plot_anom(xml):

    track = gpx.Track(xml)

    anom = track.calculate_anomolies()

    fig, ax = plt.subplots(1)
    ax.plot(anom.time, anom.anom)

    fig.autofmt_xdate()
    plt.show()
