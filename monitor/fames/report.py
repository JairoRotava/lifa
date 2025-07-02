import glob
import os
import json
import pandas as pd

import matplotlib.pyplot as plt
import numpy as np

from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import argparse


import json

def signal(df, measurement_id = 0):

    # Faz relatorio da aquisiçção

    ch4 = df.iloc[measurement_id]['ch4_signal']
    co2 = df.iloc[measurement_id]['co2_signal']
    n2 = df.iloc[measurement_id]['n2_signal']
    dist = df.iloc[measurement_id]['distance']

    nch4 = df['nch4']
    nco2 = df['nco2']
    ce = df['ce']

    time = df['start_time']



    # Apresenta sinal Lidar
    # Create figure and subplot manually
    # fig = plt.figure()
    # host = fig.add_subplot(111)

    # More versatile wrapper

    #fig, host = plt.subplots(figsize=(8,5), layout='constrained') # (width, height) in inches
    cm = 1/2.54
    fig, axes = plt.subplots(1, 1, figsize=(8,5), layout='constrained') # (width, height) in inches

    host = axes
    ax1 = host


    #plt.savefig(os.path.join(data_directory,'report.pdf'), bbox_inches='tight')

    # (see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html and
    # .. https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html)
        
    #ax2 = host.twinx()
    #ax3 = host.twinx()


        
    #host.set_xlim(0, None)
    host.set_ylim(-0.01, 0.3)
    #ax2.set_ylim(-0.01, 0.3)
    #ax3.set_ylim(0, 30)
        
    #host.set_xlabel("BIN")
    host.set_xlabel("distance (m)")
    host.set_ylabel("CH4 (ppm)")
    #ax2.set_ylabel("CO2 (ppm)")
    #ax3.set_ylabel("REF (a.u.)")

    color1, color2, color3 = plt.cm.viridis([0, .5, .9])

    p1 = host.plot(dist, ch4, color=color1, label="CH4", marker='o', linestyle=':')
    p2 = ax1.plot(dist, co2, color=color2, label="CO2", marker='o', linestyle=':')
    p3 = ax1.plot(dist, n2, color=color3, label="REF (a.u.)", marker='o', linestyle=':')
    plt.title("lidar signals")

    host.legend(handles=p1+p2+p3, loc='best')

    # right, left, top, bottom
    #ax3.spines['right'].set_position(('outward', 60))

    # no x-ticks                 
    #host.xaxis.set_ticks([])

    # Alternatively (more verbose):
    # host.tick_params(
    #     axis='x',          # changes apply to the x-axis
    #     which='both',      # both major and minor ticks are affected
    #     bottom=False,      # ticks along the bottom edge are off)
    #     labelbottom=False) # labels along the bottom edge are off
    # sometimes handy:  direction='in'    

    # Move "Velocity"-axis to the left
    # ax3.spines['left'].set_position(('outward', 60))
    # ax3.spines['left'].set_visible(True)
    # ax3.spines['right'].set_visible(False)
    # ax3.yaxis.set_label_position('left')
    # ax3.yaxis.set_ticks_position('left')

    host.yaxis.label.set_color(p1[0].get_color())
    #ax2.yaxis.label.set_color(p2[0].get_color())
    #ax3.yaxis.label.set_color(p3[0].get_color())

    #plt.show()

    # Historico da razão de mistura e CE
    # Create figure and subplot manually
    # fig = plt.figure()
    # host = fig.add_subplot(111)

    # More versatile wrapper
    #fig, host = plt.subplots(figsize=(8,5), layout='constrained') # (width, height) in inches

    return axes


