# ================================================================
# PRÁCTICA N.° 3 — TABLAS HASH CON DATOS SINTÉTICOS DE E-COMMERCE
# Curso: Estructuras de Datos | Código: SIS319 | Semanas 5-6
# Universidad Nacional del Altiplano
# Mg. Aldo Hernán Zanabria Gálvez
#
# Métodos implementados:
#   1. Encadenamiento Separado
#   2. Sondeo Lineal
#   3. Doble Hashing
#   4. dict nativo Python (referencia)
#
# Datos: sintéticos formato "user_XXXXX" (e-commerce)
# Ejecutar: python hash_tabla.py
# ================================================================

import random
import time
import matplotlib.pyplot as plt


# ───────────────────────────────────────────────────────────────
# 1. GENERADOR DE DATOS SINTÉTICOS DE E-COMMERCE
# ───────────────────────────────────────────────────────────────
def generar_claves(n: int = 10_000, semilla: int = 42) -> list:
    """
    Genera n claves únicas con formato 'user_XXXXX' que simulan
    CustomerIDs de un dataset de e-commerce (tipo Kaggle carrie1).
    """
    random.seed(semilla)
    claves = set()
    while len(claves) < n:
        claves.add(f"user_{random.randint(10_000, 300_000):05d}")
    claves = list(claves)
    print(f"[Dataset] Claves únicas generadas: {len(claves)}")
    return claves


# ───────────────────────────────────────────────────────────────
# 2. FUNCIÓN HASH POLINOMIAL (compartida por todos los métodos)
#    h1(k) = Σ(ord(k[i]) * 31^i) mod m
# ───────────────────────────────────────────────────────────────
def hash_h1(clave: str, m: int) -> int:
    """Función hash polinomial con base 31."""
    h = 0
    for c in str(clave):
        h = (h * 31 + ord(c)) % m
    return h


def hash_h2(clave: str, m: int) -> int:
    """
    Segunda función hash para doble hashing.
    h2(k) = 1 + (h_polinomial(k) mod (m-1))
    Garantiza h2(k) != 0 para toda clave.
    """
    h = 0
    for c in str(clave):
        h = (h * 31 + ord(c)) % (m - 1)
    return 1 + h


# ───────────────────────────────────────────────────────────────
# 3. TABLA HASH — ENCADENAMIENTO SEPARADO
# ───────────────────────────────────────────────────────────────
class TablaHashEncadenamiento:
    """
    Cada celda contiene una lista enlazada (lista Python) con todos
    los elementos que producen el mismo índice hash.
    Complejidad promedio: inserción O(1), búsqueda O(1 + λ).
    """

    def __init__(self, m: int):
        self.m = m                          # Capacidad de la tabla
        self.tabla = [[] for _ in range(m)] # Lista de listas (cadenas)
        self.colisiones = 0                 # Contador de colisiones
        self.n = 0                          # Elementos insertados

    def insertar(self, clave: str, valor=None) -> None:
        idx = hash_h1(clave, self.m)
        if self.tabla[idx]:                 # Cadena no vacía → colisión
            self.colisiones += 1
        self.tabla[idx].append((clave, valor))
        self.n += 1

    def buscar(self, clave: str):
        idx = hash_h1(clave, self.m)
        for k, v in self.tabla[idx]:
            if k == clave:
                return v
        return None

    def factor_de_carga(self) -> float:
        return self.n / self.m


# ───────────────────────────────────────────────────────────────
# 4. TABLA HASH — SONDEO LINEAL
#    Secuencia: h(k, i) = (h1(k) + i) mod m
# ───────────────────────────────────────────────────────────────
class TablaHashSondeoLineal:
    """
    Direccionamiento abierto con sondeo lineal.
    Sufre agrupamiento primario cuando λ > 0.7.
    Complejidad promedio: O(1/(1-λ)).
    """
    _ELIMINADO = "__ELIMINADO__"

    def __init__(self, m: int):
        self.m = m
        self.tabla = [None] * m
        self.colisiones = 0
        self.n = 0

    def insertar(self, clave: str, valor=None) -> bool:
        if self.n >= self.m:
            return False                    # Tabla completamente llena
        idx = hash_h1(clave, self.m)
        pasos = 0
        while (self.tabla[idx] is not None
               and self.tabla[idx] != self._ELIMINADO):
            self.colisiones += 1
            idx = (idx + 1) % self.m        # h(k,i) = (h(k)+i) mod m
            pasos += 1
            if pasos >= self.m:
                return False                # No hay espacio
        self.tabla[idx] = (clave, valor)
        self.n += 1
        return True

    def buscar(self, clave: str):
        idx = hash_h1(clave, self.m)
        pasos = 0
        while self.tabla[idx] is not None:
            if (self.tabla[idx] != self._ELIMINADO
                    and self.tabla[idx][0] == clave):
                return self.tabla[idx][1]
            idx = (idx + 1) % self.m
            pasos += 1
            if pasos >= self.m:
                break
        return None

    def factor_de_carga(self) -> float:
        return self.n / self.m


