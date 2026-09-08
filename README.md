# Método de Broyden — Proyecto de Exposición
## Métodos Numéricos II

Guía rápida y guion de apoyo para la presentación oral y demostración en vivo del **Método de Broyden** (método cuasi-Newton de rango 1) frente al método clásico de **Newton-Raphson**.

---

### Requisitos

- **Entorno:** Python 3.8 o superior
- **Bibliotecas requeridas:** `numpy`, `matplotlib`
- **Instalación:**
  ```bash
  pip install numpy matplotlib
  ```
- **Ejecución de los ejercicios:**
  ```bash
  python metodos.py
  python ejercicio1_newton_vs_broyden.py
  python ejercicio2_convergencia.py
  python ejercicio3_cinematica_inversa.py
  python ejercicio4_bratu.py
  ```

---

### Estructura del Proyecto

- [`metodos.py`](metodos.py): **Módulo central del proyecto.** Contiene las implementaciones desde cero de `newton` (con resolución matricial $O(n^3)$) y `broyden` ("Good Broyden" con actualización directa de la inversa vía Sherman-Morrison en $O(n^2)$), además de utilidades de formato (`imprimir_comparacion`, `configurar_graficos`).
- [`ejercicio1_newton_vs_broyden.py`](ejercicio1_newton_vs_broyden.py): Comparación directa cara a cara en un sistema $2 \times 2$ (intersección círculo–hipérbola). Muestra las trayectorias espaciales y el conteo de evaluaciones.
- [`ejercicio2_convergencia.py`](ejercicio2_convergencia.py): Estudio experimental del orden de convergencia. Verificación de la convergencia cuadrática ($p \approx 2$) vs. superlineal ($1 < p < 2$).
- [`ejercicio3_cinematica_inversa.py`](ejercicio3_cinematica_inversa.py): Aplicación en ingeniería: cinemática inversa de un manipulador robótico articular 2D. Demuestra la utilidad de Broyden cuando derivar el Jacobiano es laborioso.
- [`ejercicio4_bratu.py`](ejercicio4_bratu.py): Escalabilidad en sistemas de alta dimensión ($n$ grande) modelando el problema no lineal de transferencia de calor y combustión (Ecuación de Bratu).
- [`README.md`](README.md): Este documento; guion didáctico y resumen conceptual para la exposición.

---

### Guion de Exposición

A continuación se detalla la guía paso a paso para exponer cada uno de los ejercicios durante la presentación:

---

#### Ejercicio 1 — Newton vs. Broyden cara a cara

- **Qué muestra:**
  Compara el comportamiento de ambos métodos en el plano $\mathbb{R}^2$ resolviendo la intersección de un círculo y una hipérbola partiendo desde el mismo punto inicial $x_0$.
- **Qué parte de la teoría ilustra:**
  - La **ecuación de la secante multidimensional**: $B_{k+1} s_k = y_k$.
  - La **actualización de rango 1 de Broyden**: corrección de mínima norma de Frobenius que preserva la información en direcciones ortogonales a $s_k$.
  - El ahorro de evaluaciones de derivadas parciales: Newton recalcula $n^2 = 4$ derivadas por paso; Broyden solo evalúa $F(x)$.
- **Qué decir durante la exposición:**
  - *"Observen que Newton toma una trayectoria más directa hacia la raíz porque calcula el gradiente exacto en cada punto, necesitando menos iteraciones."*
  - *"Sin embargo, Broyden, sin calcular una sola derivada después del punto inicial, ajusta su matriz de aproximación usando únicamente las diferencias de funciones y posiciones ($s_k$ y $y_k$)."*
  - *"Miren la tabla en consola: aunque Broyden requirió un par de iteraciones extra, el número de evaluaciones del Jacobiano fue de solo 1 frente a múltiples llamadas en Newton."*
- **Gráfico clave:**
  - **Plano de fases con curvas de nivel y trayectorias ($x_1$ vs. $x_2$):** señalar cómo los saltos de Newton son estrictamente ortogonales a las tangentes locales, mientras que Broyden 'aprende' la curvatura paso a paso construyendo una trayectoria suave hacia la intersección.

---

#### Ejercicio 2 — Convergencia superlineal

- **Qué muestra:**
  Calcula y grafica empíricamente el orden de convergencia $p$ a partir de la evolución del error $e_k = \|x_k - x^*\|$, contrastando la tasa cuadrática de Newton con la tasa superlineal de Broyden.
- **Qué parte de la teoría ilustra:**
  - **Teorema de Dennis-Moré (1974):** condición necesaria y suficiente para la convergencia superlineal en métodos cuasi-Newton ($\lim \frac{\|(B_k - J(x^*))s_k\|}{\|s_k\|} = 0$).
  - Diferencia asintótica entre convergencia cuadrática ($\|e_{k+1}\| \le C \|e_k\|^2$) y superlineal ($\|e_{k+1}\| / \|e_k\| \to 0$).
- **Qué decir durante la exposición:**
  - *"Newton duplica la cantidad de dígitos de precisión en cada iteración final; por eso en la gráfica semilogarítmica el error de Newton cae como una parábola hacia abajo (convergencia cuadrática, $p \approx 2$)."*
  - *"Broyden no alcanza $p = 2$ porque la matriz $B_k$ no converge al Jacobiano exacto en todas las direcciones del espacio, sino solo a lo largo de las direcciones de los pasos realizados (principio de Dennis-Moré)."*
  - *"Aun así, la pendiente de Broyden es notablemente más pronunciada que una línea recta: es superlineal, lo que significa que acelera en cada paso sin pagar el costo de un Jacobiano completo."*
