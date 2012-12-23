
from datetime import datetime

from lxml import etree
from pyproj import Geod
import numpy as np

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
        # FIXME: what to do about div-by-zero?
        vels = dist / times

        a = np.rec.fromarrays([self.time[1:], azi, dist, vels],
                              names=('time', 'azi', 'dist', 'vel'))

        return a
