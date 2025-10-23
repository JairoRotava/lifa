""" Calcula a razão de mistura de dois canais Raman

"""
import numpy as np
import scipy

from scipy.signal import savgol_filter

from .helper_functions import molecular_extinction, molecular_backscatter, number_density_at_pt, poly_evaluate_window
from .elastic_retrievals import _integrate_from_reference
from scipy.integrate import cumulative_trapezoid

def raman_mixing_ratio(signal_raman, reference_raman, dz, alpha_aerosol_extinction, calibration_const,
                      raman_wavelength, reference_wavelength, pressure, temperature):
    r"""
    Calculates the mixing ration of two raman signals

    Parameters
    ----------
    signal_raman : (M,) array
       The range-corrected Raman signal. Should be 1D array of size M.
    reference_raman : (M, ) array
       The range-corrected Reference Raman signal. Should be 1D array of size M.
    dz : float
       Altitude step, used in the integrals calculations (m)
    alpha_aerosol_extinction : (M,) array
       The aerosol extinction coefficient at each point of the signal profile for emission and Raman wavelength.
    calibration_const : float
       Calibratio constant for mixing ratio.
    raman_wavelength : float
       Raman signal wavelength (nm)
    ref_wavelength : float
       Raman reference wavelength (nm)
    pressure : (M, ) array
        Atmosphere pressure profile, same as shape as the lidar signal (Pa)
    temperature : (M, ) array
        Atmosphere temperature profile, same as shape as the lidar signal (K)

    Returns
    -------
    mixing_ratio : arrays
        The mixing ration m

    Notes 
    -----
    TODO: Escrever a formula correta aqui
    The aerosol backscatter coefficient is given by the formula:

    .. math::
       \beta_{aer}(R,\lambda_0) = [\beta_{aer}(R_0,\lambda_0) + \beta_{mol}(R_0,\lambda_0)]
       \cdot \frac{P(R_0,\lambda_{Ra}) \cdot P(R,\lambda_0)}{P(R_0,\lambda_0) \cdot P(R,\lambda_{Ra})}
       \cdot \frac{e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_{Ra}) + \alpha_{mol}(r,\lambda_{Ra})]dr}}
       {e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_0) + \alpha_{mol}(r,\lambda_0)]dr}} - \beta_{mol}(R,\lambda_0)

    References
    ----------
    Ansmann, A. et al. Combined Raman Elastic-Backscatter LIDAR for Vertical Profiling of Moisture, 
    Aerosol Extinction, Backscatter, and LIDAR Ratio.
    Applied Physics B 55, 18-28 (1992)
    """

    # Calculate profiles of molecular extinction
    alpha_mol_signal = molecular_extinction(raman_wavelength, pressure, temperature)
    alpha_mol_reference = molecular_extinction(reference_wavelength, pressure, temperature)
    
    
    number_density = number_density_at_pt(pressure, temperature)

    mixing_ratio = retrieve_raman_mixing_ratio(signal_raman, reference_raman, dz, alpha_aerosol_extinction,
                                                 calibration_const, raman_wavelength, reference_wavelength, 
                                                 number_density, alpha_mol_signal, alpha_mol_reference)

    return mixing_ratio


def retrieve_raman_mixing_ratio(signal_raman, reference_raman, dz, alpha_aerosol_extinction, 
                                calibration_const, signal_wavelength, reference_wavelength, 
                                number_density, alpha_molecular_signal, alpha_molecular_reference):
   r"""
    Calcula o mixing raiton de dois canais raman

    Parameters
    ----------
    signal_raman : (M,) array
       The range-corrected Raman signal. Should be 1D array of size M.
    reference_raman : (M, ) array
       The range-corrected Raman signal. Should be 1D array of size M.
    dz : float
       Altitude step, used in the integrals calculations [m]
    alpha_aerosol_extinction : (M,) array
       The aerosol extinction coefficient at each point of the signal profile for emission and raman wavelength.
    calibration_const : float
       Mixing ratio calibration constant.
    raman_wavelength : float
       Raman wavelength (nm)
    reference_wavelength : float
       Reference Raman wavelength (nm)
    number_density : (M,) array
       Number density profile (particles / m3)
    alpha_molecular_raman, alpha_mol_reference : (M,) array
      The molecular extinction coefficient at each point of the signal profile for emission and raman wavelength.

   Returns
   -------
   mixing_ration : arrays
       The mixing ration

   Notes
   -----
   TODO: Consertar isso aqui
   The aerosol backscatter coefficient is given by the formula:

   .. math::
      \beta_{aer}(R,\lambda_0) = [\beta_{aer}(R_0,\lambda_0) + \beta_{mol}(R_0,\lambda_0)]
      \cdot \frac{P(R_0,\lambda_{Ra}) \cdot P(R,\lambda_0)}{P(R_0,\lambda_0) \cdot P(R,\lambda_{Ra})}
      \cdot \frac{e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_{Ra}) + \alpha_{mol}(r,\lambda_{Ra})]dr}}
      {e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_0) + \alpha_{mol}(r,\lambda_0)]dr}} - \beta_{mol}(R,\lambda_0)

   References
   ----------
    Ansmann, A. et al. Combined Raman Elastic-Backscatter LIDAR for Vertical Profiling of Moisture, 
    Aerosol Extinction, Backscatter, and LIDAR Ratio.
    Applied Physics B 55, 18-28 (1992)
   """

   # TODO: Aplicar correção de alpha aerosol para comprimento de onda
   alpha_aerosol_signal = alpha_aerosol_extinction
   alpha_aerosol_reference = alpha_aerosol_extinction


   # Substitui NAN por zeros para evitar propagação na integração
   alpha_signal = np.nan_to_num(alpha_aerosol_signal + alpha_molecular_signal)
   alpha_reference = np.nan_to_num(alpha_aerosol_reference + alpha_molecular_reference)
   integral_alpha_signal = cumulative_trapezoid(alpha_signal, dx=dz, initial=0)
   integral_alpha_reference = cumulative_trapezoid(alpha_reference, dx=dz, initial=0)

   signal_ratio = signal_raman / reference_raman

   transmission_ratio = np.exp(integral_alpha_reference)/np.exp(integral_alpha_signal)
   
   mixing_ratio = calibration_const * signal_ratio * transmission_ratio

   return mixing_ratio