- **Gráfico clave:**
  - **Evolución del error $\log_{10}(\|F(x_k)\|)$ vs. Iteraciones y estimador empírico de $p_k$:** destacar la caída vertical de Newton en las últimas 2 iteraciones frente a la aceleración progresiva de Broyden.

---

#### Ejercicio 3 — Cinemática inversa

- **Qué muestra:**
  Aplica el método de Broyden al problema geométrico de controlar un brazo robótico articulado para alcanzar coordenadas objetivo en el espacio de trabajo a partir de los ángulos de sus articulaciones $(\theta_1, \theta_2)$.
- **Qué parte de la teoría ilustra:**
  - Ventaja práctica del método cuando el modelo físico es complejo o cuando no se dispone de expresiones analíticas sencillas para el Jacobiano cinemático.
  - Robustez de la inicialización $B_0 = I$ o $B_0 = J(\theta_0)$ en aplicaciones de control y gráficos interactivos.
- **Qué decir durante la exposición:**
  - *"En robótica y videojuegos, la cinemática directa (calcular la posición a partir de los ángulos) es trivial mediante trigonometría, pero la cinemática inversa (encontrar los ángulos para una posición deseada) es un sistema fuertemente no lineal."*
  - *"En un bucle de control a 60 FPS o en tiempo real, calcular e invertir el Jacobiano analítico en cada instante es computacionalmente prohibitivo."*
  - *"Broyden ajusta el efector final moviendo las articulaciones y corrigiendo la matriz basándose únicamente en el desplazamiento observado del extremo del robot."*
- **Gráfico clave:**
  - **Esquema del brazo robótico (eslabones y articulaciones):** mostrar la configuración inicial del robot, los pasos intermedios de las articulaciones y cómo el extremo alcanza con precisión milimétrica el punto objetivo marcado con una estrella.

---

#### Ejercicio 4 — Ecuación de Bratu

- **Qué muestra:**
  Evalúa el desempeño de ambos métodos sobre la discretización por diferencias finitas de la Ecuación de Bratu ($-\Delta u = \lambda e^u$), generando sistemas no lineales grandes con $n$ desde decenas hasta cientos de variables.
- **Qué parte de la teoría ilustra:**
  - La barrera del costo computacional: Newton requiere resolver un sistema lineal de tamaño $n \times n$ en cada paso con costo $O(n^3)$ (o $O(n^2)$ con solvers esparsos), además de evaluar $n^2$ derivadas parciales.
  - La **fórmula de Sherman-Morrison**: permite actualizar directamente la inversa del Jacobiano $H_k \approx B_k^{-1}$ con costo estricto de $O(n^2)$ mediante multiplicaciones matriz–vector y productos externos.
- **Qué decir durante la exposición:**
  - *"Para $n=2$, Newton siempre parece más rápido porque hace menos iteraciones. Pero la verdadera prueba de un algoritmo numérico está en la escalabilidad cuando $n$ crece."*
  - *"La ecuación de Bratu modela fenómenos de combustión térmica donde $u$ representa la temperatura en un medio reactivo."*
  - *"Miren el gráfico de barras de tiempo total: aunque Broyden hace más iteraciones que Newton, cada iteración de Broyden cuesta $O(n^2)$ operaciones frente a $O(n^3)$ de Newton. A partir de cierto $n$, Broyden supera ampliamente a Newton en tiempo de reloj."*
- **Gráfico clave:**
  - **Gráfico de barras comparativo (Tiempo de ejecución CPU vs. Tamaño del sistema $n$):** señalar cómo la barra de Newton crece de forma exponencial/cúbica mientras que la de Broyden escala suavemente.

---

### Resumen del Trade-off Central

| Característica | Newton-Raphson | Broyden ("Good Broyden") |
| :--- | :--- | :--- |
| **Tipo de Convergencia** | **Cuadrática** ($p = 2$) | **Superlineal** ($1 < p < 2$) |
| **Costo por Iteración** | Alto: $O(n^3)$ (resolver $J \Delta x = -F$) | Bajo: $O(n^2)$ (Sherman-Morrison) |
| **Evaluaciones de Derivadas** | $n^2$ derivadas parciales por iteración | **0** derivadas (tras inicializar $B_0$) |
| **Sensibilidad a la Dimensión $n$** | Escala mal para matrices densas grandes | Escala de manera eficiente en $O(n^2)$ |
| **Número de Iteraciones** | Mínimo (usualmente 4 a 6) | Moderado (usualmente 6 a 12) |
| **Veredicto Práctico** | Óptimo para $n$ pequeño y $J(x)$ fácil de evaluar | **Ganador en sistemas grandes o cuando derivar $F$ es costoso** |

> **Mensaje de cierre para la presentación:**  
> *"Newton es el velocista que requiere un esfuerzo enorme en cada zancada; Broyden es el fondista eficiente que, dando pasos mucho más económicos, llega a la meta en menos tiempo total cuando el camino es largo."*
