# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Danielle Madeley <danielle@madeley.id.au>

from datetime import datetime, timedelta
import json
from math import pi

from lxml import etree
from pyproj import Proj
import numpy as np

class BadInputException(Exception):
    pass

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

    def __new__(cls, fp):
        track = list(cls._parse(fp))

        # initialise ourselves as a recarray
        return np.array(track,
                        dtype=[('lat', float),
                               ('lon', float),
                               ('elev', float),
                               ('time', datetime),
                              ]).view(cls)

    def _parse(cls, fp):
        raise NotImplemented()

    def calculate_vels(self, smooth_vels=False, utm_zone=55):

        p = Proj(proj='utm', zone=utm_zone, ellps='WGS84')

        # project coordinates into eastings and northings
        # This simplifies our geodetics, but requests us to specify a UTM zone
        x, y = p(self.lon, self.lat)

        rise = y[1:] - y[:-1]
        run = x[1:] - x[:-1]

        dist = np.sqrt(rise ** 2 + run ** 2)
        theta = np.arctan2(rise, run)

        # calculate the time deltas between consecutive points
        seconds = np.vectorize(lambda td: td.seconds)
        times = seconds(self.time[1:] - self.time[:-1])

        valid = times.nonzero()

        timestamps = self.time[1:][valid]
        lats = self.lat[1:][valid]
        lons = self.lon[1:][valid]
        theta = theta[valid]
        dist = dist[valid]
        times = times[valid]

        # calculate the velocities
        # remove any nans by making them zero
        vels = (dist / times) * 3.6 # m/s to km/h
        bearing = (90 - np.rad2deg(theta)) % 360

        # the idea here is to generate a long term average for the cycle
        # which we can consider the cyclists quiescent speed for the journey -
        # we do this using a very long window smoothing operator
        #
        # we then apply a short term smoothing operator to the velocities we
        # use to determine the anomalies, to remove some of the GPS jitter
        #
        # finally the anomalies are expressed as a percentage variation of the
        # cyclists speed from their quiescent speed

        longsmoo = smooth(vels, window_len=len(vels) / 2)
        shortsmoo = smooth(vels)

        anom = (shortsmoo - longsmoo) / longsmoo

        if smooth_vels:
            vels = smooth(vels)

        # decompose vels into u and v
        u = vels * np.cos(theta)
        v = vels * np.sin(theta)

        assert timestamps.shape == lats.shape == lons.shape == \
               bearing.shape == dist.shape == vels.shape == u.shape == \
               v.shape == anom.shape

        a = np.rec.fromarrays([timestamps, lats, lons,
                               bearing, dist, vels,
                               u, v, anom],
                              names=('time', 'lat', 'lon',
                                     'bearing', 'dist', 'vel',
                                     'u', 'v', 'anom'))

        return a

class GPX(Track):

    NAMESPACES = {
        None: 'http://www.topografix.com/GPX/1/1',
        'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
    }

    @staticmethod
    def elem(tag, namespace=None):
        return tag.format('{%s}' % GPX.NAMESPACES[namespace])

    @classmethod
    def _parse(cls, fp):
        try:
            for _, elem in etree.iterparse(fp, tag=GPX.elem('{}trkpt')):
                lat = float(elem.get('lat'))
                lon = float(elem.get('lon'))
                elev = float(elem.find(GPX.elem('{}ele')).text)
                time = datetime.strptime(elem.find(GPX.elem('{}time')).text,
                                         '%Y-%m-%dT%H:%M:%SZ')

                yield (lat, lon, elev, time)

                elem.clear()
        except etree.XMLSyntaxError:
            # why is this?
            pass

class RKJSON(Track):
    "RunKeeper JSON format"

    @classmethod
    def _parse(cls, fp):
        track = json.load(fp)

        if 'path' not in track:
            raise BadInputException("No path in dataset")

        starttime = datetime.strptime(track['start_time'],
                                      '%a, %d %b %Y %H:%M:%S')

        for point in track['path']:

            if point['type'] == 'manual':
                raise BadInputException("Manually edited dataset")

            lat = point['latitude']
            lon = point['longitude']
            elev = point['altitude']
            time = starttime + timedelta(seconds=point['timestamp'])

            yield (lat, lon, elev, time)
