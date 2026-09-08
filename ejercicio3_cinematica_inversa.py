import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import Blues

import json, pathlib

# Importar funciones de nuestro módulo base (metodos.py)
from metodos import newton, broyden, imprimir_comparacion, configurar_graficos

FIGURAS = pathlib.Path(__file__).resolve().parent / 'figuras'

"""
EJERCICIO 3: Cinemática Inversa de un Brazo Robótico (3 Eslabones)

CONTEXTO PARA LA PRESENTACIÓN:
La cinemática inversa es fundamental en robótica, animación 3D y videojuegos.
Consiste en encontrar los ángulos de las articulaciones (θ) necesarios para 
que el extremo del brazo alcance una posición y orientación deseadas (x, y, φ).

El Jacobiano J(θ) existe analíticamente, pero su derivación manual es muy 
TEDIOSA, especialmente a medida que aumentan los grados de libertad (DOF). 
Para brazos de 6-DOF o personajes humanoides, calcular y reevaluar J(θ) 
completamente en cada paso es costoso y propenso a errores.

Aquí es donde los métodos cuasi-Newton, como el de Broyden, brillan en la práctica:
evitan tener que derivar y re-calcular el Jacobiano exacto para cada configuración 
del brazo durante la iteración, manteniendo una convergencia muy rápida.
"""

# Configurar el estilo de los gráficos para la presentación
configurar_graficos()
FIGURAS.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
#  1. MODELO DEL BRAZO ROBÓTICO
# ═══════════════════════════════════════════════════════════════════════

# Longitudes de los eslabones
L1, L2, L3 = 2.0, 1.5, 1.0

# Posición y orientación objetivo (Target)
# Nota: La longitud máxima del brazo es 4.5. (3^2 + 2^2)^0.5 ≈ 3.6 < 4.5. Es alcanzable.
x_target = 3.0
y_target = 2.0
phi_target = np.pi / 4  # 45 grados

def F(theta):
    """
    Sistema de ecuaciones F(θ) = 0 para la cinemática inversa.
    Devuelve la diferencia entre la posición/orientación actual y la objetivo.
    """
    t1, t2, t3 = theta
    
    # Cinemática directa: posición del extremo (efector final)
    x = L1*np.cos(t1) + L2*np.cos(t1+t2) + L3*np.cos(t1+t2+t3)
    y = L1*np.sin(t1) + L2*np.sin(t1+t2) + L3*np.sin(t1+t2+t3)
    
    # Orientación del extremo (suma de los ángulos)
    phi = t1 + t2 + t3
    
    # Sistema de residuos
    f1 = x - x_target
    f2 = y - y_target
    f3 = phi - phi_target
    
    return np.array([f1, f2, f3])

def J(theta):
    """
    Jacobiano analítico J(θ) del sistema.
    Calculado derivando analíticamente cada ecuación respecto a t1, t2, t3.
    ¡Imaginen hacer esto a mano para 6 o más eslabones!
    """
    t1, t2, t3 = theta
    
    df1_dt1 = -L1*np.sin(t1) - L2*np.sin(t1+t2) - L3*np.sin(t1+t2+t3)
    df1_dt2 = -L2*np.sin(t1+t2) - L3*np.sin(t1+t2+t3)
    df1_dt3 = -L3*np.sin(t1+t2+t3)
    
    df2_dt1 = L1*np.cos(t1) + L2*np.cos(t1+t2) + L3*np.cos(t1+t2+t3)
    df2_dt2 = L2*np.cos(t1+t2) + L3*np.cos(t1+t2+t3)
    df2_dt3 = L3*np.cos(t1+t2+t3)
    
    df3_dt1 = 1.0
    df3_dt2 = 1.0
    df3_dt3 = 1.0
    
    return np.array([
        [df1_dt1, df1_dt2, df1_dt3],
        [df2_dt1, df2_dt2, df2_dt3],
        [df3_dt1, df3_dt2, df3_dt3]
    ])

# ═══════════════════════════════════════════════════════════════════════
#  2. RESOLUCIÓN DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════

# Ángulos iniciales (rad): el brazo apuntando hacia arriba-derecha
theta0 = np.array([0.5, 0.5, 0.5])

# Ejecutar Newton para comparación
print("\nEjecutando Método de Newton...")
res_newton = newton(F, J, theta0, tol=1e-8, max_iter=50, verbose=False)

# Ejecutar Broyden con el Jacobiano inicial evaluado analíticamente
print("\nEjecutando Método de Broyden...")
B0 = J(theta0)
res_broyden = broyden(F, theta0, B0=B0, tol=1e-8, max_iter=50, verbose=False)

# ═══════════════════════════════════════════════════════════════════════
#  3. SALIDA POR CONSOLA
# ═══════════════════════════════════════════════════════════════════════

def cin_directa(theta):
    """Calcula x, y, phi para un conjunto de ángulos."""
    t1, t2, t3 = theta
    x = L1*np.cos(t1) + L2*np.cos(t1+t2) + L3*np.cos(t1+t2+t3)
    y = L1*np.sin(t1) + L2*np.sin(t1+t2) + L3*np.sin(t1+t2+t3)
    phi = t1 + t2 + t3
    return x, y, phi

