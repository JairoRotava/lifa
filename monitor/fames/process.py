# Processamento dos sinais

import numpy as np
import matplotlib.pyplot as plt
#from atmospheric_lidar import licelv2
import glob
import os
#from atmospheric_lidar.licel import LicelLidarMeasurement
from lifa.licel import LicelLidarMeasurement
import json


# Parametros de calibração
calibrations = {
    'crosstalk_355_ref': 150,           # valor de crosstalk de 355 nm no sinal de 353 nm
    'g_co2': 3e6,                       # ganho do canal 371
    'crosstalk_fluo_co2': 0,            # crosstalk da fluorescencia no 371
    'g_ch4': 0.5e6,                     # ganho do canal 395 nm
    'crosstalk_fluo_ch4': 0,            # crosstalk da fluorescencia no 395 nm
    'g_sp_ch4': 0,                      # fator de correção entre 395p e 395 s. A ideia é que um tem fluorescencia+raman e outro somente fluorescencia
    'g_ce_relative': 0.16,              # fator de correção para ce calculado diretamente por 1/(1 +(g * raman ch4/raman co2))
    'pre_flare_bins': (80,100),         # região antes do flare para uso de referencia
    'post_flare_bins': (120,140),       # região após flare e oscilação pmt para referência
    'flare_bins': (104,109),            # posição do flare
    'background_bins': (15000, 16000),  # região onde é calculado background do sinal
    'correction_factor_co2': 1,         # fator de correção devido limitação resolução espacial para CO2
    'correction_factor_ch4': 1,         # fator de correção devido limitação resolução espacial para CH4
    'correction_factor_fluo': 1         # fator de correção devido limitação resolução espacial para FLUO
}

