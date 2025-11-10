import matplotlib.pyplot as plt
import lifa.fames.process_mixing_ratio as em
import glob
import numpy as np
from lifa.processing import helper_functions
from datetime import datetime, timedelta
import string 
import matplotlib.dates as mdates


# --- Configurações de legenda, cores e markers ---
# --- Legendas dos sinais ---
legend_labels = {
    'co2_raman_371': 'CO$_{2}$ at 371 nm',
    'ch4_raman_395_s': 'CH$_{4}$ s-pol at 395 nm',
    'ch4_raman_395_p': 'CH$_{4}$ p-pol at 395 nm',
    'fluo_460': 'Fluorescence at 460 nm',
    'n2_raman_353': 'N$_{2}$ at 353 nm',
    'rayleigh_355': 'Particulate signal at 355 nm',
    'n2_raman_530': 'N$_{2}$ at 530 nm',
    'rayleigh_532': 'Particulate signal at 532 nm'
}

# --- Cores dos sinais ---
colors = {
    'co2_raman_371': '#6a0dad',       # violeta
    'ch4_raman_395_s': '#7f00ff',     # roxo
    'ch4_raman_395_p': '#9b30ff',     # roxo claro
    'fluo_460': '#1f77b4',   # azul
    'n2_raman_353': '#4b0082',        # índigo
    'rayleigh_355': '#8a2be2', # azul-violeta
    'n2_raman_530': '#2ca02c',        # verde
    'rayleigh_532': '#3cb371'  # verde-claro
}

# --- Markers dos sinais ---
markers = {
    'co2_raman_371': 'o',       
    'ch4_raman_395_s': 'o',     
    'ch4_raman_395_p': 'o',     
    'fluo_460': 'o',   
    'n2_raman_353': 'o',        
    'rayleigh_355': 'o', 
    'n2_raman_530': 'o',        
    'rayleigh_532': 'o'  
}



def plot_signals(output, roi_min, roi_max, title = None):

    results = {}
    for index, row in output.iterrows():
        results[index] = {
                'signal_interval' : {
                    'co2_raman_371': row['co2_raman_trace'],
                    'ch4_raman_395_s': row['ch4_raman_s_trace'],
                    'ch4_raman_395_p': row['ch4_raman_p_trace'],
                    'fluo_460': row['fluorescence_trace'],
                    'n2_raman_353': row['n2_raman_trace'],
                    'rayleigh_355': row['rayleigh_trace'],
                    'n2_raman_530': row['n2_raman_b_trace'],
                    'rayleigh_532': row['rayleigh_b_trace']
                },
                'z_interval' : row['z_trace'],
                #'flare_pos' : row['z_flare'],
                'files' : row['files'],
            }
        
    #interval = timedelta(minutes=5)
    interval = output['duration'].iloc[0]




    markers = {k:'o' for k in legend_labels.keys()}

    # --- Controle de plotagem ---
    plot_groups = True  # True = plot grupos + média, False = média apenas


    # --- Criação do painel 4x2 ---
    fig, ax = plt.subplots(nrows=2, ncols=4, figsize=(20, 12), layout='constrained')
    ax = ax.flatten()

    if title is None:
        fig.suptitle('Sinais com média', fontsize=18, fontweight='bold')
    else:
        fig.suptitle(title, fontsize=18, fontweight='bold')

    
    title_fontsize = 13
    label_fontsize = 11
    tick_fontsize = 11

    nrows, ncols = 4, 2  # para referência das posições

    for i, key in enumerate(legend_labels.keys()):
        ax_i = ax[i]
        all_data = []

        # --- Plot dos grupos ---
        for j, (group_id, res) in enumerate(results.items()):
            signal_interval = res['signal_interval']
            z_interval = res['z_interval']
            #flare_pos = res['flare_pos']

            data = signal_interval[key]
            all_data.append(data)

            if plot_groups:
                ax_i.plot(
                    z_interval,
                    data,
                    #color='gray',  # cor neutra para todos os grupos
                    color = colors[key],
                    linestyle='-',
                    linewidth=1.0,
                    alpha=0.3
                )

        # --- Calcula a média do sinal ---
        mean_signal = np.mean(np.array(all_data), axis=0)

        # --- Plot da média ---
        mean_color = colors.get(key, 'k')
        marker = markers.get(key, 'o')
        ax_i.plot(
            z_interval,
            mean_signal,
            color=mean_color,
            linestyle='-',
            linewidth=2.0,
            marker=marker,
            markersize=2,
            label=f'Time average = {interval.seconds} sec'
        )

        # Retângulo em torno do flare
