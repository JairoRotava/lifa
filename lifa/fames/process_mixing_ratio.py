import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import math
from scipy.signal import find_peaks
from importlib import reload
import json
import pandas as pd


from lifa.licel import LicelLidarMeasurement
from lifa.processing import fit_checks
from lifa.processing import pre_processing
from lifa.processing import helper_functions
from lifa.processing import raman_mixing_ratio
from lifa.processing import raman_retrievals
from .files import group_files

default_config = {
    'zenith_angle': 12,
    'elevation': 0,
    'cross_talk_355_353': 160,
    'ch4_cal': 4000,
    'co2_cal': 26000,
    'ce_cal': 0.25,
    'fluo_cal': 100,
    'z_ref_idx': 96,
    'z_flare_idx': 106,
    'dead_time': 1/240,
    'background_min_idx': 12000,
    'background_max_idx' : 15000,
    'z_min_flare': 100,
    'z_max_flare': 700,
    'flare_roi': 10,
    'flare_pos': 400,
    'n2_raman': {'channel':'00353.o_an', 'bin_shift':0, 'lambda': 323},
    'rayleigh': {'channel':'00355.o_an', 'bin_shift':0, 'lambda': 355},
    'co2_raman': {'channel':'00371.o_ph', 'bin_shift':4, 'lambda': 371},
    'ch4_raman_s': {'channel':'00395.s_ph', 'bin_shift':4, 'lambda': 395},
    'ch4_raman_p': {'channel':'00395.p_ph', 'bin_shift':4, 'lambda': 395},
    'fluorescence': {'channel':'00460.o_an', 'bin_shift':1, 'lambda': 460},
    'n2_raman_b': {'channel':'00530.o_an', 'bin_shift':0, 'lambda': 530},
    'rayleigh_b': {'channel':'00532.o_an', 'bin_shift':0, 'lambda': 532},

}


