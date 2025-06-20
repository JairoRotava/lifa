from os.path import expanduser, join, abspath
import re
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
#import atmospheric_lidar as atl
#from atmospheric_lidar import licelv2
from lifa import licelv2
from scipy.signal import find_peaks
from numpy import ones,vstack
from numpy.linalg import lstsq
import json
import argparse
import glob
import json
import fames.process


def process_emissions(filename, fdestination):

    #TODO: checar se arquivo é válido - tipo licel.
    lidar_data = licelv2.LicelFileV2(filename)
    flare_emissions = fames.process.emissions(files=[filename], calib = fames.process.calibrations)


    # Salva como JSON
    with open(fdestination, 'w', encoding='utf-8') as f:
        json.dump(flare_emissions, f, ensure_ascii=False, indent=4, default=str)


def process_licel(filename, fdestination, ce_cal=1, co2_cal=1, ch4_cal=1, n2_cal=1 ):

    #TODO: checar se arquivo é válido - tipo licel.
    lidar_data = licelv2.LicelFileV2(filename)
    # find peak
    co2_signal = lidar_data.channels['BT3_L1_P1'].data
    peak_bin = find_one_peak(co2_signal)
    margin = 15
    min_bin = peak_bin - margin
    max_bin = peak_bin + margin
    d_bin = max_bin - min_bin

    ch4_bkg = np.mean(lidar_data.channels['BT1_L1_P1'].data[:-d_bin])
    co2_bkg = np.mean(lidar_data.channels['BT3_L1_P1'].data[:-d_bin])
    n2_bkg = np.mean(lidar_data.channels['BT2_L1_P1'].data[:-d_bin])

    bin_width = lidar_data.channels['BT3_L1_P1'].bin_width

    # corrected signal
    ch4_corrected = np.subtract(lidar_data.channels['BT1_L1_P1'].data[min_bin:max_bin],ch4_bkg)
    co2_corrected = np.subtract(lidar_data.channels['BT3_L1_P1'].data[min_bin:max_bin], co2_bkg)
    n2_corrected = np.subtract(lidar_data.channels['BT2_L1_P1'].data[min_bin:max_bin], n2_bkg)
    distance =  [i*bin_width for i in range(min_bin,max_bin)]

    # Calculte Combustion eficienci CE
    ch4 = np.sum(ch4_corrected)
    co2 = np.sum(co2_corrected)
    #ce_cal = 1
    ce = 1/(1+ce_cal*ch4/co2)

    # Fit de linha para N2, sem o pico
    #TODO: ajustar os points por slices
    points = [(0,n2_corrected[0]),(1,n2_corrected[1]),(len(n2_corrected)-5, n2_corrected[-5]),(len(n2_corrected)-1, n2_corrected[-1])]
    x_coords, y_coords = zip(*points)
    A = vstack([x_coords,ones(len(x_coords))]).T
    m, c = lstsq(A, y_coords, rcond=None)[0]
    n2_baseline = np.fromfunction(lambda i: i*m + c, (len(n2_corrected),), dtype=float)

    # Razao de mistura
    #co2_cal = 1
    #ch4_cal = 1
    #n2_cal = 1

    rm_co2 = np.divide(co2_corrected, n2_baseline)
    rm_ch4 = np.divide(ch4_corrected, n2_baseline)
    rm_n2 = np.divide(n2_corrected, n2_baseline)

    nco2 = co2_cal * np.sum(rm_co2)
    nch4 = ch4_cal * np.sum(rm_ch4)


    data = {
        'source': lidar_data.file_name,
        'reference:': lidar_data.file_name,
        'start_time': lidar_data.start_time,
        'stop_time': lidar_data.stop_time,
        'laser_shots': lidar_data.laser1_shots,
        'detected_peak_bin': peak_bin,
        'bin_width': bin_width,
        'ce': ce,
        'nch4' : nch4,
        'nco2' : nco2,
        'n2_cal' : n2_cal,
        'ch4_cal' : ch4_cal,
        'co2_cal' : co2_cal,
        'bin_min' : int(min_bin),
        'bin_max' : int(max_bin),
        'co2_signal' : co2_corrected.tolist(),
        'ch4_signal' : ch4_corrected.tolist(),
        'n2_signal' : n2_corrected.tolist(),
        'distance' : distance

    }
    with open(fdestination, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)


def find_one_peak(x, width = 5):
    peaks, peaks_prop = find_peaks(x, width=(0, width))
    i = peaks_prop['prominences'].argmax()
    return peaks[i]



def read_processed(sources):
    row_list = []
    for source in sources:
        with open(source) as f:
            d = json.load(f)
            print(d['emissions'])
            row_list.append(d['emissions']
            #row_list.append({'file_name': f.name, 
            #                 'start_time': d['start_time'],
            #                 'stop_time': d['stop_time'],
            #                 'ce' : d['ce'],
            #                 'ch4' : d['ch4'],
            #                 'co2' : d['co2'],
            #                 'fluo' : d['fluo'],
            #                 'signals' : d['signals'],
            #                 'distance': d['distance']
            )
                                                                      
    df = pd.DataFrame(row_list)
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['stop_time'] = pd.to_datetime(df['stop_time'])
    df = df.sort_values(by='start_time', ignore_index=True)
    return df


if __name__ == "__main__":
    # recebe argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Process FAMES files')
    parser.add_argument('source', help="Source LICEL file")
    parser.add_argument('destination', help="Destination folder for processed data")
    parser.add_argument('-r','--recursive', action='store_true')
    args = parser.parse_args()


    if args.recursive:
        fdir = os.path.dirname(args.source)
        fname = os.path.basename(args.source)
        sources = glob.glob(os.path.join(fdir, '**',fname), recursive=True)
    else:
        sources = glob.glob(args.source, recursive=False)

    destination = glob.glob(args.destination)

    if not destination:
        print("Destination directory not found")
        exit()

    if not os.path.isdir(destination[0]):
        print("Destination directory not found")
        exit()

    destination = os.path.abspath(destination[0])


    for fname in sources:
        if os.path.isfile(fname):
            print("Processing {} ".format(fname), end='')
            fprocessed = os.path.join(destination,os.path.basename(fname) + '.fames')
            try:
                #process(fname, fprocessed)
                print('-> {}'.format(fprocessed))
            except:
                print('ERROR')
