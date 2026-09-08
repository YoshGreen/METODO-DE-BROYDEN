"""
Ejercicio 2: Verificación empírica de la convergencia superlineal de Broyden
frente a la convergencia cuadrática de Newton.
"""
import numpy as np
import matplotlib.pyplot as plt
import json, pathlib
from metodos import newton, broyden, configurar_graficos, imprimir_comparacion

FIGURAS = pathlib.Path(__file__).resolve().parent / 'figuras'

def F(x):
    """Sistema de ecuaciones no lineales."""
    x1, x2, x3 = x
    return np.array([
        x1**2 + x2**2 + x3**2 - 3.0,
        x1 + x2**2 + x3**3 - 3.0,
        x1**3 + x2 + x3**2 - 3.0
    ])

def J(x):
    """Jacobiano exacto del sistema."""
    x1, x2, x3 = x
    return np.array([
        [2*x1, 2*x2, 2*x3],
        [1.0, 2*x2, 3*x3**2],
        [3*x1**2, 1.0, 2*x3]
    ])

# ═══════════════════════════════════════════════════════════════════════
# TEOREMA DE DENNIS-MORÉ Y CONVERGENCIA SUPERLINEAL
# ═══════════════════════════════════════════════════════════════════════
# El teorema de Dennis-Moré garantiza la convergencia superlineal para
# métodos cuasi-Newton cuando la matriz aproximada del Jacobiano cumple
# ciertas condiciones asintóticas en la dirección del paso.
#
# Convergencia superlineal significa que:
#    lim (k→∞) ‖e_{k+1}‖ / ‖e_k‖ = 0
#
# Pero a diferencia de Newton, la tasa NO alcanza el orden 2 de forma
# consistente: ‖e_{k+1}‖ / ‖e_k‖² NO tiende a una constante finita.
#
# Al medir la tasa empírica p_k = log(e_{k+1}) / log(e_k), esperamos
# que p_k converja a un valor entre 1 y 2 para Broyden.
# Para sistemas n-dimensionales, la literatura a menudo asocia a Broyden
# con un orden teórico aproximado a la razón áurea (1 + √5)/2 ≈ 1.618,
# dependiendo del análisis y la secuencia de pasos.
# ═══════════════════════════════════════════════════════════════════════

def calcular_errores_y_tasas(historial_x, x_star):
    """Calcula el error absoluto y la tasa empírica de convergencia p_k."""
    errores = []
    for x in historial_x:
        errores.append(np.linalg.norm(x - x_star))
    
    tasas = []
    ks_tasas = []
    
    for k in range(len(errores) - 1):
        ek = errores[k]
        ek_next = errores[k+1]
        
        # Calcular tasa p_k solo si hay error significativo y es menor que 1
        # para evitar divisiones por cero y ruido numérico al acercarnos a la solución
        if 1e-15 < ek < 1.0:
            pk = np.log(ek_next) / np.log(ek)
            tasas.append(pk)
            ks_tasas.append(k)
            
    return errores, ks_tasas, tasas

