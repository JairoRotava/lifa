""" Retrievals of backscatter and extinction based on Raman measurements

.. warning::
   These functions have not been tested!
"""
import numpy as np
import scipy

from scipy.signal import savgol_filter

from .helper_functions import molecular_extinction, molecular_backscatter, number_density_at_pt, poly_evaluate_window
from .elastic_retrievals import _integrate_from_reference


def raman_extinction(signal, dz, emission_wavelength, raman_wavelength, angstrom_aerosol, temperature, pressure,
                     window_size, order):
    r"""
    Calculates the aerosol extinction coefficient based on pre-processed Raman signals and molecular profiles.

    The derivative is calculated using a Savitzky-Golay filter.

    Parameters
    ----------
    signal : (M,) array
       The range_corrected molecular signal. Should be 1D array of size M.
    dz : float
       Altitude step, used in the derivative [m]
    emission_wavelength, raman_wavelength : float
       The emission and detection wavelengths [nm]
    angstrom_aerosol : float
       The aerosol Angstrom exponent.
    temperature : (M,) array
       Atmospheric temperature profile, same shape as the lidar signal [Kelvin]
    pressure : (M,) array
       Atmospheric pressure profile, same shape as the lidar signal [Pa]
    window_size : int
       the length of the smoothing window. Must be an odd integer number.
    order : int
       The order of the polynomial used in the filtering.
       Must be less then `window_size` - 1.

    Returns
    -------
    alpha_aer : arrays
       The aerosol extinction coefficient [m-1]
       
    Notes
    -----
    The aerosol extinction coefficient is given by the formula:
    
    .. math::
       \alpha_{aer}(R,\lambda_0) = \frac{\frac{d}{dR}ln[\frac{N_{Ra}(R)}
       {S(R,\lambda_{Ra})}] - \alpha_{mol}(R,\lambda_0) - \alpha_{mol}(R,\lambda_{Ra})}
       {[1 + (\frac{\lambda_0}{\lambda_{Ra}})^{\alpha(R)}]}

    References
    ----------
    Ansmann, A. et al. Independent measurement of extinction and backscatter profiles
    in cirrus clouds by using a combined Raman elastic-backscatter lidar.
    Applied Optics Vol. 31, Issue 33, pp. 7113-7131 (1992)    
    """
    # Calculate profiles of molecular extinction

    # pressure_pa = pressure * 100  # From hPa to Pa

    alpha_molecular_emission = molecular_extinction(emission_wavelength, pressure, temperature)
    alpha_molecular_raman = molecular_extinction(raman_wavelength, pressure, temperature)

    # Calculate number density of the target molecule
    number_density = number_density_at_pt(pressure, temperature)

    alpha_aer = retrieve_raman_extinction(signal, dz, emission_wavelength, raman_wavelength, alpha_molecular_emission,
                                          alpha_molecular_raman, angstrom_aerosol, number_density, window_size, order)

    return alpha_aer


def retrieve_raman_extinction(signal, dz, emission_wavelength, raman_wavelength, alpha_molecular_emission,
                              alpha_molecular_raman, angstrom_aerosol, number_density, window_size, order):
    """ Calculates the aerosol extinction coefficient based on pre-processed Raman signals and molecular profiles.

    The derivative is calculated using a Savitzky-Golay filter.

    Parameters
    ----------
    signal : (M,) array
       The range-corrected molecular signal. Should be 1D array of size M.
    dz : float
       Altitude step, used in the derivative [m]
    emission_wavelength, raman_wavelength : float
       The emission and detection wavelength [nm]
    alpha_molecular_emission, alpha_molecular_raman : (M,) array
       The molecular extinction coefficient at each point of the signal profile for emission and Raman wavelength.
    number_density : (M,) array
       The number density of the scattering molecule. E.g. the number density of N2 particles for typical Raman systems.
    angstrom_aerosol: float
       The aerosol Angstrom exponent.
    window_size : int
       the length of the smoothing window. Must be an odd integer number.
    order : int
       The order of the polynomial used in the filtering.
       Must be less then `window_size` - 1.

    Returns
    -------
    alpha_aer: arrays
       The aerosol extinction coefficient [m-1]
    """

    # Ratio to apply derivative
    ratio = np.ma.log(number_density / signal)

    derivative = savgol_filter(ratio, window_size, order, deriv=1, delta=dz,
                               mode='nearest')  # Calculate 1st derivative

    alpha_aer = (derivative - alpha_molecular_emission - alpha_molecular_raman) / (
            1 + (emission_wavelength / float(raman_wavelength)) ** angstrom_aerosol)

    return alpha_aer


