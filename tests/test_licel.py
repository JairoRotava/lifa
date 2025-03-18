# Use "pytest tests" in command line for testing, or right click run test in visual studio code

import pytest
from atmospheric_lidar import licel

def test_func():
    assert 1 == 1

if __name__ == "__main__":
    pytest.main()

