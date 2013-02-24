from numpy.testing import assert_almost_equal

from srtm import SRTM

def test_load_srtm():
    grid = SRTM()

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
