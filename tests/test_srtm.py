import numpy as np
import pytest
from matplotlib import pyplot as plt
from numpy.testing import assert_almost_equal, assert_allclose

from srtm import SRTM

from tests.test_json import json as track_json

@pytest.fixture(scope='module')
def grid():
    return SRTM()

@pytest.fixture
def track(track_json):
    from track import RKJSON

    return RKJSON(track_json)

def test_load_srtm(grid):
    # assert grid makes sense shapewise
    assert grid.ndim == 2
    assert grid.lats.ndim == grid.lons.ndim == 1
    assert grid.shape == (grid.lats.shape[0], grid.lons.shape[0])

    # 3 arcsecond grid
    assert_almost_equal(grid.binsize, 3./3600)

    # origin is top-left
    assert grid.lats[0] > grid.lats[1]
    assert_almost_equal(grid.lats[0] - grid.lats[1], grid.binsize)

    assert grid.lons[0] < grid.lons[1]
    assert_almost_equal(grid.lons[1] - grid.lons[0], grid.binsize)

    # Check our grid contains places interesting to us:
    # Melbourne
    assert grid.lats[0] >= -37.81361 >= grid.lats[-1] and \
           grid.lons[0] <= 144.96306 <= grid.lons[-1]
    # Altona
    assert grid.lats[0] >= -37.868 >= grid.lats[-1] and \
           grid.lons[0] <= 144.83 <= grid.lons[-1]
    # Brunswick
    assert grid.lats[0] >= -37.767 >= grid.lats[-1] and \
           grid.lons[0] <= 144.960 <= grid.lons[-1]

def test_plot_srtm(grid):

    fig, (ax1, ax2) = plt.subplots(2, 1)

    ax1.set_title("Meridional Elevation (Lon = {})".format(grid.lons[0]))
    ax1.set_xlabel("Latitude")
    ax1.plot(grid.lats, grid[:, 0])

    ax2.set_title("Zonal Elevation (Lat = {})".format(grid.lats[0]))
    ax2.set_xlabel("Longitude")
    ax2.plot(grid.lons, grid[0, :])

    plt.show()

def test_against_google(grid):

    import json
    from rk import Client

    client = Client()

    # make a request to the Google Elevation API
    _, content = client.request(
        'http://maps.googleapis.com/maps/api/elevation/json',
        data=dict(path='{},{}|{},{}'.format(grid.lats[0], grid.lons[0],
                                            grid.lats[-1], grid.lons[0]),
                  samples=100,
                  sensor='false'))

    content = json.loads(content)

    assert content['status'] == 'OK'
    assert 'results' in content

    data = np.empty(shape=(len(content['results']), 3))

    for i, rec in enumerate(content['results']):
        data[i] = [rec['location']['lat'],
                   rec['location']['lng'],
                   rec['elevation']]

    data = data.view(type=np.recarray,
                     dtype=[('lats', float),
                            ('lons', float),
                            ('elev', float)])

    fig, ax1 = plt.subplots(1, 1)

    ax1.set_title("SRTM v Google (Lon = {})".format(grid.lons[0]))
    ax1.set_xlabel("Latitude")
    ax1.plot(grid.lats, grid[:, 0])
    ax1.plot(data.lats, data.elev, 'r')
    ax1.set_xlim(-38.5, -33.5)
    ax1.set_ylim(-20, 200)

    plt.show()

@pytest.mark.parametrize(('lat', 'lon'), [
    (-37.81361, 144.96306), # Melbourne
    (-37.868, 144.83), # Altona
    (-37.767, 144.960), # Brunswick
])
def test_extract_point(grid, lat, lon):
    import json
    from rk import Client

    calc = grid.extract_point(lat, lon)

    # make a request to the Google Elevation API
    client = Client()

    _, content = client.request(
        'http://maps.googleapis.com/maps/api/elevation/json',
        data=dict(locations='{},{}'.format(lat, lon),
                  sensor='false'))

    content = json.loads(content)

    assert content['status'] == 'OK'
    assert 'results' in content
    assert len(content['results']) == 1

    result = content['results'][0]
    desr = result['elevation']
    res = result['resolution']

    # assert the calculated value is within the resolution of Google's value
    assert_allclose(calc, desr, atol=res / 2)

def test_extract_track_against_rk(grid, track):
    elevs = grid.extract_track(track)

    assert len(elevs) == len(track)

    # calculate RMS error
    rmse = np.sqrt(np.mean((elevs - track.elev) ** 2))
    nrms = rmse / (elevs.max() - elevs.min())

    print "RMS error", rmse
    print "NRMS", nrms

    fig, ax1 = plt.subplots(1, 1)

    ax1.set_title("SRTM v RK")
    ax1.plot(elevs)
    ax1.plot(track.elev, 'r')

    plt.show()
