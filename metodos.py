"""
metodos.py — Implementaciones desde cero de Newton-Raphson y Broyden
para sistemas de ecuaciones no lineales F(x) = 0.

Proyecto de exposición — Métodos Numéricos II

Conceptos clave implementados:
  • Newton-Raphson: usa el Jacobiano completo J(x_k) en cada iteración.
    Convergencia cuadrática, pero costo O(n³) por iteración.
  • Broyden ("good Broyden"): aproxima el Jacobiano con actualización de
    rango 1, y mantiene la inversa con Sherman-Morrison.
    Convergencia superlineal, costo O(n²) por iteración.
"""

import numpy as np


# ═══════════════════════════════════════════════════════════════════════
#  NEWTON-RAPHSON
# ═══════════════════════════════════════════════════════════════════════

def newton(F, J, x0, tol=1e-10, max_iter=50, verbose=True):
    """
    Método de Newton-Raphson para sistemas no lineales F(x) = 0.

    Algoritmo (por iteración):
        1. Evaluar F(x_k) y J(x_k)                        ← O(n²)
        2. Resolver  J(x_k) · Δx = -F(x_k)                ← O(n³)
        3. Actualizar  x_{k+1} = x_k + Δx

    Resolver el sistema lineal es el análogo multidimensional de
    "dividir por la derivada" en 1D: x_{k+1} = x_k - f(x)/f'(x).

    Convergencia: cuadrática (p ≈ 2) cuando x_0 está suficientemente
    cerca de la raíz y J(x*) es no singular.

    Parámetros
    ----------
    F : callable
        Función vectorial F: R^n → R^n.  Recibe y devuelve array 1-D.
    J : callable
        Jacobiano  J: R^n → R^{n×n}.  Recibe array 1-D, devuelve 2-D.
    x0 : array_like
        Punto inicial (n componentes).
    tol : float
        Criterio de parada: ‖F(x_k)‖ < tol.
    max_iter : int
        Número máximo de iteraciones.
    verbose : bool
        Si True, imprime progreso iteración por iteración.

    Retorna
    -------
    dict con claves:
        'solucion'        : ndarray  — aproximación final x*
        'historial_x'     : list     — [x_0, x_1, …, x_k]
        'historial_norma' : list     — [‖F(x_0)‖, ‖F(x_1)‖, …]
        'iteraciones'     : int      — cantidad de iteraciones realizadas
        'evals_F'         : int      — evaluaciones totales de F
        'evals_J'         : int      — evaluaciones totales del Jacobiano
        'convergio'       : bool
    """
    x = np.array(x0, dtype=float)

    historial_x = [x.copy()]
    historial_norma = []
    evals_F = 0
    evals_J = 0

    if verbose:
        print(f"\n{'═'*60}")
        print(f"  NEWTON-RAPHSON")
        print(f"{'═'*60}")
        print(f"  x₀ = {np.array2string(x, precision=4)}")
        print(f"  {'Iter':>4s}  {'‖F(x)‖':>14s}")
        print(f"  {'─'*4}  {'─'*14}")

    for k in range(max_iter):
        # ── Paso 1: evaluar F(x_k) ──
        Fk = np.atleast_1d(np.asarray(F(x), dtype=float))
        evals_F += 1
        norma = np.linalg.norm(Fk)
        historial_norma.append(norma)

        if verbose:
            print(f"  {k:4d}  {norma:14.6e}")

        # ── Criterio de parada ──
        if norma < tol:
            if verbose:
                print(f"  ✓ Convergió en {k} iteraciones")
            return _resultado(x, historial_x, historial_norma,
                              k, evals_F, evals_J, True)

        # ── Paso 2: evaluar el Jacobiano J(x_k) ──
        # ¡Este es el paso CARO!  Necesitamos las n² derivadas parciales.
        Jk = np.atleast_2d(np.asarray(J(x), dtype=float))
        evals_J += 1

        # ── Paso 3: resolver J(x_k)·Δx = −F(x_k)  [O(n³)] ──
        dx = np.linalg.solve(Jk, -Fk)

        # ── Paso 4: actualizar x ──
        x = x + dx
        historial_x.append(x.copy())

    # ── No convergió ──
    Fk = np.atleast_1d(np.asarray(F(x), dtype=float))
    evals_F += 1
    historial_norma.append(np.linalg.norm(Fk))
    if verbose:
        print(f"  ✗ No convergió en {max_iter} iteraciones")
    return _resultado(x, historial_x, historial_norma,
                      max_iter, evals_F, evals_J, False)


