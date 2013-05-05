import os
from glob import glob

import pytest

from matplotlib import pyplot as plt
from mpl_toolkits.basemap import Basemap

from cyclerouter.processing.track import RKJSON, smooth, BadInputException
from cyclerouter.processing.binning import Grid


NO_PLOTS = not (os.environ.get('PLOTS', 'no') == 'yes')


@pytest.fixture
def json(request):
    filename = glob('json/*.json')[1]

    fp = open(filename, 'rb')
    request.addfinalizer(fp.close)

    return fp


@pytest.mark.skipif('NO_PLOTS')
def test_point_scatter(json):
    track = RKJSON(json)

    fig, ax = plt.subplots(1)
    ax.scatter(track.lon, track.lat)

    for (i, p) in enumerate(zip(track.lon, track.lat)):
        plt.annotate(str(i), p)

    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plots(json):
    track = RKJSON(json)

    vels = track.calculate_vels()
    longsmoo = smooth(vels.vel, window_len=len(vels) / 2)
    shortsmoo = smooth(vels.vel)

    fig, (ax1, ax2) = plt.subplots(2)
    ax1.set_title("Speed and smoothed speed")
    ax1.yaxis.set_label_text("km/h")
    ax1.plot(vels.time, shortsmoo, vels.time, longsmoo)

    ax2.set_title("Speed anomaly")
    ax2.yaxis.set_label_text("% anomaly")
    ax2.plot(vels.time, vels.anom * 100)

    fig.autofmt_xdate()
    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plot_map_vels(json):
    track = RKJSON(json)
    vels = track.calculate_vels()

    lllat, lllon = min(track.lat) - 0.01, min(track.lon) - 0.01
    urlat, urlon = max(track.lat) + 0.01, max(track.lon) + 0.01

    print vels.bearing

    # find the centre point
    lat_0 = (urlat - lllat) / 2 + lllat
    lon_0 = (urlon - lllon) / 2 + lllon

    # FIXME: rsphere required because my Proj is screwy
    m = Basemap(projection='cyl',
                llcrnrlon=lllon, llcrnrlat=lllat,
                urcrnrlon=urlon, urcrnrlat=urlat,
                lat_0=lat_0, lon_0=lon_0,
                resolution='h')

    x, y = m(vels.lon, vels.lat)
    plt.annotate("Start", (x[0], y[0]))

    m.barbs(x, y, vels.u, vels.v) #, vels.anom, cmap=plt.get_cmap('RdBu_r'))
    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_plot_all_map_vels():
    def gen_tracks():
        for fn in glob('tracks/*.json'):
            with open(fn, 'rb') as fp:
                try:
                    yield RKJSON(fp)
                except BadInputException:
                    pass

    tracks = list(gen_tracks())

    print "Considering {} tracks".format(len(tracks))

    lllat, urlat, lllon, urlon = Grid.calculate_bounds(tracks)

    m = Basemap(projection='cyl',
                llcrnrlon=lllon, llcrnrlat=lllat,
                urcrnrlon=urlon, urcrnrlat=urlat,
                resolution='h')
    m.drawcoastlines()

    for t in tracks:
        vels = t.calculate_vels()
        x, y = m(vels.lon, vels.lat)
        m.barbs(x, y, vels.u, vels.v)

    plt.annotate("Docklands", (144.948, -37.815))
    plt.annotate("Brunswick", (144.960, -37.767))
    plt.annotate("Brunswick East", (144.979, -37.769))
    plt.annotate("Richmond", (144.999, -37.819))
    plt.annotate("Fitzroy", (144.978, -37.800))

    plt.show()