#        ax_i.axvspan(
#            flare_pos - delta, flare_pos + delta,
#            facecolor='none',
#            edgecolor='lightgray',
#            linestyle='--',
#            linewidth=1.0
#        )

        #ax_i.axvspan(output['z_min_roi'].iloc[0], output['z_max_roi'].iloc[0],
        ax_i.axvspan(roi_min, roi_max,
        facecolor='lightgray', alpha=1)

        ax_i.set_title(legend_labels[key], fontsize=title_fontsize, fontweight='bold')


        # --- Ajuste dos labels ---
        col_idx = i % ncols
        row_idx = i // ncols

        if col_idx == 0:  # primeira coluna
            ax_i.set_ylabel('Signal (a.u.)', fontsize=label_fontsize)
        if row_idx == nrows - 1:  # última linha
            ax_i.set_xlabel('distance (m)', fontsize=label_fontsize)


        ax_i.set_yscale('log')
        #ax_i.set_xlim(0, 1000)
        ax_i.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        ax_i.legend(fontsize=9)

    # Desliga eixos extras
    for j in range(i + 1, len(ax)):
        ax[j].axis('off')

    #plt.show()
    return(fig)


##-----------------------------------------------------------------
# --- Labels e cores ---
legend_m_labels = {
    'CO2/N2': 'Concentration of CO$_{2}$',
    'CH4/N2': 'Concentration of CH$_{4}$',
    'CE [%]': 'Combustion Efficiency',
    'FLUO [%]': 'Fluorescence',

}


y_labels = {
    'CO2/N2': '[ppm]',
    'CH4/N2': '[ppm]',
    'CE [%]': '[%]',
    'FLUO [%]': '[%]',

}


colors_m = {
    'CO2/N2': '#1f77b4',   # azul
    'CH4/N2': '#ff7f0e',   # laranja
    'CE [%]': '#2ca02c',    # verde
    'FLUO [%]': "#cc2944",
}


# --- Ajuste manual dos eixos Y ---
ymin_values = {
    'CO2/N2': 0,
    'CH4/N2': 0,
    'CE [%]': None,
    'FLUO [%]': 0,
}

ymax_values = {
    'CO2/N2': None,
    'CH4/N2': None,
    'CE [%]': None,
    'FLUO [%]': None,
}

# --- Tamanho da fonte dos ticks ---
tick_major_size = 14
tick_minor_size = 12




def plot_emissions(output, roi_min, roi_max, title=None):
    plot_groups_concentration = True
    plot_groups = True

    # --- Preparar dados para plotagem temporal (valores máximos) ---
    time_labels = []
    max_co2 = []
    max_ch4 = []
    max_ce = []
    max_fluo = []



    results = {}
    for index, row in output.iterrows():
         # Retira valores de CE, CO2, CH4 e fluorescencia do range definidos
        roi_bin_min = helper_functions.find_nearest(roi_min, row['z_trace'])
        roi_bin_max = helper_functions.find_nearest(roi_max, row['z_trace'])
        ce_peak = np.min(row['ce_trace'][roi_bin_min:roi_bin_max])
        ch4_peak = np.max(row['ch4_mixing_trace'][roi_bin_min:roi_bin_max])
        co2_peak = np.max(row['co2_mixing_trace'][roi_bin_min:roi_bin_max])
        fluo_peak = np.max(row['fluo_mixing_trace'][roi_bin_min:roi_bin_max])
        #ce_m_peak = np.max(row['ce_mixing_trace'][roi_bin_min:roi_bin_max])
        results[index] = {
                'mratios' : {
                    'CO2/N2': row['co2_mixing_trace'],
                    'CH4/N2': row['ch4_mixing_trace'],
                    'CE [%]': row['ce_trace'],
                    'FLUO [%]': row['fluo_mixing_trace']
                },
                'start_time': row['start_time'],
                'stop_time': row['stop_time'],
                'duration' : row['duration'],
                'ce': ce_peak,         
                'ch4': ch4_peak,
                'co2': co2_peak,
                'fluorescence': fluo_peak,
                'z_interval' : row['z_trace'],
                #'flare_pos' : row['z_flare'],
                'files' : row['files'],
            }
        
    #interval = timedelta(minutes=5)
    interval = output['duration'].iloc[0]
    group_mratios = results 

    mean_mratios = {}
    for key in ['CO2/N2', 'CH4/N2', 'CE [%]', 'FLUO [%]']:
        stacked = np.array([g['mratios'][key] for g in group_mratios.values()])
        mean_mratios[key] = np.mean(stacked, axis=0)

    z_interval_mean = group_mratios[list(group_mratios.keys())[0]]['z_interval']
    #flare_pos_mean = group_mratios[list(group_mratios.keys())[0]]['flare_pos']
    #flare_pos_mean = output['z_flare'].iloc[0]



    for group_id, res in group_mratios.items():
        time_labels.append(res['start_time'] + res['duration']/2)

        #z_interval = res['z_interval']
        #flare_pos = res['flare_pos']
        #mask = (z_interval >= flare_pos - delta) & (z_interval <= flare_pos + delta)

        #max_co2.append(np.max(res['mratios']['CO2/N2'][mask]))
        max_co2.append(res['co2'])
        ##max_ch4.append(np.max(res['mratios']['CH4/N2'][mask]))
        max_ch4.append(res['ch4'])
        #max_ce.append(np.max(res['mratios']['CE [%]'][mask]))
        max_ce.append(res['ce'])

        max_fluo.append(res['fluorescence'])

    # --- Criar painel 2 linhas x 3 colunas ---
    fig, axes = plt.subplots(nrows=2, ncols=4, figsize=(20, 12), layout='constrained')
    axes = axes.flatten()

    # --- Primeira coluna: sinais médios vs distância ---
    for i, key in enumerate(mean_mratios.keys()):
        ax = axes[i]
        if plot_groups:
            for g in group_mratios.values():
                ax.plot(g['z_interval'], g['mratios'][key],
                        color=colors_m[key], linestyle='-', alpha=0.3, linewidth=1)
        ax.plot(z_interval_mean, mean_mratios[key],
                color=colors_m[key], linestyle='-', linewidth=2, label='Time average')
        
