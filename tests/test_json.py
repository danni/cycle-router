
from glob import glob

import pytest

from matplotlib import pyplot as plt

from track import RKJSON, smooth

@pytest.fixture
def json(request):
    filename = glob('tracks/*.json')[1]

    fp = open(filename, 'rb')
    request.addfinalizer(fp.close)

    return fp

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