def generate(df, measurement_id = -1):

    # Faz relatorio da aquisiçção

    ch4 = df.iloc[measurement_id]['ch4_signal']
    co2 = df.iloc[measurement_id]['co2_signal']
    n2 = df.iloc[measurement_id]['n2_signal']
    dist = df.iloc[measurement_id]['distance']

    nch4 = df['nch4']
    nco2 = df['nco2']
    ce = df['ce']

    time = df['start_time']



    # Apresenta sinal LIdar
    # Create figure and subplot manually
    # fig = plt.figure()
    # host = fig.add_subplot(111)

    # More versatile wrapper

    #fig, host = plt.subplots(figsize=(8,5), layout='constrained') # (width, height) in inches
    cm = 1/2.54
    fig, axes = plt.subplots(3, 1, figsize=(18*cm,29.7*cm), layout='constrained') # (width, height) in inches



    #histograma CE
    #fig, axs = plt.subplots(figsize=(8,5), layout='constrained')
    axs = axes[0]
    n_bins = np.arange(-0.1, 1.1, 0.01)
    # We can set the number of bins with the *bins* keyword argument.
    axs.hist(ce, bins=n_bins, rwidth=0.9)
    axs.set_xlabel("CE")
    #axs.yaxis.set_ticks([])
    #axs.set_xlim([0.5, 1])
    axs.set_title("CE histogram")

    # escreve info da aquisição

    #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    #textstr = "info\ndir:{}\nmeas:{}\nnshots:{}\nstart:{}\nstop:{}".format(data_directory, df.shape[0], laser_shots, df['start_time'].min(),df['start_time'].max())
    #axs.text(1, 1, textstr, fontsize=8,verticalalignment='top', bbox=props)

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    textstr = ("info\n"
            "Numero de medidas:{}\n"
            "Hora inicio:{}\n"
            "Hora fim:{}").format(df.shape[0], df['start_time'].min(),df['start_time'].max())
    axs.text(0, 1.5, textstr, transform=axs.transAxes, fontsize=8,verticalalignment='top', bbox=props)



    host=axes[1]
    # (see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html and
    # .. https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html)
        
    ax2 = host.twinx()
    ax3 = host.twinx()
        
    #host.set_xlim(0, None)
    #host.set_ylim(0, 0.1)
    #ax2.set_ylim(0, 0.1)
    #ax3.set_ylim(0, 1)
        
    #host.set_xlabel("BIN")
    host.set_xlabel("datetime")
    host.set_ylabel("CH4 (ppm)")
    ax2.set_ylabel("CO2 (ppm)")
    ax3.set_ylabel("CE (%)")

    color1, color2, color3 = plt.cm.viridis([0, .5, .9])

    p1 = host.plot(time, nch4, color=color1, label="CH4", marker='o', linestyle=':')
    p2 = ax2.plot(time, nco2, color=color2, label="CO2", marker='o', linestyle=':')
    p3 = ax3.plot(time, ce, color=color3, label="CE", marker='o', linestyle=':')
    host.set_title("History")

    host.legend(handles=p1+p2+p3, loc='best')

    # right, left, top, bottom
    ax3.spines['right'].set_position(('outward', 60))

    # no x-ticks                 
    #host.xaxis.set_ticks([])

    # Alternatively (more verbose):
    # host.tick_params(
    #     axis='x',          # changes apply to the x-axis
    #     which='both',      # both major and minor ticks are affected
    #     bottom=False,      # ticks along the bottom edge are off)
    #     labelbottom=False) # labels along the bottom edge are off
    # sometimes handy:  direction='in'    

    # Move "Velocity"-axis to the left
    # ax3.spines['left'].set_position(('outward', 60))
    # ax3.spines['left'].set_visible(True)
    # ax3.spines['right'].set_visible(False)
    # ax3.yaxis.set_label_position('left')
    # ax3.yaxis.set_ticks_position('left')

    host.yaxis.label.set_color(p1[0].get_color())
    ax2.yaxis.label.set_color(p2[0].get_color())
    ax3.yaxis.label.set_color(p3[0].get_color())

    host = axes[2]


    #plt.savefig(os.path.join(data_directory,'report.pdf'), bbox_inches='tight')

    # (see https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html and
    # .. https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html)
        
    ax2 = host.twinx()
    ax3 = host.twinx()


        
    #host.set_xlim(0, None)
    host.set_ylim(-0.01, 0.3)
    ax2.set_ylim(-0.01, 0.3)
    ax3.set_ylim(0, 30)
        
    #host.set_xlabel("BIN")
    host.set_xlabel("distance (m)")
    host.set_ylabel("CH4")
    ax2.set_ylabel("CO2")
    ax3.set_ylabel("N2")

    color1, color2, color3 = plt.cm.viridis([0, .5, .9])

    p1 = host.plot(dist, ch4, color=color1, label="CH4", marker='o', linestyle=':')
    p2 = ax2.plot(dist, co2, color=color2, label="CO2", marker='o', linestyle=':')
    p3 = ax3.plot(dist, n2, color=color3, label="N2", marker='o', linestyle=':')
    plt.title("lidar signal corrected")

    host.legend(handles=p1+p2+p3, loc='best')

    # right, left, top, bottom
    ax3.spines['right'].set_position(('outward', 60))

    # no x-ticks                 
    #host.xaxis.set_ticks([])

    # Alternatively (more verbose):
    # host.tick_params(
    #     axis='x',          # changes apply to the x-axis
    #     which='both',      # both major and minor ticks are affected
    #     bottom=False,      # ticks along the bottom edge are off)
    #     labelbottom=False) # labels along the bottom edge are off
    # sometimes handy:  direction='in'    

    # Move "Velocity"-axis to the left
    # ax3.spines['left'].set_position(('outward', 60))
    # ax3.spines['left'].set_visible(True)
    # ax3.spines['right'].set_visible(False)
    # ax3.yaxis.set_label_position('left')
    # ax3.yaxis.set_ticks_position('left')

    host.yaxis.label.set_color(p1[0].get_color())
    ax2.yaxis.label.set_color(p2[0].get_color())
    ax3.yaxis.label.set_color(p3[0].get_color())

    #plt.show()

    # Historico da razão de mistura e CE
    # Create figure and subplot manually
    # fig = plt.figure()
    # host = fig.add_subplot(111)

    # More versatile wrapper
    #fig, host = plt.subplots(figsize=(8,5), layout='constrained') # (width, height) in inches

    return axes

    #plt.savefig(os.path.join(data_directory,'report.pdf'), bbox_inches='tight')

