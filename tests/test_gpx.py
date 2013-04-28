from math import *
import os
import os.path

import pytest

from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap

from track import GPX, smooth


NO_PLOTS = not (os.environ.get('PLOTS', 'no') == 'yes')


@pytest.fixture(params=[
    'gpx/RK_gpx _2012-12-16_1734.gpx',
    'gpx/RK_gpx _2012-12-18_2012.gpx',
])
def xml(request):
    filename = os.path.join(os.path.dirname(__file__),
                            request.param)
    fp = open(filename, 'rb')

    request.addfinalizer(fp.close)

    return fp


def test_import(xml):
    track = GPX(xml)

    assert track is not None


@pytest.mark.skipif('NO_PLOTS')
def test_plot_elevation(xml):
    track = GPX(xml)

    fig, ax = plt.subplots(1)

    ax.plot(track.time, track.elev)

    fig.autofmt_xdate()
    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plot_speeds(xml):
    track = GPX(xml)

    # validate sanity
    assert len(track.lat[:-1]) == len(track) - 1

    vels = track.calculate_vels()
    assert len(vels) == len(track) - 1

    longsmoo = smooth(vels.vel, window_len=len(vels) / 2)
    shortsmoo = smooth(vels.vel)
    assert len(longsmoo) == len(shortsmoo) == len(vels)

    fig, ax = plt.subplots(1)

    ax.plot(vels.time, shortsmoo, vels.time, longsmoo)

    fig.autofmt_xdate()
    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plot_anom(xml):

    track = GPX(xml)

    anom = track.calculate_vels()

    fig, ax = plt.subplots(1)
    ax.plot(anom.time, anom.anom)

    fig.autofmt_xdate()
    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plot_map_vels(xml):
    track = GPX(xml)
    vels = track.calculate_vels(smooth_vels=True)

    lllat, lllon = min(track.lat) - 0.01, min(track.lon) - 0.01
    urlat, urlon = max(track.lat) + 0.01, max(track.lon) + 0.01

    # find the centre point
    lat_0 = (urlat - lllat) / 2 + lllat
    lon_0 = (urlon - lllon) / 2 + lllon

    # FIXME: rsphere required because my Proj is screwy
    m = Basemap(projection='cyl',
                llcrnrlon=lllon, llcrnrlat=lllat,
                urcrnrlon=urlon, urcrnrlat=urlat,
                lat_0=lat_0, lon_0=lon_0,
                resolution='h')
                # rsphere=(6378137.00, 6356752.3142))

    x, y = m(vels.lon, vels.lat)

    m.drawcoastlines()
    m.drawrivers()
    m.barbs(x, y, vels.u, vels.v) #, vels.anom, cmap=plt.get_cmap('RdBu_r'))
    plt.show()