# ═══════════════════════════════════════════════════════════════════════
#  BROYDEN  ("Good Broyden")
# ═══════════════════════════════════════════════════════════════════════

def broyden(F, x0, B0=None, tol=1e-10, max_iter=50, verbose=True):
    """
    Método de Broyden ("good Broyden") para sistemas no lineales F(x) = 0.

    Idea central:  en vez de recalcular el Jacobiano completo en cada
    iteración, Broyden ACTUALIZA una aproximación B_k ≈ J(x_k) usando
    información de la iteración anterior (ecuación de la secante).

    Fórmula de actualización de Broyden (mínima norma de Frobenius):
        B_{k+1} = B_k  +  (y_k − B_k s_k) s_kᵀ / (s_kᵀ s_k)

    donde  s_k = x_{k+1} − x_k,   y_k = F(x_{k+1}) − F(x_k).

    Para evitar resolver  B_{k+1}·Δx = −F  en cada paso [O(n³)],
    mantenemos directamente la inversa aproximada H_k ≈ B_k⁻¹ usando
    la fórmula de Sherman-Morrison:

        H_{k+1} = H_k + (s_k − H_k y_k)(s_kᵀ H_k) / (s_kᵀ H_k y_k)

    Esto reduce el costo por iteración de O(n³) a O(n²).

    Convergencia: superlineal (Teorema de Dennis-Moré) — más lenta que
    la cuadrática de Newton, pero con costo MUCHO menor por paso.

    Parámetros
    ----------
    F : callable
        Función vectorial F: R^n → R^n.
    x0 : array_like
        Punto inicial.
    B0 : array_like o None
        Aproximación inicial del Jacobiano.
        - None  → usa B_0 = I  (identidad).
        - array → típicamente J(x_0) para mejor convergencia.
    tol : float
        Criterio de parada: ‖F(x_k)‖ < tol.
    max_iter : int
        Número máximo de iteraciones.
    verbose : bool
        Si True, imprime progreso.

    Retorna
    -------
    dict — mismo formato que newton().
    """
    x = np.array(x0, dtype=float)
    n = len(x)

    # ── Inicializar H_0 = B_0⁻¹ ──
    if B0 is None:
        # B_0 = I  ⟹  H_0 = I
        H = np.eye(n)
        evals_J = 0
        b0_label = "I (identidad)"
    else:
        # B_0 = J(x_0)  ⟹  invertimos una sola vez al inicio
        H = np.linalg.inv(np.atleast_2d(np.asarray(B0, dtype=float)))
        evals_J = 1
        b0_label = "J(x₀)"

    historial_x = [x.copy()]
    historial_norma = []
    evals_F = 0

    # Evaluar F en el punto inicial
    Fk = np.atleast_1d(np.asarray(F(x), dtype=float))
    evals_F += 1

    if verbose:
        print(f"\n{'═'*60}")
        print(f"  BROYDEN")
        print(f"{'═'*60}")
        print(f"  x₀ = {np.array2string(x, precision=4)}")
        print(f"  B₀ = {b0_label}")
        print(f"  {'Iter':>4s}  {'‖F(x)‖':>14s}")
        print(f"  {'─'*4}  {'─'*14}")

    for k in range(max_iter):
        norma = np.linalg.norm(Fk)
        historial_norma.append(norma)

        if verbose:
            print(f"  {k:4d}  {norma:14.6e}")

        # ── Criterio de parada ──
        if norma < tol:
            if verbose:
                print(f"  ✓ Convergió en {k} iteraciones")
            return _resultado(x, historial_x, historial_norma,
                              k, evals_F, evals_J, True)

        # ── Calcular el paso:  Δx = −H_k · F(x_k)  ──
        # Acá está la ventaja clave: un simple producto matriz·vector O(n²)
        # reemplaza la resolución del sistema lineal O(n³) de Newton.
        sk = -H @ Fk

        # ── Actualizar x ──
        x_new = x + sk

        # ── Evaluar F en el nuevo punto ──
        F_new = np.atleast_1d(np.asarray(F(x_new), dtype=float))
        evals_F += 1

        # ── Calcular y_k = F(x_{k+1}) − F(x_k)  ──
        # s_k y y_k son los ingredientes de la ECUACIÓN DE LA SECANTE:
        # queremos que nuestra aproximación cumpla  B_{k+1} s_k = y_k,
        # que es el análogo multidimensional de  f'(x) ≈ Δf/Δx.
        yk = F_new - Fk

        # ══════════════════════════════════════════════════════════════
        #  ACTUALIZACIÓN DE SHERMAN-MORRISON
        # ══════════════════════════════════════════════════════════════
        #
        #  H_{k+1} = H_k  +  (s_k − H_k y_k)(s_kᵀ H_k)
        #                     ─────────────────────────────
        #                          s_kᵀ H_k y_k
        #
        #  Se obtiene aplicando la fórmula de Sherman-Morrison-Woodbury
        #  a la actualización de rango 1 de Broyden.
        #  Costo: O(n²) — dos productos matriz·vector + un outer product.
        # ══════════════════════════════════════════════════════════════

        Hyk = H @ yk           # H_k · y_k            → vector  (n,)
        sH  = sk @ H           # s_kᵀ · H_k           → vector  (n,)
        denominador = sH @ yk  # s_kᵀ · H_k · y_k     → escalar

        if abs(denominador) > 1e-14:
            # Numerador: (s_k − H_k y_k)(s_kᵀ H_k)  → matriz (n × n)
            H = H + np.outer(sk - Hyk, sH) / denominador

        # ── Avanzar ──
        x = x_new
        Fk = F_new
        historial_x.append(x.copy())

    # ── No convergió ──
    historial_norma.append(np.linalg.norm(Fk))
    if verbose:
        print(f"  ✗ No convergió en {max_iter} iteraciones")
    return _resultado(x, historial_x, historial_norma,
                      max_iter, evals_F, evals_J, False)