def emissions(files, calib):


    measurement_all = LicelLidarMeasurement(files)
    licel_channels_names = ['00355.o_an', '00353.o_an',  '00371.o_an', '00395.s_an', '00395.p_an', '00460.o_an', '00532.o_an', '00530.o_an']
    licel_channels_id = {k: v for v, k in enumerate(licel_channels_names)}
    measurement = measurement_all.subset_by_channels(licel_channels_names)

    # Range correction
    for channel in licel_channels_names:
        measurement.channels[channel].calculate_rc()

    # Build raw signal and range corrected matrix
    raw_signal = []
    rc_signal = []
    distance = []
    hv = []
    start_time = []
    stop_time = []
    for channel in licel_channels_names:
        raw_signal.append(np.mean(measurement.channels[channel].matrix, axis=0))
        rc_signal.append(np.mean(measurement.channels[channel].rc, axis=0))
        distance.append(measurement.channels[channel].z)
        hv.append(measurement.channels[channel].hv)
        start_time.append(measurement.channels[channel].start_time)
        stop_time.append(measurement.channels[channel].stop_time)


    raw_signal =np.array(raw_signal)
    rc_signal = np.array(rc_signal)
    # assume distance is the same for all channels
    distance = np.array(distance)[0]
    # assume voltage is the same all files
    hv = np.array(hv)[:,0]
    # Asssume start/stop time is the same all channels and files
    start_time = start_time[0]
    stop_time = stop_time[0]

    # raw_signal é melhor que range corrected pq evidencia sinais mais próximos do lidar. Melhor para visualizar pequenos sinais
    # Retira background
    signal = raw_signal
    #bin_min = -1000
    #bin_max = -500
    background_bins = calib['background_bins']
    background = np.mean(raw_signal[:,background_bins], axis=1)
    signal = np.transpose(np.transpose(raw_signal) - background)

    #clipa na região de interesse
    pre_flare_bins = calib['pre_flare_bins']
    post_flare_bins = calib['post_flare_bins']
    subset_min = pre_flare_bins[0]
    subset_max = post_flare_bins[1]
    signal_subset = signal[:,subset_min:subset_max]
    distance_subset = distance[subset_min:subset_max]
    bins_subset = np.arange(subset_min, subset_max)

    # Calcula sinal de referencia
    # Avaliação de crosstalk entre 355 e 352. Ver que exite influencia. O mesmo não ocorre em 532 e 530 nm.
    #bin_shift = 0
    #crosstalk = 150
    crosstalk = calib['crosstalk_355_ref']

    ref_signal = signal_subset[licel_channels_id['00353.o_an']] - (1/crosstalk)*signal_subset[licel_channels_id['00355.o_an']]

    # Seleciona região da curva para fitting. Pegar depois de pico
    #bin_min = None
    #bin_max = None
    #fit_idx = np.concatenate((x[:2], x[-2:]))
    #xfit = distance_subset[bin_min:bin_max]
    pre_len = pre_flare_bins[1] - pre_flare_bins[0]
    post_len = post_flare_bins[1] - post_flare_bins[0]
    
    # região de fitting é somente pre e post flame
    xfit = np.concatenate( (distance_subset[:pre_len], distance_subset[-post_len:]) )
    ydata = np.concatenate( (ref_signal[:pre_len], ref_signal[-post_len:]) )



    #ydata = ref_signal[bin_min:bin_max]


    z = np.polyfit(xfit, ydata, 10)
    f = np.poly1d(z)

    fit_ref = f(distance_subset)

    # Fluorescencia
    # Fluorescence indicator 460/ref
    fluo = signal_subset[licel_channels_id['00460.o_an']]/fit_ref

    # CO2 = (371)/ref
    #gco2 = 3e6
    gco2 = calib['g_co2']
    #gfluo_co2 = 0.00235
    #gfluo_co2 = 0.0
    gfluo_co2 = calib['crosstalk_fluo_co2']
    co2 = gco2*((signal_subset[licel_channels_id['00371.o_an']])/fit_ref - gfluo_co2*fluo)

    # CO2 = (371)/ref
    #gch4 = 0.5e6
    gch4 = calib['g_ch4']
    #gdif_ch4 = 0
    gdif_ch4 = calib['g_sp_ch4']
    #gfluo_ch4 = 0
    gfluo_ch4 = calib['crosstalk_fluo_ch4']

    # Forma 1
    ch4_1 = gch4*((signal_subset[licel_channels_id['00395.p_an']] - gdif_ch4*signal_subset[licel_channels_id['00395.s_an']])/fit_ref)
    # Forma 2
    ch4_2 = gch4*(signal_subset[licel_channels_id['00395.p_an']]/fit_ref - gfluo_ch4*fluo)

    ch4= ch4_1

    #ce = 1 /(1 + ch4/(co2 + ch4))
    ce_1 = co2/(co2 + ch4)
    g_ce_rel = 0.16
    ce_2 = 1/(1 + (g_ce_rel*signal_subset[licel_channels_id['00395.p_an']]/signal_subset[licel_channels_id['00371.o_an']]))

    ce = ce_1

    flare_bins = calib['flare_bins']
    rel_idx_min = flare_bins[0] - subset_min
    rel_idx_max = flare_bins[1] - subset_min
    flare_co2 = calib['correction_factor_co2']*np.mean(co2[rel_idx_min:rel_idx_max])
    flare_ch4 = calib['correction_factor_ch4']*np.mean(ch4[rel_idx_min:rel_idx_max])
    flare_ce = flare_co2/(flare_ch4 + flare_co2)
    flare_ce_rel = np.mean(ce_2[rel_idx_min:rel_idx_max])
    flare_fluo = calib['correction_factor_fluo']*np.mean(fluo[rel_idx_min:rel_idx_max])

    rel_idx_min = 0
    rel_idx_max = pre_flare_bins[1] - subset_min
    pre_flare_co2 = np.mean(co2[rel_idx_min:rel_idx_max])
    pre_flare_ch4 = np.mean(ch4[rel_idx_min:rel_idx_max])
    pre_flare_ce = pre_flare_co2/(pre_flare_ch4 + pre_flare_co2)
    pre_flare_ce_rel = np.mean(ce_2[rel_idx_min:rel_idx_max])
    pre_flare_fluo = np.mean(fluo[rel_idx_min:rel_idx_max])

    output = {
        'diagnostics' :
        {
            'calibrations': calib,
            'files': files,
            'channels': licel_channels_names,
            'hv': hv,
            'signal': signal,
            'background': background,
            'reference': ref_signal,
            'fitting': fit_ref,
            'fluorescence': fluo,
            'co2': co2,
            'ch4': ch4,
            'ce': ce,
            'ce_rel': ce_2,
            'distances': distance,
            'start_time': start_time,
            'stop_time': stop_time
        },
        'pre_flare' : {
            'co2': pre_flare_co2,
            'ch4': pre_flare_ch4,
            'ce': pre_flare_ce,
            'ce_rel' : pre_flare_ce_rel, 
            'fluo': pre_flare_fluo,
        },
        'flare' : {
            'co2': flare_co2,
            'ch4': flare_ch4,
            'ce': flare_ce,
            'ce_rel': flare_ce_rel,
            'fluo': flare_fluo,
        },
        'emissions' : {
            'file_name': files, 
            'start_time': start_time,
            'stop_time': stop_time,
            'ce' : flare_ce,
            'ch4' : flare_ch4,
            'co2' : flare_co2,
            'fluo' : flare_fluo,
            'signals' : signal_subset.tolist(),
            'distances': distance_subset.tolist(),
            'bins': bins_subset.tolist(),
            'channels' : licel_channels_names
        },
    }

    return output




#flare_emissions = emissions(files=files[:], calib = calibrations)