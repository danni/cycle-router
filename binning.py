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

import numpy as np
from pyproj import Proj

class LatLon(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

MELBOURNE = LatLon(-37.81361, 144.96306) # Coordinates of Melbourne

class Direction(object):
    INBOUND, OUTBOUND = range(2)

class Grid(np.ndarray):

    @classmethod
    def calculate_bounds(cls, tracks):
        bounds = np.rec.array([(min(t.lat), max(t.lat), min(t.lon), max(t.lon))
                               for t in tracks],
                              names=('minlat', 'maxlat', 'minlon', 'maxlon'))

        return min(bounds.minlat), max(bounds.maxlat), \
               min(bounds.minlon), max(bounds.maxlon)

    def __new__(cls, tracks, xnum=100, ynum=100, refpoint=MELBOURNE):

        minlat, maxlat, minlon, maxlon = cls.calculate_bounds(tracks)

        # initialise ourselves
        self = np.zeros((2, xnum, ynum)).view(Grid)

        self._elems_total = np.zeros((2, xnum, ynum))
        self._nelems = np.zeros((2, xnum, ynum), dtype=int)

        self.refpoint = refpoint
        self.x = np.linspace(minlon, maxlon, num=xnum)
        self.y = np.linspace(minlat, maxlat, num=ynum)

        for track in tracks:
            self.add_track(track, recalculate=False)

        self._recalculate()

        return self

    def bin_direction(self, point, bearing=None, utm_zone=55):
        p = Proj(proj='utm', zone=utm_zone, ellps='WGS84')

        if bearing is None:
            bearing = point.bearing

        refx, refy = p(self.refpoint.lon, self.refpoint.lat)
        px, py = p(point.lon, point.lat)

        rise = refy - py
        run = refx - px

        dist = np.sqrt(rise ** 2 + run ** 2)
        theta = np.arctan2(rise, run)

        beta = (90 - np.rad2deg(theta)) % 360

        if beta - 90 < bearing <= beta + 90:
            return Direction.INBOUND
        else:
            return Direction.OUTBOUND

    def add_track(self, track, recalculate=True):
        vels = track.calculate_vels()
        xbins = np.digitize(vels.lon, self.x) - 1
        ybins = np.digitize(vels.lat, self.y) - 1

        for (x, y, vel) in zip(xbins, ybins, vels):
            d = self.bin_direction(vel)

            # rows, columns
            self._elems_total[d, y, x] += vel.anom
            self._nelems[d, y, x] += 1

        if recalculate:
            self._recalculate()

    def _recalculate(self):
        valid = self._nelems.nonzero()

        self[valid] = self._elems_total[valid] / self._nelems[valid]