def emissions(files, config=default_config):


    measurement_all = LicelLidarMeasurement(files)

    channels = ['n2_raman', 'rayleigh', 'co2_raman', 'ch4_raman_s', 'ch4_raman_p', 'fluorescence', 'n2_raman_b', 'rayleigh_b']

    # define z
    z = measurement_all.channels[config['rayleigh']['channel']].z

    bin_width = measurement_all.channels[config['rayleigh']['channel']].resolution

    # Pre processamento
    signal = {}
    for c in channels:
        temp = measurement_all.channels[config[c]['channel']]

        # Faz média e corrige dead time
        if temp.is_photon_counting:
            s = pre_processing.correct_count_rate_dead_time_nonparalyzable(temp.average_profile(),config['dead_time'])
        else:
            s = temp.average_profile()

        # Remove backgroun
        signal[c], bg_mean, bg_std = pre_processing.subtract_background(s, config['background_min_idx'], config['background_max_idx'])

        # Corrige bin shift
        signal[c] = pre_processing.correct_trigger_delay_bins(signal[c], config[c]['bin_shift'])

    # remove crosstalk do 355 no 353
    signal['n2_raman'] = signal['n2_raman'] - (signal['rayleigh']/config['cross_talk_355_353'])
  
    # Faz correção de range
    signal_rc = {}
    for key,val in signal.items():
        signal_rc[key] = pre_processing.apply_range_correction(val, z)

    # Calcula molecular a partir de atmosfera padrão
    elevation_angle = config['zenith_angle']
    elevation = config['elevation']
    bin_min = helper_functions.find_nearest(z, config['z_min_flare'])
    bin_max = helper_functions.find_nearest(z, config['z_max_flare'])
    height = z * math.sin(math.radians(elevation_angle)) + elevation 

    # Modelo Padrão Atmosfera
    pressure, temperature, density = helper_functions.standard_atmosphere(height)

    # Calcula extinction rate para aerosol a partir de sinal Raman
    #alpha_aer =  raman_retrievals.raman_extinction(signal_rc['n2_raman_353'],    # array sinal raman com range correction
    #                                bin_width,   # tamanho de cada bin em metros
    #                                355, # comprimento de onda do laser/rayleigh
    #                                353,    # comprimento de onda sinal raman
    #                                angstrom_aerosol=1,    # fator de relação. Geralmente por volta de 1
    #                                temperature=temperature,   # array com temperatura do ar
    #                                pressure=pressure,     # array com pressão do ar
    #                                window_size=5,     # deve ser algum tipo de janela para filtro
    #                                order = 4)         # ordem de algum tipo de filtro


    # O calculo de extinction rate por ramana não fica bom com o sinal Raman do N2. Usa tudo zero por enquanto
    alpha_aer = np.zeros_like(height)

    # co2 mixing ratio
    co2_mixing_ratio = raman_mixing_ratio.raman_mixing_ratio(signal_rc['co2_raman'], 
                                        signal_rc['n2_raman'], 
                                        bin_width, 
                                        alpha_aer, 
                                        config['co2_cal'], 
                                        config['co2_raman']['lambda'], 
                                        config['n2_raman']['lambda'], 
                                        pressure, 
                                        temperature)

    # ch4 mixing ratio
    ch4_mixing_ratio = raman_mixing_ratio.raman_mixing_ratio(signal_rc['ch4_raman_p'], 
                                        signal_rc['n2_raman'], 
                                        bin_width, 
                                        alpha_aer, 
                                        config['ch4_cal'], 
                                        config['ch4_raman_p']['lambda'], 
                                        config['n2_raman']['lambda'], 
                                        pressure, 
                                        temperature)
    
    # ce mixing ration
    ce_mixing_ratio = raman_mixing_ratio.raman_mixing_ratio(signal_rc['ch4_raman_p'], 
                                      signal_rc['co2_raman'], 
                                      bin_width, 
                                      alpha_aer, 
                                      config['ce_cal'], 
                                      config['ch4_raman_p']['lambda'],
                                      config['co2_raman']['lambda'],
                                      pressure, 
                                      temperature)
    ce = 1/(1 + ce_mixing_ratio) * 100

    # Fluorescence
    fluo_mixing_ratio = raman_mixing_ratio.raman_mixing_ratio(signal_rc['fluorescence'], 
                                      signal_rc['n2_raman'], 
                                      bin_width, 
                                      alpha_aer, 
                                      config['fluo_cal'], 
                                      config['fluorescence']['lambda'],
                                      config['n2_raman']['lambda'],
                                      pressure, 
                                      temperature)
    
    # Detecta pico se declarado como None, senão usa distancia fornecida
    min_distance_idx = bin_min
    max_distance_idx = bin_max
    if config['flare_pos'] is None:
        peaks, _ = find_peaks(signal['rayleigh'][min_distance_idx: max_distance_idx], width=1,  threshold=2)
        peak_idx =  peaks[0] + min_distance_idx
        pre_peak_idx = peak_idx - 10
    else:
        peak_idx = helper_functions.find_nearest(config['flare_pos'], z)
        pre_peak_idx = peak_idx - 10

    # Retira valores de CE, CO2, CH4 e fluorescencia do range definidos
    roi_bin_min = helper_functions.find_nearest(config['flare_pos'] - config['flare_roi'], z)
    roi_bin_max = helper_functions.find_nearest(config['flare_pos'] + config['flare_roi'], z)
    ce_peak = np.min(ce[roi_bin_min:roi_bin_max])
    ch4_peak = np.max(ch4_mixing_ratio[roi_bin_min:roi_bin_max])
    co2_peak = np.max(co2_mixing_ratio[roi_bin_min:roi_bin_max])
    fluo_peak = np.max(fluo_mixing_ratio[roi_bin_min:roi_bin_max])
    ce_m_peak = np.max(ce_mixing_ratio[roi_bin_min:roi_bin_max])
    





    output = {
        'start_time' : measurement_all.info['start_time'],
        'stop_time' : measurement_all.info['stop_time'],
        'duration' : measurement_all.info['duration'],
        'bin_width': bin_width,
        'cross_talk_355_353': config['cross_talk_355_353'],
        'ch4_cal': config['ch4_cal'],
        'co2_cal': config['co2_cal'],
        'ce_cal': config['ce_cal'],
        'fluo_cal': config['fluo_cal'],
        'z_ref': z[pre_peak_idx],
        'co2_ref': co2_mixing_ratio[pre_peak_idx],
        'ch4_ref': ch4_mixing_ratio[pre_peak_idx],
        'ce_ref': ce[pre_peak_idx],
        'ce_m_ref': ce_mixing_ratio[pre_peak_idx],
        'fluo_ref': fluo_mixing_ratio[pre_peak_idx],
        'z_flare': z[peak_idx],
        'z_min_roi': config['flare_pos'] - config['flare_roi'],
        'z_max_roi': config['flare_pos'] + config['flare_roi'],
        'co2': co2_peak,
        'ch4': ch4_peak,
        'ce': ce_peak,
        'ce_m': ce_m_peak,
        'fluo': fluo_peak,
        'z_trace': [z[min_distance_idx:max_distance_idx]],
        'ch4_mixing_trace': [ch4_mixing_ratio[min_distance_idx:max_distance_idx]],
        'co2_mixing_trace': [co2_mixing_ratio[min_distance_idx:max_distance_idx]],
        'ce_mixing_trace': [ce_mixing_ratio[min_distance_idx:max_distance_idx]],
        'ce_trace': [ce[min_distance_idx:max_distance_idx]],
        'fluo_mixing_trace': [fluo_mixing_ratio[min_distance_idx:max_distance_idx]],
        'n2_raman_trace': [signal['n2_raman'][min_distance_idx:max_distance_idx]],
        'rayleigh_trace': [signal['rayleigh'][min_distance_idx:max_distance_idx]],
        'co2_raman_trace': [signal['co2_raman'][min_distance_idx:max_distance_idx]],
        'ch4_raman_s_trace': [signal['ch4_raman_s'][min_distance_idx:max_distance_idx]],
        'ch4_raman_p_trace': [signal['ch4_raman_p'][min_distance_idx:max_distance_idx]],
        'fluorescence_trace': [signal['fluorescence'][min_distance_idx:max_distance_idx]],
        'rayleigh_b_trace': [signal['rayleigh_b'][min_distance_idx:max_distance_idx]],
        'n2_raman_b_trace': [signal['n2_raman_b'][min_distance_idx:max_distance_idx]],
        'number_of_files': len(measurement_all.files),
        'files': [measurement_all.files],
    }


    df = pd.DataFrame.from_dict(output)
    return(df)


def emissions_group(files, config=default_config, step=1, size=1):
    group = group_files(files, step, size)
    results = []
    for f in group:
        df = emissions(f, config)
        results.append(df)
    output = pd.concat(results, ignore_index=True)
    return output
    