def plot_signal(axes, df, measurement_id = 0):

    #print(axes)

    ax1 = axes[0]
    #ax2 = axes[1]
    #ax3 = axes[2]

    ax1.cla()
    #ax2.cla()
    #ax2.yaxis.set_label_position('right')
    #ax3.cla()
    #ax3.yaxis.set_label_position('right')

    # Faz relatorio da aquisiçção

    #ch4 = df.iloc[measurement_id]['ch4_signal']
    #co2 = df.iloc[measurement_id]['co2_signal']
    #n2 = df.iloc[measurement_id]['n2_signal']
    #dist = df.iloc[measurement_id]['distance']

    #ch4 = [0, 1]
    #co2 = [0, 1]
    #n2 = [0, 1]
    #dist = [0, 1]

       
    #host.set_xlim(0, None)
    #ax1.set_ylim(-0.01, 0.3)
    #ax2.set_ylim(-0.01, 0.3)
    #ax3.set_ylim(0, 30)
        
    #ax1.set_ylim(0, None)

    #host.set_xlabel("BIN")
    ax1.set_xlabel("bin")
    #ax1.set_ylabel("CH4 (ppm)")
    #ax2.set_ylabel("CO2 (ppm)")
    #ax3.set_ylabel("REF")

    ax1.set_ylabel("(mV)")

    ax1.minorticks_on()
    ax1.grid(which='both')
    

    color1, color2, color3 = plt.cm.viridis([0, .5, .9])

    ax1.set_yscale('log')

    distances = df['bins'][measurement_id]
    signals = df['signals'][measurement_id]
    channels_names = df['channels'][measurement_id]

    #print('xx')
    #print(type(distances)) 
    #print(channels_names)

    p1 = ax1.plot(distances, np.transpose(signals), label = channels_names)
    #p2 = ax1.plot(dist, co2, color=color2, label="CO2", marker='o', linestyle=':')
    #p3 = ax1.plot(dist, n2, color=color3, label="REF", marker='o', linestyle=':')
    ax1.set_title("Signals")

    ax1.legend(p1, channels_names,  loc='upper right')
    #ax1.legend(handles=p1, loc='upper right')


    # right, left, top, bottom
    #ax3.spines['right'].set_position(('outward', 60))

    ax1.yaxis.label.set_color(p1[0].get_color())
    #ax2.yaxis.label.set_color(p2[0].get_color())
    #ax3.yaxis.label.set_color(p3[0].get_color())