theta_final = res_broyden['solucion']
x_f, y_f, phi_f = cin_directa(theta_final)

print("\nResultados de Cinemática Inversa (usando Broyden):")
print(f"Ángulos Iniciales [grados]: {np.degrees(theta0).round(2)}")
print(f"Ángulos Finales   [grados]: {np.degrees(theta_final).round(2)}")
print("\nPosición del efector final vs Objetivo:")
print(f"X:   alcanzado = {x_f:.4f}, objetivo = {x_target:.4f}")
print(f"Y:   alcanzado = {y_f:.4f}, objetivo = {y_target:.4f}")
print(f"Phi: alcanzado = {np.degrees(phi_f):.2f}°, objetivo = {np.degrees(phi_target):.2f}°")

imprimir_comparacion(res_newton, res_broyden)

# ═══════════════════════════════════════════════════════════════════════
#  4. GRÁFICAS PARA LA PRESENTACIÓN
# ═══════════════════════════════════════════════════════════════════════

def dibujar_brazo(ax, theta, color, alpha=1.0, linewidth=2, label=None):
    """
    Función de ayuda para graficar el brazo robótico a partir de sus ángulos.
    Calcula la posición de las articulaciones (nodos) y las une con líneas.
    """
    t1, t2, t3 = theta
    
    # Coordenadas de las articulaciones
    x0, y0 = 0.0, 0.0
    x1 = L1*np.cos(t1)
    y1 = L1*np.sin(t1)
    x2 = x1 + L2*np.cos(t1+t2)
    y2 = y1 + L2*np.sin(t1+t2)
    x3 = x2 + L3*np.cos(t1+t2+t3)
    y3 = y2 + L3*np.sin(t1+t2+t3)
    
    xs = [x0, x1, x2, x3]
    ys = [y0, y1, y2, y3]
    
    # Dibujar eslabones (líneas) y articulaciones (círculos)
    ax.plot(xs, ys, '-', color=color, alpha=alpha, linewidth=linewidth, label=label)
    ax.plot(xs, ys, 'o', color=color, alpha=alpha, markersize=8)

# -- GRÁFICO 1: Visualización del brazo robótico --
fig1, ax1 = plt.subplots()

# Dibujar configuración inicial
dibujar_brazo(ax1, theta0, color='lightgray', linewidth=4, label='Inicial')

# Dibujar pasos intermedios (iteraciones de Broyden)
hist_th = res_broyden['historial_x']
n_iters = len(hist_th)
for i, th in enumerate(hist_th[1:-1]):
    # Mapear el índice de iteración a un color progresivo de la paleta Blues
    frac = (i + 1) / n_iters
    color_intermedio = Blues(0.3 + 0.6 * frac) # Evitar los colores demasiado claros
    dibujar_brazo(ax1, th, color=color_intermedio, alpha=0.5, linewidth=2)

# Dibujar configuración final
dibujar_brazo(ax1, theta_final, color='navy', linewidth=4, label='Final (Broyden)')

# Marcar el punto objetivo (Target)
ax1.plot(x_target, y_target, 'r*', markersize=15, label='Objetivo')

ax1.set_aspect('equal')
ax1.set_xlabel('Eje X')
ax1.set_ylabel('Eje Y')
ax1.set_title('Cinemática inversa — Brazo robótico de 3 eslabones')
ax1.legend(loc='lower right')
ax1.set_xlim(-1, 4.5)
ax1.set_ylim(-1, 4.5)
plt.tight_layout()
plt.savefig(FIGURAS / 'ej3_brazo_robotico.png', dpi=300, bbox_inches='tight', facecolor='white')


# -- GRÁFICO 2: Evolución de la convergencia (‖F(x)‖) --
fig2, ax2 = plt.subplots()

ax2.semilogy(res_newton['historial_norma'], 'o-', label='Newton', color='darkorange', linewidth=2.5)
ax2.semilogy(res_broyden['historial_norma'], 's--', label='Broyden', color='navy', linewidth=2.5)

ax2.set_xlabel('Iteración (k)')
ax2.set_ylabel(r'Norma del residuo $\Vert F(x_k) \Vert$ (log)')
ax2.set_title('Convergencia en Cinemática Inversa')
ax2.legend()
plt.tight_layout()
plt.savefig(FIGURAS / 'ej3_convergencia_cinematica.png', dpi=300, bbox_inches='tight', facecolor='white')

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
    'angulos_iniciales_deg': np.degrees(theta0).tolist(),
    'angulos_finales_deg': np.degrees(theta_final).tolist(),
    'pos_final': {'x': float(x_f), 'y': float(y_f), 'phi_deg': float(np.degrees(phi_f))},
    'objetivo': {'x': x_target, 'y': y_target, 'phi_deg': float(np.degrees(phi_target))}
}
with open(FIGURAS / 'resultados_ej3.json', 'w') as f:
    json.dump(resultados, f, indent=2)

plt.show()