def main():
    FIGURAS.mkdir(exist_ok=True)
    configurar_graficos()
    
    # 1. Definir parámetros del sistema
    x_star = np.array([1.0, 1.0, 1.0])
    x0 = np.array([0.5, 1.5, 0.8])
    tol = 1e-14
    max_iter = 30
    
    # 2. Ejecutar métodos
    print("Ejecutando método de Newton...")
    res_newton = newton(F, J, x0, tol=tol, max_iter=max_iter, verbose=False)
    
    print("Ejecutando método de Broyden...")
    B0 = J(x0) # Usamos J(x0) como aproximación inicial
    res_broyden = broyden(F, x0, B0=B0, tol=tol, max_iter=max_iter, verbose=False)
    
    # 3. Calcular errores y tasas
    err_n, k_tasas_n, tasas_n = calcular_errores_y_tasas(res_newton['historial_x'], x_star)
    err_b, k_tasas_b, tasas_b = calcular_errores_y_tasas(res_broyden['historial_x'], x_star)
    
    # 4. Imprimir tabla de resultados en consola
    print("\n" + "═"*70)
    print("  ANÁLISIS ITERACIÓN POR ITERACIÓN (Newton vs Broyden)")
    print("═"*70)
    print(f" {'k':>3s} | {'Error Newton':>15s} | {'p_k Newton':>10s} | {'Error Broyden':>15s} | {'p_k Broyden':>10s}")
    print("-" * 70)
    
    max_k = max(len(err_n), len(err_b))
    for k in range(max_k):
        str_en = f"{err_n[k]:15.2e}" if k < len(err_n) else f"{'-':>15s}"
        str_eb = f"{err_b[k]:15.2e}" if k < len(err_b) else f"{'-':>15s}"
        
        # Encontrar p_k
        idx_tn = k_tasas_n.index(k) if k in k_tasas_n else -1
        idx_tb = k_tasas_b.index(k) if k in k_tasas_b else -1
        
        str_pn = f"{tasas_n[idx_tn]:10.3f}" if idx_tn != -1 else f"{'-':>10s}"
        str_pb = f"{tasas_b[idx_tb]:10.3f}" if idx_tb != -1 else f"{'-':>10s}"
        
        print(f" {k:3d} | {str_en} | {str_pn} | {str_eb} | {str_pb}")
        
    print("═"*70)
    print("\nResumen narrativo:")
    print("Se observa claramente cómo el método de Newton estabiliza su tasa p_k cerca de 2")
    print("(convergencia cuadrática), logrando altísima precisión en muy pocos pasos.")
    print("Por otro lado, Broyden muestra un p_k que oscila y se estabiliza típicamente")
    print("entre 1 y 2, confirmando su convergencia superlineal. Aunque requiere más iteraciones,")
    print("compensa con su menor costo computacional por iteración (O(n²) frente a O(n³)).")

    # 5. GRAFICAR
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Gráfico 1: Error vs iteración
    ax1.plot(range(len(err_n)), np.log10(np.maximum(err_n, 1e-16)), 'b-o', label='Newton')
    ax1.plot(range(len(err_b)), np.log10(np.maximum(err_b, 1e-16)), 'r-s', label='Broyden')
    ax1.set_xlabel('Iteración k')
    ax1.set_ylabel('log10(‖x_k − x*‖)')
    ax1.set_title('Error real vs iteración')
    ax1.legend()
    
    # Gráfico 2: Tasa empírica p_k vs iteración
    ax2.plot(k_tasas_n, tasas_n, 'b-o', label='Newton')
    ax2.plot(k_tasas_b, tasas_b, 'r-s', label='Broyden')
    
    # Líneas de referencia
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7)
    ax2.text(0, 1.02, 'Lineal (p=1)', color='gray')
    
    ax2.axhline(y=1.618, color='green', linestyle='--', alpha=0.7)
    ax2.text(0, 1.638, 'Superlineal (p≈1.618)', color='green')
    
    ax2.axhline(y=2.0, color='black', linestyle='--', alpha=0.7)
    ax2.text(0, 2.02, 'Cuadrática (p=2)', color='black')
    
    ax2.set_xlabel('Iteración k')
    ax2.set_ylabel('p_k')
    ax2.set_title('Tasa de convergencia empírica')
    ax2.set_ylim([0.5, 2.5])
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(FIGURAS / 'ej2_convergencia_superlineal.png', dpi=300, bbox_inches='tight', facecolor='white')

    resultados = {
        'newton': {
            'iteraciones': res_newton['iteraciones'],
            'evals_F': res_newton['evals_F'],
            'tasas_finales': [float(t) for t in tasas_n[-3:]] if len(tasas_n) >= 3 else [float(t) for t in tasas_n]
        },
        'broyden': {
            'iteraciones': res_broyden['iteraciones'],
            'evals_F': res_broyden['evals_F'],
            'tasas_finales': [float(t) for t in tasas_b[-3:]] if len(tasas_b) >= 3 else [float(t) for t in tasas_b]
        }
    }
    with open(FIGURAS / 'resultados_ej2.json', 'w') as f:
        json.dump(resultados, f, indent=2)

    plt.show()

if __name__ == '__main__':
    main()