def raman_backscatter(signal_raman, signal_emission, dz, reference_idx, alpha_aerosol_emission, angstrom_aerosol,
                      elastic_wavelength, raman_wavelength, pressure, temperature, beta_aer_ref=0,
                      reference_window_size=1, component='total'):
    r"""
    Calculates the aerosol backscatter coefficient based on:
    * Preprocessed elastic & raman signals.
    * The retrieved aerosol extinction coefficient.

    Parameters
    ----------
    signal_raman : (M,) array
       The range-corrected Raman signal. Should be 1D array of size M.
    signal_emission : (M, ) array
       The range-corrected elastic signal (at the emission wavelength). Should be 1D array of size M.
    dz : float
       Altitude step, used in the integrals calculations (m)
    reference_idx : int
       It is the index of the reference altitude to find into arrays the quantity (for example the signal) at the
       reference altitude.
    alpha_aerosol_emission : (M,) array
       The aerosol extinction coefficient at each point of the signal profile for emission and Raman wavelength.
    angstrom_aerosol : float
       Aerosol angstrom exponent.
    elastic_wavelength : float
       Elastic wavelength (nm)
    raman_wavelength : float
       Raman wavelength (nm)
    pressure : (M, ) array
        Atmosphere pressure profile, same as shape as the lidar signal (Pa)
    temperature : (M, ) array
        Atmosphere temperature profile, same as shape as the lidar signal (K)
    beta_aer_ref : float
        The molecular backscatter coefficient at reference altitude.
    reference_window_size : int
        The symmetrical window size used for the reference value, it should be an odd positive integer.
    component : str
        Molecular backscatter component detected. One of 'total' or 'cabannes'.

    Returns
    -------
    backscatter_raman_aer : arrays
        The aerosol  backscatter coefficient [m-1]

    Notes
    -----
    The aerosol backscatter coefficient is given by the formula:

    .. math::
       \beta_{aer}(R,\lambda_0) = [\beta_{aer}(R_0,\lambda_0) + \beta_{mol}(R_0,\lambda_0)]
       \cdot \frac{P(R_0,\lambda_{Ra}) \cdot P(R,\lambda_0)}{P(R_0,\lambda_0) \cdot P(R,\lambda_{Ra})}
       \cdot \frac{e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_{Ra}) + \alpha_{mol}(r,\lambda_{Ra})]dr}}
       {e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_0) + \alpha_{mol}(r,\lambda_0)]dr}} - \beta_{mol}(R,\lambda_0)

    References
    ----------
    Ansmann, A. et al. Independent measurement of extinction and backscatter profiles
    in cirrus clouds by using a combined Raman elastic-backscatter lidar.
    Applied Optics Vol. 31, Issue 33, pp. 7113-7131 (1992)
    """

    # Calculate profiles of molecular extinction
    alpha_mol_emmision = molecular_extinction(elastic_wavelength, pressure, temperature)
    beta_mol_emmision = molecular_backscatter(elastic_wavelength, pressure, temperature, component=component)

    alpha_mol_raman = molecular_extinction(raman_wavelength, pressure, temperature)

    number_density = number_density_at_pt(pressure, temperature)

    backscatter_aer = retrieve_raman_backscatter(signal_raman, signal_emission, dz, alpha_aerosol_emission,
                                                 angstrom_aerosol, elastic_wavelength, raman_wavelength, reference_idx,
                                                 number_density, alpha_mol_emmision, alpha_mol_raman,
                                                 beta_mol_emmision, beta_aer_ref, reference_window_size)

    return backscatter_aer


