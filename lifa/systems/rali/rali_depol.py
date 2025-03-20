from ...licel_depol import LicelCalibrationMeasurement
from . import rali_depolarization_parameters

class RALICalibrationMeasurement(LicelCalibrationMeasurement):
    extra_netcdf_parameters = rali_depolarization_parameters
