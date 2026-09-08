import numpy as np
import matplotlib.pyplot as plt
import time
import json, pathlib
from metodos import newton, broyden, configurar_graficos

FIGURAS = pathlib.Path(__file__).resolve().parent / 'figuras'

# ═══════════════════════════════════════════════════════════════════════
#  CONTEXTO DEL PROBLEMA
# ═══════════════════════════════════════════════════════════════════════
# La ecuación de Bratu modela fenómenos de combustión, reacciones químicas
# y descontrol térmico (thermal runaway).
# Estos grandes sistemas no lineales aparecen constantemente en simulaciones
# basadas en Elementos Finitos (FEM) o Diferencias Finitas (FDM).
# Para n grandes, el costo O(n³) por iteración de Newton domina el tiempo
# de cómputo. Broyden evita esto con un costo O(n²) por iteración.
#
# NOTA: Para este problema en particular, el Jacobiano de Newton es
# tridiagonal, por lo que un solver especializado podría resolver el
# sistema en O(n). Sin embargo, usamos np.linalg.solve (general O(n³))
# en metodos.py para ilustrar el comportamiento en el caso general
# de sistemas densos o sin estructura especial explotada.
# ═══════════════════════════════════════════════════════════════════════

def fdm_bratu_F(u, n, lam=1.0):
    """
    Evalúa la función F(u) para el sistema de Diferencias Finitas.
    F_i = (u_{i-1} - 2u_i + u_{i+1})/h² + λ·exp(u_i) = 0
    """
    h = 1.0 / (n + 1)
    F = np.zeros(n)
    
    # Fronteras u_0 = u_{n+1} = 0
    # Para i = 0 (primer punto interior, u_1 en la malla completa)
    if n == 1:
        F[0] = (-2*u[0])/h**2 + lam * np.exp(u[0])
    else:
        F[0] = (-2*u[0] + u[1])/h**2 + lam * np.exp(u[0])
        
        # Para i = 1 hasta n-2
        for i in range(1, n - 1):
            F[i] = (u[i-1] - 2*u[i] + u[i+1])/h**2 + lam * np.exp(u[i])
            
        # Para i = n-1 (último punto interior)
        F[n-1] = (u[n-2] - 2*u[n-1])/h**2 + lam * np.exp(u[n-1])
        
    return F

def fdm_bratu_J(u, n, lam=1.0):
    """
    Evalúa el Jacobiano exacto (tridiagonal) como una matriz densa.
    J_{ii}   = -2/h² + λ·exp(u_i)
    J_{i,i-1} = 1/h²
    J_{i,i+1} = 1/h²
    """
    h = 1.0 / (n + 1)
    J = np.zeros((n, n))
    
    for i in range(n):
        J[i, i] = -2/h**2 + lam * np.exp(u[i])
        if i > 0:
            J[i, i-1] = 1/h**2
        if i < n - 1:
            J[i, i+1] = 1/h**2
            
    return J