def retrieve_raman_backscatter(signal_raman, signal_emission, dz, alpha_aerosol_emission, angstrom_aerosol,
                               elastic_wavelength, raman_wavelength, reference_idx, number_density,
                               alpha_molecular_emmision, alpha_molecular_raman, beta_molecular_emmision, beta_aer_ref=0,
                               reference_window_size=1):
    """
    Calculates the aerosol backscatter coefficient based on:
    * Preprocessed elastic & raman signals.
    * The retrieved aerosol extinction coefficient.

    Parameters
    ----------
    signal_raman : (M,) array
       The range-corrected Raman signal. Should be 1D array of size M.
    signal_emission : (M, ) array
       The range-corrected elastic signal (at the emission wavelength). Should be 1D array of size M.
    dz : float
       Altitude step, used in the integrals calculations [m]
    alpha_aerosol_emission : (M,) array
       The aerosol extinction coefficient at each point of the signal profile for emission and raman wavelength.
    angstrom_aerosol : float
       Aerosol angstrom exponent.
    elastic_wavelength : float
       Elastic wavelength (nm)
    raman_wavelength : float
       Raman wavelength (nm)
    reference_idx : int
       It is the index of the reference altitude to find into arrays the quantity (for example the signal) at the
       reference altitude.
    number_density : (M,) array
       Number density profile (particles / m3)
    alpha_molecular_emission, alpha_mol_raman : (M,) array
      The molecular extinction coefficient at each point of the signal profile for emission and raman wavelength.
   backscatter_molecules : (M, ) array
      The altitude range depended backscatter coefficient from molecules (m-1 sr-1)
   alpha_molecular_emission, alpha_molecular_raman : (M,) array
      The molecular extinction coefficient at each point of the signal profile for emission and raman wavelengths.
   pressure : (M, ) array
      Atmosphere pressure profile, same as shape as the lidar signal (Pa)
   temperature : (M, ) array
      Atmosphere temperature profile, same as shape as the lidar signal (K)
   beta_aer_ref : float
      The molecular backscatter coefficient at reference altitude.
   reference_window_size : int
      The symmetrical window size used for the reference value, it should be an odd positive integer.


   Returns
   -------
   backscatter_raman_aer : arrays
       The aerosol  backscatter coefficient [m-1]

   Notes
   -----
   The aerosol backscatter coefficient is given by the formula:

   .. math::
      \beta_{aer}(R,\lambda_0) = [\beta_{aer}(R_0,\lambda_0) + \beta_{mol}(R_0,\lambda_0)]
      \cdot \frac{P(R_0,\lambda_{Ra}) \cdot P(R,\lambda_0)}{P(R_0,\lambda_0) \cdot P(R,\lambda_{Ra})}
      \cdot \frac{e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_{Ra}) + \alpha_{mol}(r,\lambda_{Ra})]dr}}
      {e^{-\int_{R_0}^{R} [\alpha_{aer}(r,\lambda_0) + \alpha_{mol}(r,\lambda_0)]dr}} - \beta_{mol}(R,\lambda_0)

   References
   ----------
   Ansmann, A. et al. Independent measurement of extinction and backscatter profiles
   in cirrus clouds by using a combined Raman elastic-backscatter lidar.
   Applied Optics Vol. 31, Issue 33, pp. 7113-7131 (1992)
   """
    alpha_aer_raman = alpha_aerosol_emission * (raman_wavelength / elastic_wavelength) ** -angstrom_aerosol

    # TODO: substitute this with proper molecular profile fitting
    if reference_window_size > 1:
        window_offset = int(np.floor(reference_window_size / 2))
        ref_raman = poly_evaluate_window(signal_raman[reference_idx - window_offset:reference_idx + window_offset + 1])
        ref_emission = poly_evaluate_window(
            signal_emission[reference_idx - window_offset:reference_idx + window_offset + 1])
    else:
        ref_raman = signal_raman[reference_idx]
        ref_emission = signal_emission[reference_idx]

    signal_ratio = ref_raman * signal_emission * number_density / (
            ref_emission * signal_raman * number_density[reference_idx])

    alpha_tot_emission = alpha_molecular_emmision + alpha_aerosol_emission
    alpha_tot_raman = alpha_molecular_raman + alpha_aer_raman

    integral_raman = _integrate_from_reference(alpha_tot_raman, reference_idx, dz)
    integral_emission = _integrate_from_reference(alpha_tot_emission, reference_idx, dz)

    transmission_ratio = np.exp(integral_emission - integral_raman)

    parameter = beta_aer_ref + beta_molecular_emmision[reference_idx]

    backscatter_aer = - beta_molecular_emmision + (parameter * signal_ratio * transmission_ratio)

    return backscatter_aer