def plot_histogram(ax, df):
    
    ax.cla()
    ce = ce = df['ce']
    n_bins = np.arange(0.5, 1.1, 0.01)
    # We can set the number of bins with the *bins* keyword argument.
    ax.hist(ce, bins=n_bins, rwidth=0.9)
    ax.set_xlabel("CE")
    #axs.yaxis.set_ticks([])
    #axs.set_xlim([0.5, 1])
    ax.set_title("Histogram")

def plot_history(axes, df, highlight = None):

    ch4 = df['ch4']
    co2 = df['co2']
    ce = df['ce']
    fluo = df['fluo']

    time = df['start_time']

    ax1 = axes[0]
    ax2 = axes[1]
    ax3 = axes[2]
    
    ax1.cla()
    ax2.cla()
    ax2.yaxis.set_label_position('right')
    ax3.cla()
    ax3.yaxis.set_label_position('right')

        
    #host.set_xlim(0, None)
    ax1.set_ylim(0, max(ch4)/0.8)
    ax2.set_ylim(0, max(co2)/0.8)
    #ax3.set_ylim(0.5, 1/0.8)
    ax3.set_ylim(70, 110)
    
    

    #host.set_xlabel("BIN")
    ax1.set_xlabel("datetime")
    ax1.set_ylabel("CH4 (ppm)")
    ax2.set_ylabel("CO2 (ppm)")
    ax3.set_ylabel("CE (%)")

    color1, color2, color3 = plt.cm.viridis([0, .5, .9])

    p1 = ax1.plot(time, ch4, color=color1, label="CH4", marker='o', linestyle=':')
    p2 = ax2.plot(time, co2, color=color2, label="CO2", marker='o', linestyle=':')
    p3 = ax3.plot(time, ce*100, color=color3, label="CE", marker='o', linestyle=':')
    ax1.set_title("Emissions")

    ax1.legend(handles=p1+p2+p3, loc='upper right')

    # right, left, top, bottom
    ax3.spines['right'].set_position(('outward', 60))

    ax1.yaxis.label.set_color(p1[0].get_color())
    ax2.yaxis.label.set_color(p2[0].get_color())
    ax3.yaxis.label.set_color(p3[0].get_color())
    

    #highlight
    #ax1.axvspan(time[3], time[4], color='red', alpha=0.5)
    if highlight is not None:
        ax1.plot(time[highlight], ch4[highlight], 'r*')
        ax2.plot(time[highlight], co2[highlight], 'r*')
        ax3.plot(time[highlight], ce[highlight]*100, 'r*')


def create_simple_dashboard(fig):
    #fig.suptitle('FAMES Monitor')
    figT, figB = fig.subfigures(2, 1)
    fig_history, fig_histogram = figT.subfigures(1 ,2, width_ratios=[2, 1])
    ax = fig_history.subplots(1,1)
    history_axes = [ax, ax.twinx(), ax.twinx() ]
    histogram_axes = fig_histogram.subplots(1,1)

    fig_signal, fig_info = figB.subfigures(1, 2, width_ratios=[2, 1])
    ax = fig_signal.subplots(1,1)
    axes_signal = [ax]

    return [fig, history_axes, histogram_axes, axes_signal, fig_info]

def update_simple_dashboard( dashboard, df, meas=-1):
   fig = dashboard[0]
   history_axes = dashboard[1]
   histogram_axes = dashboard[2]
   axes_signal = dashboard[3]
   fig_info = dashboard[4]
   plot_history(history_axes, df, meas )
   plot_histogram(histogram_axes, df)
   plot_signal(axes_signal, df, meas)
   
   row = df.iloc[meas]
   id = df.index.get_loc(row.name)
   info = ('Total measurements: {}\nShowing measurement: {}\nFile: {}\nStart time: {}\nStop time {}\nCE: {:.2f}%\nCH4: {:.2f} ppm\nCO2: {:.2f} ppm\nFluo: {:.2f}%'.format(
      len(df.index),
      id + 1,
      os.path.basename(row['file_name'][0]),
      row['start_time'],
      row['stop_time'],
      row['ce']*100,
      row['ch4'],
      row['co2'],
      row['fluo']*100
      ))
   fig_info.clear()
   fig_info.text(0,0.9,info, verticalalignment='top')



if __name__ == "__main__":
    import sys
    print('iuhuu')