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

from contextlib import contextmanager

import gdal
import numpy as np
import numpy.ma as ma
from gdalconst import *
from numpy.testing import assert_almost_equal

MIN_INT16 = -2**15

@contextmanager
def GDAL_Open(*args, **kwargs):
    """
    A context manager for gdal.Open.
    """

    try:
        yield gdal.Open(*args, **kwargs)
    finally:
        # how do I close ds?
        pass

class SRTM(ma.MaskedArray):
    """
    Loads Geoscience Australia SRTM DEM data from ESRI grid format.
    """

    def __new__(cls,
                gridfile='3sSRTM_2008_DEM_ESRI_GRID_3sx3s_Mosaic/dem3s_int'):

        with GDAL_Open(gridfile, GA_ReadOnly) as ds:

            # FIXME: do we need to handle this somehow?
            # print ds.GetProjection()

            originx, sizex, _, originy, _, sizey = ds.GetGeoTransform()

            # ensure regular grid
            assert sizex == -sizey, "Grid not regular or correct orientation"

            # assert we only have one layer
            assert ds.RasterCount == 1, "Expected only one layer in grid"

            band = ds.GetRasterBand(1)
            data = band.ReadAsArray()

            # determine the mask
            mask = (data == MIN_INT16)

            self = ma.array(data, mask=mask).view(cls)

            self.binsize = sizex

            self.lats = np.linspace(originy, originy + ds.RasterYSize * sizey,
                                    num=ds.RasterYSize, endpoint=False)
            self.lons = np.linspace(originx, originx + ds.RasterXSize * sizex,
                                    num=ds.RasterXSize, endpoint=False)

            return self

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)