#        ax.axvspan(output['z_min_roi'].iloc[0], output['z_max_roi'].iloc[0],
        ax.axvspan(roi_min, roi_max,
                facecolor='lightgray', alpha=1)
        
        ax.set_title(legend_m_labels[key], fontsize=16, fontweight='bold')
        ax.set_xlabel('Distance (m)', fontsize=12, fontweight='bold')
        #ax.set_ylabel('Concentration [ppm]' if key != 'CE [%]' else 'Efficiency [%]',
        #              fontsize=14, fontweight='bold')
        ax.set_ylabel(y_labels[key],
                    fontsize=14, fontweight='bold')

        ax.set_ylim(ymin_values[key], ymax_values[key])
        ax.tick_params(axis='both', which='major', labelsize=tick_major_size)
        ax.tick_params(axis='both', which='minor', labelsize=tick_minor_size)
        ax.grid(True, linestyle='--', alpha=0.5)
        #ax.legend(fontsize=10)

    # --- Segunda coluna: valores máximos vs tempo com variabilidade ---
    values_list = [max_co2, max_ch4, max_ce, max_fluo]
    #values_list = [output['co2'], output['ch4'], output['ce'], output['fluo']]
    variables = ['CO2/N2', 'CH4/N2', 'CE [%]', 'FLUO [%]']
    ylabels = ['[ppm]', '[ppm]', '[%]', '[%]']

    for i, var in enumerate(variables):
        ax = axes[i+4]  # segunda linha

        # --- Plot individual de cada grupo em cinza com transparência ---
        #for g in group_mratios.values():
            #z_interval = g['z_interval']
            #flare_pos = g['flare_pos']
            #mask = (z_interval >= flare_pos - delta) & (z_interval <= flare_pos + delta)
            # plot em cinza apenas os valores máximos dentro do intervalo
            #ax.plot(time_labels, [np.max(g['mratios'][var][mask])] * len(time_labels),
            #ax.plot(time_labels, [values_list[i]] * len(time_labels),
            #        color='gray', linestyle='-', alpha=0.3, linewidth=1)

        # --- Plot do valor máximo em cor sólida ---
        ax.plot(time_labels, values_list[i], '-o', color=colors_m[var], label=var)
        #ax.plot(max_values_list[i], '-o', color=colors[var], label=var)

        ax.set_title(legend_m_labels[var], fontsize=14, fontweight='bold')
        ax.set_xlabel('Date and Time', fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabels[i], fontsize=12, fontweight='bold')
        ax.set_ylim(ymin_values[var], ymax_values[var])

        # --- Formatar eixo X ---
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b %H:%M'))
        total_minutes = int((max(time_labels) - min(time_labels)).total_seconds() / 60)
        step = 2 if total_minutes / 2 <= 30 else max(1, total_minutes // 15)
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, step)))

        # --- Tamanho dos ticks ---
        ax.tick_params(axis='both', which='major', labelsize=tick_major_size)
        ax.tick_params(axis='both', which='minor', labelsize=tick_minor_size)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.5)
        #ax.legend(fontsize=10)

    # --- Título do painel ---
    if title is None:
        fig.suptitle('Concentration of CO$_2$ and CH$_4$, Combustion Efficiency and Fluorescence\n', fontsize=18, fontweight='bold')
    else:
        fig.suptitle(title, fontsize=18, fontweight='bold')

    return(fig)
#plt.show()