def main():
    FIGURAS.mkdir(exist_ok=True)
    configurar_graficos()
    
    lam = 1.0
    ns = [20, 50, 100, 200]
    
    tiempos_newton = []
    tiempos_broyden = []
    evals_F_newton = []
    evals_F_broyden = []
    iters_newton = []
    iters_broyden = []
    
    sol_newton_100 = None
    sol_broyden_100 = None
    x_100 = None
    
    print(f"\n{'═'*85}")
    print(f"  ESCALABILIDAD: ECUACIÓN DE BRATU (λ = {lam})")
    print(f"{'═'*85}")
    print(f"  {'n':<5} | {'Newton (s)':<12} | {'Broyden (s)':<12} | {'Speedup':<9} | {'Iters N/B':<11}")
    print(f"  {'-'*5}-+-{'-'*12}-+-{'-'*12}-+-{'-'*9}-+-{'-'*11}")
    
    for n in ns:
        h = 1.0 / (n + 1)
        x_interior = np.linspace(h, 1 - h, n)
        
        # Initial guess: u0 = sin(pi * x)
        u0 = np.sin(np.pi * x_interior)
        
        # Funciones envolventes para fijar n y lam
        F = lambda u: fdm_bratu_F(u, n, lam)
        J = lambda u: fdm_bratu_J(u, n, lam)
        
        # --- NEWTON ---
        t0 = time.perf_counter()
        res_n = newton(F, J, u0, tol=1e-10, max_iter=100, verbose=False)
        t1 = time.perf_counter()
        t_newton = t1 - t0
        
        # --- BROYDEN ---
        # Usamos B0 = J(u0) para una comparación justa
        B0 = J(u0)
        t0 = time.perf_counter()
        res_b = broyden(F, u0, B0=B0, tol=1e-10, max_iter=200, verbose=False)
        t1 = time.perf_counter()
        t_broyden = t1 - t0
        
        # Guardar métricas
        tiempos_newton.append(t_newton)
        tiempos_broyden.append(t_broyden)
        evals_F_newton.append(res_n['evals_F'])
        evals_F_broyden.append(res_b['evals_F'])
        iters_newton.append(res_n['iteraciones'])
        iters_broyden.append(res_b['iteraciones'])
        
        speedup = t_newton / t_broyden if t_broyden > 0 else 0
        print(f"  {n:<5} | {t_newton:<12.5f} | {t_broyden:<12.5f} | {speedup:<9.2f} | {res_n['iteraciones']}/{res_b['iteraciones']}")
        
        if n == 100:
            sol_newton_100 = res_n['solucion']
            sol_broyden_100 = res_b['solucion']
            x_100 = x_interior
            
    print(f"{'═'*85}\n")
    
    # ── Gráfico 1: Solución para n=100 ──
    plt.figure()
    
    # Añadimos las condiciones de frontera para el plot
    x_full = np.concatenate(([0.0], x_100, [1.0]))
    u_n_full = np.concatenate(([0.0], sol_newton_100, [0.0]))
    u_b_full = np.concatenate(([0.0], sol_broyden_100, [0.0]))
    
    plt.plot(x_full, u_n_full, 'b-', label='Newton', linewidth=3)
    plt.plot(x_full, u_b_full, 'r--', label='Broyden', linewidth=2)
    plt.title('Solución de la ecuación de Bratu (n=100, λ=1)')
    plt.xlabel('x')
    plt.ylabel('u(x)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURAS / 'ej4_solucion_bratu.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # ── Gráfico 2: Escalabilidad (Barras) ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    x = np.arange(len(ns))
    width = 0.35
    
    # Izquierda: Tiempo
    ax1.bar(x - width/2, tiempos_newton, width, label='Newton', color='blue', alpha=0.7)
    ax1.bar(x + width/2, tiempos_broyden, width, label='Broyden', color='red', alpha=0.7)
    ax1.set_title('Tiempo de Ejecución vs Tamaño (n)')
    ax1.set_xlabel('Tamaño del sistema (n)')
    ax1.set_ylabel('Tiempo (segundos)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(ns)
    ax1.legend()
    
    # Derecha: Evaluaciones de F
    ax2.bar(x - width/2, evals_F_newton, width, label='Newton', color='blue', alpha=0.7)
    ax2.bar(x + width/2, evals_F_broyden, width, label='Broyden', color='red', alpha=0.7)
    ax2.set_title('Evaluaciones de F vs Tamaño (n)')
    ax2.set_xlabel('Tamaño del sistema (n)')
    ax2.set_ylabel('Cantidad de Evaluaciones')
    ax2.set_xticks(x)
    ax2.set_xticklabels(ns)
    ax2.legend()
    
    fig.suptitle('Escalabilidad: Newton vs Broyden', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIGURAS / 'ej4_escalabilidad.png', dpi=300, bbox_inches='tight', facecolor='white')

    resultados = {
        'tabla': []
    }
    for i, n in enumerate(ns):
        resultados['tabla'].append({
            'n': n,
            't_newton': tiempos_newton[i],
            't_broyden': tiempos_broyden[i],
            'speedup': tiempos_newton[i] / tiempos_broyden[i] if tiempos_broyden[i] > 0 else 0,
            'iters_newton': iters_newton[i],
            'iters_broyden': iters_broyden[i],
            'evals_F_newton': evals_F_newton[i],
            'evals_F_broyden': evals_F_broyden[i]
        })
    with open(FIGURAS / 'resultados_ej4.json', 'w') as f:
        json.dump(resultados, f, indent=2)

    plt.show()

if __name__ == '__main__':
    main()