# ═══════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════════════

def _resultado(x, hist_x, hist_norma, iters, eF, eJ, ok):
    """Empaqueta los resultados en un dict estándar."""
    return {
        'solucion':        x.copy(),
        'historial_x':     hist_x,
        'historial_norma': hist_norma,
        'iteraciones':     iters,
        'evals_F':         eF,
        'evals_J':         eJ,
        'convergio':       ok,
    }


def imprimir_comparacion(res_newton, res_broyden):
    """
    Imprime tabla comparativa Newton vs Broyden en consola.
    Ideal para mostrar en vivo durante la exposición.
    """
    print(f"\n{'═'*62}")
    print(f"  COMPARACIÓN  NEWTON  vs  BROYDEN")
    print(f"{'═'*62}")
    print(f"  {'Métrica':<30s} {'Newton':>13s} {'Broyden':>13s}")
    print(f"  {'─'*30} {'─'*13} {'─'*13}")

    rn, rb = res_newton, res_broyden
    print(f"  {'Iteraciones':<30s} {rn['iteraciones']:>13d} {rb['iteraciones']:>13d}")
    print(f"  {'Evaluaciones de F':<30s} {rn['evals_F']:>13d} {rb['evals_F']:>13d}")
    print(f"  {'Evaluaciones de J':<30s} {rn['evals_J']:>13d} {rb['evals_J']:>13d}")
    print(f"  {'‖F(x*)‖ final':<30s} {rn['historial_norma'][-1]:>13.2e} {rb['historial_norma'][-1]:>13.2e}")

    def _si_no(b):
        return "Sí" if b else "No"
    print(f"  {'Convergió':<30s} {_si_no(rn['convergio']):>13s} {_si_no(rb['convergio']):>13s}")
    print(f"{'═'*62}\n")


def configurar_graficos():
    """
    Aplica un estilo limpio y legible a los gráficos de matplotlib.
    Pensado para que se vean bien proyectados en una presentación.
    """
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'figure.figsize':    (10, 6),
        'font.size':         13,
        'axes.titlesize':    15,
        'axes.titleweight':  'bold',
        'axes.labelsize':    13,
        'legend.fontsize':   12,
        'xtick.labelsize':   11,
        'ytick.labelsize':   11,
        'lines.linewidth':   2.0,
        'lines.markersize':  8,
        'figure.dpi':        100,
        'savefig.dpi':       150,
        'axes.grid':         True,
        'grid.alpha':        0.3,
    })
