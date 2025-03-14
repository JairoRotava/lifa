from ...licel import LicelLidarMeasurement

from . import rali_netcdf_parameters


class RaliLidarMeasurement(LicelLidarMeasurement):
    extra_netcdf_parameters = rali_netcdf_parameters


