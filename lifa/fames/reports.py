import matplotlib.pyplot as plt
import lifa.fames.process_mixing_ratio as em
import glob
import numpy as np

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



def plot_signals(output):

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
                    'n2_raman_530': row['rayleigh_trace'],
                    'rayleigh_532': row['rayleigh_trace']
                },
                'z_interval' : row['z_trace'],
                'flare_pos' : row['z_flare'],
                'files' : row['files'],
            }
        
    #interval = timedelta(minutes=5)
    interval = output['duration'][0]




    markers = {k:'o' for k in legend_labels.keys()}

    # --- Controle de plotagem ---
    plot_groups = True  # True = plot grupos + média, False = média apenas


    # --- Criação do painel 4x2 ---
    fig, ax = plt.subplots(nrows=4, ncols=2, figsize=(12, 20), layout='constrained')
    ax = ax.flatten()

    fig.suptitle('Sinais com média', fontsize=18, fontweight='bold')

    delta = 18
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
            flare_pos = res['flare_pos']

            data = signal_interval[key]
            all_data.append(data)

            if plot_groups:
                ax_i.plot(
                    z_interval,
                    data,
                    color='gray',  # cor neutra para todos os grupos
                    linestyle='-',
                    linewidth=1.0,
                    alpha=0.5
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
        ax_i.axvspan(
            flare_pos - delta, flare_pos + delta,
            facecolor='none',
            edgecolor='lightgray',
            linestyle='--',
            linewidth=1.0
        )

        ax_i.set_title(legend_labels[key], fontsize=title_fontsize, fontweight='bold')


        # --- Ajuste dos labels ---
        col_idx = i % ncols
        row_idx = i // ncols

        if col_idx == 0:  # primeira coluna
            ax_i.set_ylabel('Signal (a.u.)', fontsize=label_fontsize)
        if row_idx == nrows - 1:  # última linha
            ax_i.set_xlabel('distance (m)', fontsize=label_fontsize)


        ax_i.set_yscale('log')
        ax_i.set_xlim(0, 1000)
        ax_i.tick_params(axis='both', which='major', labelsize=tick_fontsize)
        ax_i.legend(fontsize=9)

    # Desliga eixos extras
    for j in range(i + 1, len(ax)):
        ax[j].axis('off')

    #plt.show()
    return(fig)



