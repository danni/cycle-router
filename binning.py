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

class Grid(np.ndarray):

    @classmethod
    def calculate_bounds(cls, tracks):
        bounds = np.rec.array([(min(t.lat), max(t.lat), min(t.lon), max(t.lon))
                               for t in tracks],
                              names=('minlat', 'maxlat', 'minlon', 'maxlon'))

        return min(bounds.minlat), max(bounds.maxlat), \
               min(bounds.minlon), max(bounds.maxlon)

    def __new__(cls, tracks, xnum=50, ynum=50):

        minlat, maxlat, minlon, maxlon = cls.calculate_bounds(tracks)

        # initialise ourselves
        self = np.zeros((xnum, ynum)).view(Grid)

        self._elems_total = np.zeros((xnum, ynum))
        self._nelems = np.zeros((xnum, ynum), dtype=int)

        self.x = np.linspace(minlon, maxlon, num=xnum)
        self.y = np.linspace(minlat, maxlat, num=ynum)

        for track in tracks:
            self.add_track(track, recalculate=False)

        self._recalculate()

        return self

    def bin_direction(self, point, bearing):
        # g = Geod(ellps='WGS84')

        # p = list(reversed(point)) + list(reversed(self.refpoint))
        # refazi, _, _ = g.inv(*p)

        # print azi
        # print refazi
        pass

    def add_track(self, track, recalculate=True):
        vels = track.calculate_vels()
        xbins = np.digitize(vels.lon, self.x) - 1
        ybins = np.digitize(vels.lat, self.y) - 1

        for (x, y, anom, bearing) in zip(xbins, ybins, vels.anom, vels.bearing):
            # rows, columns
            self._elems_total[y, x] += anom
            self._nelems[y, x] += 1

        if recalculate:
            self._recalculate()

    def _recalculate(self):
        valid = self._nelems.nonzero()

        self[valid] = self._elems_total[valid] / self._nelems[valid]
