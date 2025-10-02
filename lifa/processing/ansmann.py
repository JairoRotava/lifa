# Codgio enviado por Alex para processamento Raman. Parece retornar extinction rate para canal elástico a partir de medida Raman de N2.

import numpy as np
from scipy.signal import savgol_filter

def number_density_air(p_pa, T_k):
    # N_air = p / (k_B T)
    k_B = 1.380649e-23
    return p_pa / (k_B * T_k)

def number_density_n2(p_pa, T_k, f_n2=0.78084):
    return f_n2 * number_density_air(p_pa, T_k)

def rayleigh_sigma_nm(lambda_nm):
    # Aproximação típica (~lambda^-4). Substitua por fórmula com fator de King se quiser.
    # Retorna sigma em m^2 para ar seco aproximado.
    lam_um = lambda_nm * 1e-3
    # coef calib aproximado para Rayleigh do ar seco no visível:
    # Use sua função de referência se tiver (Bodhaine, Bucholtz, etc.).
    A = 5.45e-32  # m^2 at 0.55 µm (valor ilustrativo)
    return A * (0.55 / lam_um)**4

def rayleigh_extinction(lambda_nm, N_air):
    sigma = rayleigh_sigma_nm(lambda_nm)
    return sigma * N_air  # m^-1

def raman_extinction_ansmann(
    z_m, SR_counts, p_pa, T_k,
    lambda_E_nm, lambda_R_nm,
    angstrom=1.3,
    deriv_window=21, deriv_poly=3
):
    """
    z_m: vetor de alturas [m] crescente e uniformemente espaçado
    SR_counts: sinal Raman já limpo (bg/overlap/dead-time) [u.a.]
    p_pa, T_k: perfis pressão/temperatura
    returns: alpha_aer_E [1/m]
    """
    # Densidades
    N_air = number_density_air(p_pa, T_k)
    N_R = number_density_n2(p_pa, T_k)  # para Raman de N2

    # Extinção molecular
    alpha_m_E = rayleigh_extinction(lambda_E_nm, N_air)
    alpha_m_R = rayleigh_extinction(lambda_R_nm, N_air)

    # Termo log do método:
    # L(z) = ln( N_R(z) * z^2 / S_R(z) )
    # Use uma proteção contra zeros/negativos
    z2 = np.clip(z_m, 1.0, None)**2
    SRc = np.clip(SR_counts, np.finfo(float).tiny, None)
    L = np.log( np.clip(N_R, np.finfo(float).tiny, None) * z2 / SRc )

    # Derivada dL/dz com Savitzky-Golay (suaviza e deriva)
    # Requer passo uniforme
    dz = np.mean(np.diff(z_m))
    L_smooth = savgol_filter(L, deriv_window, deriv_poly, mode="interp")
    dL_dz = savgol_filter(L, deriv_window, deriv_poly, deriv=1, delta=dz, mode="interp")

    # Fator de Ångström entre lambdas
    fA = (lambda_R_nm / lambda_E_nm)**(-angstrom)

    # Fórmula fechada
    alpha_aer_E = ( dL_dz - alpha_m_E - alpha_m_R ) / (1.0 + fA)

    # Opcional: filtrar alpha para reduzir ruído residual
    alpha_aer_E = savgol_filter(alpha_aer_E, deriv_window, deriv_poly, mode="interp")

    return alpha_aer_E, dict(
        dL_dz=dL_dz, alpha_m_E=alpha_m_E, alpha_m_R=alpha_m_R, N_air=N_air, N_R=N_R
    )

# --- Exemplo de uso ---
# z_m = np.arange(150.0, 15000.0, 15.0)  # grelha de 150 m a 15 km, passo 15 m (exemplo)
# SR = ...  # seu perfil Raman já corrigido
# p_pa, T_k = ...  # perfis atmosféricos colocalizados
# alpha_aer_532, debug = raman_extinction_ansmann(z_m, SR, p_pa, T_k, 532.0, 607.0, angstrom=1.4)
