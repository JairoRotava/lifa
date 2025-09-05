# Use "pytest tests" in command line for testing, or right click run test in visual studio code

import pytest
import glob
from lifa import licel

def test_func():
    assert 1 == 1

def test_subset_by_bin():
    files = glob.glob('./tests/tests_data/measurement_1/*')
    measurements = licel.LicelLidarMeasurement(files)
    subset_channels = measurements.subset_by_channels(['00355.o_an', '00395.s_an', '00353.o_an'])
    subset = subset_channels.subset_by_bins(10, 20)
    assert 1 == 1

def test_calculate_rc():
    files = glob.glob('./tests/tests_data/measurement_1/*')
    measurements = licel.LicelLidarMeasurement(files)
    channel = measurements.channels['00355.o_an']
    channel.calculate_rc()
    assert 1 == 1

def test_photon_counting():
    files = glob.glob('./tests/tests_data/measurement_1/*')
    measurements = licel.LicelLidarMeasurement(files)
    channel = measurements.channels['00355.o_ph']
    assert 1 == 1


if __name__ == "__main__":
    pytest.main()

