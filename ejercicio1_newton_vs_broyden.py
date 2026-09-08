"""
Ejercicio 1: Intersección de Curvas Geométricas (Círculo e Hipérbola)
Comparación: Newton-Raphson vs Broyden

Contexto:
Este sistema representa la búsqueda de puntos de intersección entre curvas geométricas,
un problema muy común en geometría computacional, diseño asistido por computadora (CAD)
y detección de colisiones. 

El sistema es:
    f1(x,y) = x² + y² - 4 = 0    (Circunferencia de radio 2)
    f2(x,y) = x·y - 1 = 0        (Hipérbola)
"""

import numpy as np
import matplotlib.pyplot as plt
import json, pathlib
from metodos import newton, broyden, imprimir_comparacion, configurar_graficos

FIGURAS = pathlib.Path(__file__).resolve().parent / 'figuras'

# 1. Definición del sistema y Jacobiano analítico
def F(vars):
    """
    Evalúa el sistema de ecuaciones no lineales F(x) = 0.
    Cada evaluación conecta el método con la posición actual en el espacio.
    """
    x, y = vars
    return np.array([
        x**2 + y**2 - 4,
        x * y - 1
    ])

def J(vars):
    """
    Evalúa el Jacobiano analítico del sistema.
    J = [[∂f1/∂x, ∂f1/∂y],
         [∂f2/∂x, ∂f2/∂y]]
    Proporciona a Newton la dirección de descenso más rápida en forma exacta.
    """
    x, y = vars
    return np.array([
        [2*x, 2*y],
        [y, x]
    ])