# ───────────────────────────────────────────────────────────────
# 5. TABLA HASH — DOBLE HASHING
#    Secuencia: h(k, i) = (h1(k) + i * h2(k)) mod m
# ───────────────────────────────────────────────────────────────
class TablaHashDobleHashing:
    """
    Direccionamiento abierto con doble hashing.
    Elimina el agrupamiento primario del sondeo lineal.
    Requiere m primo y h2(k) != 0 para toda clave.
    """

    def __init__(self, m: int):
        self.m = m
        self.tabla = [None] * m
        self.colisiones = 0
        self.n = 0

    def insertar(self, clave: str, valor=None) -> bool:
        if self.n >= self.m:
            return False
        h1 = hash_h1(clave, self.m)
        h2 = hash_h2(clave, self.m)         # h2(k) = 1 + hash(k) mod (m-1)
        idx = h1
        pasos = 0
        while self.tabla[idx] is not None:
            self.colisiones += 1
            pasos += 1
            idx = (h1 + pasos * h2) % self.m  # h(k,i) = (h1+i*h2) mod m
            if pasos >= self.m:
                return False
        self.tabla[idx] = (clave, valor)
        self.n += 1
        return True

    def buscar(self, clave: str):
        h1 = hash_h1(clave, self.m)
        h2 = hash_h2(clave, self.m)
        idx = h1
        pasos = 0
        while self.tabla[idx] is not None:
            if self.tabla[idx][0] == clave:
                return self.tabla[idx][1]
            pasos += 1
            idx = (h1 + pasos * h2) % self.m
            if pasos >= self.m:
                break
        return None

    def factor_de_carga(self) -> float:
        return self.n / self.m


# ───────────────────────────────────────────────────────────────
# 6. BENCHMARK COMPLETO
#    Varía m en {503, 1009, 2003, 4001} y λ en {0.3, 0.5, 0.7, 0.9}
# ───────────────────────────────────────────────────────────────
def benchmark_completo(claves: list,
                        tamanios: list = None,
                        lambdas: list = None) -> list:
    """
    Ejecuta 16 experimentos (4 m × 4 λ) para los tres métodos.
    Registra colisiones, tiempo de inserción y tiempo de búsqueda.
    """
    if tamanios is None:
        tamanios = [503, 1009, 2003, 4001]
    if lambdas is None:
        lambdas = [0.3, 0.5, 0.7, 0.9]

    N_BUSQUEDAS = 200   # Muestra de búsquedas por experimento
    resultados = []

    print("\n" + "=" * 95)
    print(f"{'m':>6} {'λ':>5} {'n':>6}  "
          f"{'Col_Enc':>8} {'Ins_Enc(ms)':>11}  "
          f"{'Col_SL':>8} {'Ins_SL(ms)':>10}  "
          f"{'Col_DH':>8} {'Ins_DH(ms)':>10}")
    print("=" * 95)

    for m in tamanios:
        for lam in lambdas:
            n = min(len(claves), int(m * lam))
            subclaves = claves[:n]
            muestra = random.sample(subclaves, min(N_BUSQUEDAS, n))

            # ── Encadenamiento ──────────────────────────────────
            enc = TablaHashEncadenamiento(m)
            t0 = time.perf_counter()
            for c in subclaves:
                enc.insertar(c)
            t_ins_enc = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            for c in muestra:
                enc.buscar(c)
            t_bus_enc = (time.perf_counter() - t0) * 1e6 / len(muestra)

            # ── Sondeo Lineal ───────────────────────────────────
            sl = TablaHashSondeoLineal(m)
            t0 = time.perf_counter()
            for c in subclaves:
                sl.insertar(c)
            t_ins_sl = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            for c in muestra:
                sl.buscar(c)
            t_bus_sl = (time.perf_counter() - t0) * 1e6 / len(muestra)

            # ── Doble Hashing ───────────────────────────────────
            dh = TablaHashDobleHashing(m)
            t0 = time.perf_counter()
            for c in subclaves:
                dh.insertar(c)
            t_ins_dh = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            for c in muestra:
                dh.buscar(c)
            t_bus_dh = (time.perf_counter() - t0) * 1e6 / len(muestra)

            fila = {
                "m": m, "lambda": lam, "n": n,
                "col_enc": enc.colisiones, "ins_enc": round(t_ins_enc, 3),
                "bus_enc": round(t_bus_enc, 3),
                "col_sl":  sl.colisiones,  "ins_sl":  round(t_ins_sl,  3),
                "bus_sl":  round(t_bus_sl,  3),
                "col_dh":  dh.colisiones,  "ins_dh":  round(t_ins_dh,  3),
                "bus_dh":  round(t_bus_dh,  3),
            }
            resultados.append(fila)
            print(f"{m:>6} {lam:>5} {n:>6}  "
                  f"{enc.colisiones:>8} {t_ins_enc:>11.3f}  "
                  f"{sl.colisiones:>8}  {t_ins_sl:>9.3f}  "
                  f"{dh.colisiones:>8}  {t_ins_dh:>9.3f}")

    print("=" * 95)
    return resultados


