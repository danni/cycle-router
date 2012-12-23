
from datetime import datetime

from lxml import etree
from pyproj import Geod
import numpy as np

def smooth(x, window_len=11, window='flat'):
    """
    Adapted from http://www.scipy.org/Cookbook/SignalSmooth
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    elif x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    elif window_len < 3:
        return x

    s = np.r_[x[window_len - 1:0:-1],x,x[-1:-window_len:-1]]

    if window == 'flat':
        w = np.ones(window_len, 'd')
    else:
        w = getattr(np, window)(window_len)

    y = np.convolve(w / w.sum(), s, mode='valid')

    return y[window_len / 2 - 1:-window_len / 2]

class Track(np.recarray):

    NAMESPACES = {
        None: 'http://www.topografix.com/GPX/1/1',
        'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
    }

    @staticmethod
    def elem(tag, namespace=None):
        return tag.format('{%s}' % Track.NAMESPACES[namespace])

    def __new__(cls, fp):
        track = []

        try:
            for _, elem in etree.iterparse(fp, tag=Track.elem('{}trkpt')):
                lat = float(elem.get('lat'))
                lon = float(elem.get('lon'))
                elev = float(elem.find(Track.elem('{}ele')).text)
                time = datetime.strptime(elem.find(Track.elem('{}time')).text,
                                         '%Y-%m-%dT%H:%M:%SZ')

                track.append((lat, lon, elev, time))

                elem.clear()
        except etree.XMLSyntaxError:
            # why is this?
            pass

        # initialise ourselves as a recarray
        return np.array(track,
                        dtype=[('lat', float),
                               ('lon', float),
                               ('elev', float),
                               ('time', datetime),
                              ]).view(cls)

    def calculate_vels(self):

        g = Geod(ellps='WGS84')

        # calculate the azimuths and distances between consecutive points
        azi, _, dist = g.inv(self.lon[:-1], self.lat[:-1],
                             self.lon[1:], self.lat[1:])

        # calculate the time deltas between consecutive points
        seconds = np.vectorize(lambda td: td.seconds)
        times = seconds(self.time[1:] - self.time[:-1])

        # calculate the velocities
        # remove any nans by making them zero
        vels = np.nan_to_num(dist / times) * 3.6

        a = np.rec.fromarrays([self.time[1:], azi, dist, vels],
                              names=('time', 'azi', 'dist', 'vel'))

        return a

    def calculate_anomolies(self):

        vels = self.calculate_vels()

        # the idea here is to generate a long term average for the cycle
        # which we can consider the cyclists quiescent speed for the journey -
        # we do this using a very long window smoothing operator
        #
        # we then apply a short term smoothing operator to the velocities we
        # use to determine the anomalies, to remove some of the GPS jitter
        #
        # finally the anomalies are expressed as a percentage variation of the
        # cyclists speed from their quiescent speed

        longsmoo = smooth(vels.vel, window_len=len(vels) / 2)
        shortsmoo = smooth(vels.vel)

        anom = (shortsmoo - longsmoo) / longsmoo

        a = np.rec.fromarrays([vels.time, anom],
                              names=('time', 'anom'))

        return a