def main():
    FIGURAS.mkdir(exist_ok=True)
    # Configurar estilo de gráficos para la presentación (usando metodos.py)
    configurar_graficos()
    
    # Punto inicial cercano a la solución en el primer cuadrante
    x0 = np.array([2.5, 0.5])
    
    print("Resolviendo el sistema con Newton-Raphson (Jacobiano exacto en cada paso)...")
    # Newton calculará y resolverá un sistema lineal completo usando el Jacobiano exacto
    res_newton = newton(F, J, x0, tol=1e-10, max_iter=20, verbose=True)
    
    print("\nResolviendo el sistema con Broyden (Jacobiano aproximado y actualizado)...")
    # Para Broyden, usamos el Jacobiano exacto evaluado en el punto inicial como B0
    # Esto le da una excelente dirección de arranque.
    B0 = J(x0)
    res_broyden = broyden(F, x0, B0=B0, tol=1e-10, max_iter=20, verbose=True)
    
    # Imprimir la tabla de comparación en consola
    imprimir_comparacion(res_newton, res_broyden)
    
    print("\nExplicación de los gráficos:")
    print("- Gráfico 1 (Trayectorias): Muestra el mapa de contorno del error log10(||F(x,y)||) de fondo.")
    print("  Las curvas sólidas son las funciones f1=0 (círculo) y f2=0 (hipérbola).")
    print("  Se observa cómo cada método navega el espacio hacia la intersección (raíz).")
    print("- Gráfico 2 (Convergencia): Compara la caída del error log10(||F(x_k)||) por iteración.")
    print("  Newton exhibe una pendiente más pronunciada (convergencia cuadrática), mientras")
    print("  que Broyden requiere más iteraciones (convergencia superlineal), pero con menor costo computacional por paso.\n")

    # Extraer historiales de iteración para graficar las trayectorias
    hist_x_newton = np.array(res_newton['historial_x'])
    hist_x_broyden = np.array(res_broyden['historial_x'])
    
    # ---------------------------------------------------------
    # GRAFICO 1: Mapa de contornos y trayectorias
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 8))
    
    # Malla para evaluar el error y graficar contornos
    x_val = np.linspace(0, 3, 200)
    y_val = np.linspace(0, 2.5, 200)
    X, Y = np.meshgrid(x_val, y_val)
    
    # Evaluar la norma ||F(x,y)|| en la malla
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            val = F([X[i,j], Y[i,j]])
            # sumamos eps para evitar log10(0)
            Z[i,j] = np.log10(np.linalg.norm(val) + 1e-16)
            
    # Contornos de log10(||F(x)||)
    cp = plt.contourf(X, Y, Z, levels=30, cmap='viridis', alpha=0.7)
    plt.colorbar(cp, label='$\log_{10}(||F(x, y)||)$')
    
    # Curvas explícitas
    # Círculo: x^2 + y^2 = 4 => y = sqrt(4 - x^2)
    x_circ = np.linspace(0, 2, 200)
    y_circ = np.sqrt(4 - x_circ**2)
    plt.plot(x_circ, y_circ, 'k--', linewidth=2, label='$x^2 + y^2 = 4$ (Círculo)')
    
    # Hipérbola: xy = 1 => y = 1/x
    x_hyp = np.linspace(0.4, 3, 200)
    y_hyp = 1 / x_hyp
    plt.plot(x_hyp, y_hyp, 'k-.', linewidth=2, label='$x \cdot y = 1$ (Hipérbola)')
    
    # Trayectorias de los métodos
    plt.plot(hist_x_newton[:,0], hist_x_newton[:,1], 'bo-', label='Trayectoria Newton', markersize=6)
    plt.plot(hist_x_broyden[:,0], hist_x_broyden[:,1], 'rs-', label='Trayectoria Broyden', markersize=6)
    
    # Puntos especiales
    plt.plot(x0[0], x0[1], 'k*', markersize=12, label='Punto Inicial $x_0$')
    if res_newton['convergio']:
        sol = res_newton['solucion']
        plt.plot(sol[0], sol[1], 'g*', markersize=12, label='Solución Exacta')
        
    plt.title('Trayectorias de Convergencia: Newton vs Broyden')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.xlim([0, 3])
    plt.ylim([0, 2.5])
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(FIGURAS / 'ej1_trayectorias.png', dpi=300, bbox_inches='tight', facecolor='white')
    
    # ---------------------------------------------------------
    # GRAFICO 2: Gráfico de convergencia (norma vs iteración)
    # ---------------------------------------------------------
    plt.figure(figsize=(9, 6))
    
    err_newton = res_newton['historial_norma']
    err_broyden = res_broyden['historial_norma']
    
    # En el eje Y mostramos el logaritmo base 10 de la norma del error,
    # para visualizar claramente la tasa de convergencia (pendiente).
    plt.plot(range(len(err_newton)), np.log10(np.array(err_newton) + 1e-16), 
             'bo-', label='Newton-Raphson', linewidth=2, markersize=8)
    plt.plot(range(len(err_broyden)), np.log10(np.array(err_broyden) + 1e-16), 
             'rs-', label='Broyden', linewidth=2, markersize=8)
             
    plt.title('Convergencia: Newton vs Broyden')
    plt.xlabel('Número de Iteración (k)')
    plt.ylabel('$\log_{10}(||F(x_k)||)$')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(FIGURAS / 'ej1_convergencia.png', dpi=300, bbox_inches='tight', facecolor='white')

    resultados = {
        'newton': {
            'iteraciones': res_newton['iteraciones'],
            'evals_F': res_newton['evals_F'],
            'evals_J': res_newton['evals_J'],
            'norma_final': float(res_newton['historial_norma'][-1]),
            'convergio': res_newton['convergio']
        },
        'broyden': {
            'iteraciones': res_broyden['iteraciones'],
            'evals_F': res_broyden['evals_F'],
            'evals_J': res_broyden['evals_J'],
            'norma_final': float(res_broyden['historial_norma'][-1]),
            'convergio': res_broyden['convergio']
        },
        'solucion': res_newton['solucion'].tolist(),
        'x0': x0.tolist()
    }
    with open(FIGURAS / 'resultados_ej1.json', 'w') as f:
        json.dump(resultados, f, indent=2)
    
    plt.show()

if __name__ == '__main__':
    main()