# ───────────────────────────────────────────────────────────────
# 7. GRÁFICOS (Figuras 1, 2 y 3 del informe)
# ───────────────────────────────────────────────────────────────
def graficar(resultados: list) -> None:
    """Genera los tres gráficos requeridos por el trabajo de investigación."""

    tamanios = [503, 1009, 2003, 4001]
    lambdas  = [0.3, 0.5, 0.7, 0.9]
    colores  = {"Encadenamiento": "royalblue",
                "Sondeo Lineal":  "tomato",
                "Doble Hashing":  "seagreen"}

    # ── Figura 1: Colisiones vs λ para m=1009 ──────────────────
    m_fig1 = 1009
    sub = [r for r in resultados if r["m"] == m_fig1]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["lambda"] for r in sub], [r["col_enc"] for r in sub],
            "o-", color=colores["Encadenamiento"], label="Encadenamiento")
    ax.plot([r["lambda"] for r in sub], [r["col_sl"]  for r in sub],
            "s-", color=colores["Sondeo Lineal"],  label="Sondeo Lineal")
    ax.plot([r["lambda"] for r in sub], [r["col_dh"]  for r in sub],
            "^-", color=colores["Doble Hashing"],  label="Doble Hashing")
    ax.set_title(f"Colisiones vs Factor de Carga (m = {m_fig1})")
    ax.set_xlabel("Factor de carga (λ)")
    ax.set_ylabel("Número de colisiones")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("fig1_colisiones_vs_lambda.png", dpi=150)
    print("Guardado: fig1_colisiones_vs_lambda.png")
    plt.show()

    # ── Figura 2: Tiempo de inserción vs m para λ=0.7 ──────────
    lam_fig2 = 0.7
    sub = [r for r in resultados if r["lambda"] == lam_fig2]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["m"] for r in sub], [r["ins_enc"] for r in sub],
            "o-", color=colores["Encadenamiento"], label="Encadenamiento")
    ax.plot([r["m"] for r in sub], [r["ins_sl"]  for r in sub],
            "s-", color=colores["Sondeo Lineal"],  label="Sondeo Lineal")
    ax.plot([r["m"] for r in sub], [r["ins_dh"]  for r in sub],
            "^-", color=colores["Doble Hashing"],  label="Doble Hashing")
    ax.set_title(f"Tiempo de Inserción vs Tamaño de Tabla (λ = {lam_fig2})")
    ax.set_xlabel("Tamaño de tabla (m)")
    ax.set_ylabel("Tiempo de inserción (ms)")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("fig2_insercion_vs_m.png", dpi=150)
    print("Guardado: fig2_insercion_vs_m.png")
    plt.show()

    # ── Figura 3: Tiempo de búsqueda vs λ para m=2003 ──────────
    m_fig3 = 2003
    sub = [r for r in resultados if r["m"] == m_fig3]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["lambda"] for r in sub], [r["bus_enc"] for r in sub],
            "o-", color=colores["Encadenamiento"], label="Encadenamiento")
    ax.plot([r["lambda"] for r in sub], [r["bus_sl"]  for r in sub],
            "s-", color=colores["Sondeo Lineal"],  label="Sondeo Lineal")
    ax.plot([r["lambda"] for r in sub], [r["bus_dh"]  for r in sub],
            "^-", color=colores["Doble Hashing"],  label="Doble Hashing")
    ax.set_title(f"Tiempo de Búsqueda Promedio vs λ (m = {m_fig3})")
    ax.set_xlabel("Factor de carga (λ)")
    ax.set_ylabel("Tiempo promedio de búsqueda (μs/op)")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("fig3_busqueda_vs_lambda.png", dpi=150)
    print("Guardado: fig3_busqueda_vs_lambda.png")
    plt.show()


# ───────────────────────────────────────────────────────────────
# 8. EJECUCIÓN PRINCIPAL
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  TABLAS HASH — Práctica N.° 3 | SIS319")
    print("  Dataset: sintético e-commerce (user_XXXXX)")
    print("=" * 60)

    # Genera 10 000 claves únicas tipo e-commerce
    claves = generar_claves(n=10_000, semilla=42)

    # Ejecuta benchmark: 16 experimentos por método
    resultados = benchmark_completo(
        claves,
        tamanios=[503, 1009, 2003, 4001],
        lambdas=[0.3, 0.5, 0.7, 0.9]
    )

    # Genera los tres gráficos del informe
    graficar(resultados)
