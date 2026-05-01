// ================================================================
// PRÁCTICA N.° 3 — TABLAS HASH CON DATOS SINTÉTICOS DE E-COMMERCE
// Curso: Estructuras de Datos | Código: SIS319 | Semanas 5-6
// Universidad Nacional del Altiplano
// Mg. Aldo Hernán Zanabria Gálvez
//
// Métodos implementados:
//   1. Encadenamiento Separado
//   2. Sondeo Lineal
//   3. Doble Hashing
//
// Datos: sintéticos formato "user_XXXXX" (e-commerce)
// Compilar: g++ -O2 -std=c++17 -o hash_tabla hash_tabla.cpp
// Ejecutar:  ./hash_tabla
// ================================================================

#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <list>
#include <chrono>
#include <random>
#include <unordered_set>
#include <algorithm>
#include <cmath>

using namespace std;
using namespace std::chrono;

// ───────────────────────────────────────────────────────────────
// ESTRUCTURA: par clave-valor (simula registro e-commerce)
// ───────────────────────────────────────────────────────────────
struct Registro {
    string clave;   // e.g. "user_14382"
    string valor;   // campo auxiliar (país, email, etc.)
};

// ───────────────────────────────────────────────────────────────
// GENERADOR DE DATOS SINTÉTICOS DE E-COMMERCE
// Produce n claves únicas con formato "user_XXXXX"
// ───────────────────────────────────────────────────────────────
vector<Registro> generarClaves(int n = 10000, unsigned semilla = 42) {
    mt19937 rng(semilla);
    uniform_int_distribution<int> dist(10000, 300000);

    unordered_set<string> vistas;
    vector<Registro> datos;
    datos.reserve(n);

    while ((int)datos.size() < n) {
        string clave = "user_" + to_string(dist(rng));
        if (vistas.insert(clave).second) {          // clave única
            datos.push_back({clave, "ecommerce_record"});
        }
    }
    cout << "[Dataset] Claves unicas generadas: " << datos.size() << "\n";
    return datos;
}

// ───────────────────────────────────────────────────────────────
// FUNCIONES HASH
// h1(k) = Σ(k[i] * 31^i) mod m   — hash polinomial
// h2(k) = 1 + (h1(k) mod (m-1))  — segunda función (doble hashing)
// ───────────────────────────────────────────────────────────────
size_t hashH1(const string& clave, size_t m) {
    size_t h = 0;
    for (char c : clave)
        h = (h * 31 + (size_t)c) % m;
    return h;
}

size_t hashH2(const string& clave, size_t m) {
    // Garantiza h2(k) != 0 para toda clave
    size_t h = 0;
    for (char c : clave)
        h = (h * 31 + (size_t)c) % (m - 1);
    return 1 + h;
}

// ───────────────────────────────────────────────────────────────
// CLASE: Tabla Hash con Encadenamiento Separado
// Cada celda es una lista enlazada (std::list).
// Complejidad promedio: inserción O(1), búsqueda O(1 + λ).
// ───────────────────────────────────────────────────────────────
class TablaHashEncadenamiento {
public:
    size_t m;                           // Capacidad de la tabla
    vector<list<Registro>> tabla;       // Vector de listas enlazadas
    long long colisiones = 0;
    long long n = 0;

    explicit TablaHashEncadenamiento(size_t m) : m(m), tabla(m) {}

    void insertar(const Registro& reg) {
        size_t idx = hashH1(reg.clave, m);
        if (!tabla[idx].empty())        // Lista no vacía → colisión
            colisiones++;
        tabla[idx].push_back(reg);      // Agrega al final de la lista
        n++;
    }

    Registro* buscar(const string& clave) {
        size_t idx = hashH1(clave, m);
        for (auto& reg : tabla[idx])
            if (reg.clave == clave) return &reg;
        return nullptr;
    }

    double factorDeCarga() const { return (double)n / m; }
};

// ───────────────────────────────────────────────────────────────
// CLASE: Tabla Hash con Sondeo Lineal
// h(k,i) = (h1(k) + i) mod m
// Sufre agrupamiento primario cuando λ > 0.7.
// ───────────────────────────────────────────────────────────────
class TablaHashSondeoLineal {
    enum Estado { VACIO, OCUPADO, ELIMINADO };
public:
    size_t m;
    vector<Registro> tabla;
    vector<Estado>   estados;
    long long colisiones = 0;
    long long n = 0;

    explicit TablaHashSondeoLineal(size_t m)
        : m(m), tabla(m), estados(m, VACIO) {}

    bool insertar(const Registro& reg) {
        if (n >= (long long)m) return false;
        size_t idx   = hashH1(reg.clave, m);
        size_t pasos = 0;
        while (estados[idx] == OCUPADO) {
            colisiones++;
            idx = (idx + 1) % m;            // Sondeo: h(k,i)=(h(k)+i) mod m
            if (++pasos >= m) return false; // Evita ciclo infinito
        }
        tabla[idx]   = reg;
        estados[idx] = OCUPADO;
        n++;
        return true;
    }

    Registro* buscar(const string& clave) {
        size_t idx   = hashH1(clave, m);
        size_t pasos = 0;
        while (estados[idx] != VACIO) {
            if (estados[idx] == OCUPADO && tabla[idx].clave == clave)
                return &tabla[idx];
            idx = (idx + 1) % m;
            if (++pasos >= m) break;
        }
        return nullptr;
    }

    double factorDeCarga() const { return (double)n / m; }
};

// ───────────────────────────────────────────────────────────────
// CLASE: Tabla Hash con Doble Hashing
// h(k,i) = (h1(k) + i * h2(k)) mod m
// Elimina el agrupamiento primario. Requiere m primo.
// ───────────────────────────────────────────────────────────────
class TablaHashDobleHashing {
    enum Estado { VACIO, OCUPADO, ELIMINADO };
public:
    size_t m;
    vector<Registro> tabla;
    vector<Estado>   estados;
    long long colisiones = 0;
    long long n = 0;

    explicit TablaHashDobleHashing(size_t m)
        : m(m), tabla(m), estados(m, VACIO) {}

    bool insertar(const Registro& reg) {
        if (n >= (long long)m) return false;
        size_t h1    = hashH1(reg.clave, m);
        size_t h2    = hashH2(reg.clave, m);   // h2(k) = 1 + hash mod (m-1)
        size_t idx   = h1;
        size_t pasos = 0;
        while (estados[idx] == OCUPADO) {
            colisiones++;
            pasos++;
            idx = (h1 + pasos * h2) % m;       // h(k,i) = (h1+i*h2) mod m
            if (pasos >= m) return false;
        }
        tabla[idx]   = reg;
        estados[idx] = OCUPADO;
        n++;
        return true;
    }

    Registro* buscar(const string& clave) {
        size_t h1    = hashH1(clave, m);
        size_t h2    = hashH2(clave, m);
        size_t idx   = h1;
        size_t pasos = 0;
        while (estados[idx] != VACIO) {
            if (estados[idx] == OCUPADO && tabla[idx].clave == clave)
                return &tabla[idx];
            pasos++;
            idx = (h1 + pasos * h2) % m;
            if (pasos >= m) break;
        }
        return nullptr;
    }

    double factorDeCarga() const { return (double)n / m; }
};

// ───────────────────────────────────────────────────────────────
// UTILIDAD: microsegundos transcurridos desde t0
// ───────────────────────────────────────────────────────────────
using Clock = high_resolution_clock;
using TP    = time_point<Clock>;

inline double us(TP t0, TP t1) {
    return duration_cast<microseconds>(t1 - t0).count();
}

// ───────────────────────────────────────────────────────────────
// BENCHMARK COMPLETO
// Varía m ∈ {503,1009,2003,4001} y λ ∈ {0.3,0.5,0.7,0.9}
// → 16 experimentos × 3 métodos
// ───────────────────────────────────────────────────────────────
struct Fila {
    size_t m; double lambda; size_t n;
    long long col_enc;  double ins_enc_us;  double bus_enc_us;
    long long col_sl;   double ins_sl_us;   double bus_sl_us;
    long long col_dh;   double ins_dh_us;   double bus_dh_us;
};

vector<Fila> benchmark(const vector<Registro>& datos,
                       const vector<size_t>& tamanios,
                       const vector<double>& lambdas,
                       int n_busquedas = 200)
{
    vector<Fila> resultados;

    // Cabecera de la tabla
    cout << "\n" << string(105, '=') << "\n";
    cout << right
         << setw(6)  << "m"
         << setw(6)  << "lam"
         << setw(7)  << "n"
         << setw(10) << "Col_Enc"
         << setw(13) << "Ins_Enc(us)"
         << setw(10) << "Col_SL"
         << setw(12) << "Ins_SL(us)"
         << setw(10) << "Col_DH"
         << setw(12) << "Ins_DH(us)"
         << "\n";
    cout << string(105, '=') << "\n";

    mt19937 rng(99);

    for (size_t m : tamanios) {
        for (double lam : lambdas) {
            size_t n = min(datos.size(), (size_t)(m * lam));

            // Muestra de búsquedas
            size_t nb = min((size_t)n_busquedas, n);
            vector<size_t> idx_muestra(n);
            iota(idx_muestra.begin(), idx_muestra.end(), 0);
            shuffle(idx_muestra.begin(), idx_muestra.end(), rng);
            idx_muestra.resize(nb);

            // ── Encadenamiento ───────────────────────────────
            TablaHashEncadenamiento enc(m);
            auto t0 = Clock::now();
            for (size_t i = 0; i < n; i++) enc.insertar(datos[i]);
            auto t1 = Clock::now();
            double ins_enc = us(t0, t1);

            t0 = Clock::now();
            for (size_t i : idx_muestra) enc.buscar(datos[i].clave);
            t1 = Clock::now();
            double bus_enc = us(t0, t1) / nb;

            // ── Sondeo Lineal ────────────────────────────────
            TablaHashSondeoLineal sl(m);
            t0 = Clock::now();
            for (size_t i = 0; i < n; i++) sl.insertar(datos[i]);
            t1 = Clock::now();
            double ins_sl = us(t0, t1);

            t0 = Clock::now();
            for (size_t i : idx_muestra) sl.buscar(datos[i].clave);
            t1 = Clock::now();
            double bus_sl = us(t0, t1) / nb;

            // ── Doble Hashing ────────────────────────────────
            TablaHashDobleHashing dh(m);
            t0 = Clock::now();
            for (size_t i = 0; i < n; i++) dh.insertar(datos[i]);
            t1 = Clock::now();
            double ins_dh = us(t0, t1);

            t0 = Clock::now();
            for (size_t i : idx_muestra) dh.buscar(datos[i].clave);
            t1 = Clock::now();
            double bus_dh = us(t0, t1) / nb;

            // Imprime fila
            cout << right
                 << setw(6)  << m
                 << setw(6)  << fixed << setprecision(1) << lam
                 << setw(7)  << n
                 << setw(10) << enc.colisiones
                 << setw(13) << fixed << setprecision(1) << ins_enc
                 << setw(10) << sl.colisiones
                 << setw(12) << fixed << setprecision(1) << ins_sl
                 << setw(10) << dh.colisiones
                 << setw(12) << fixed << setprecision(1) << ins_dh
                 << "\n";

            resultados.push_back({
                m, lam, n,
                enc.colisiones, ins_enc, bus_enc,
                sl.colisiones,  ins_sl,  bus_sl,
                dh.colisiones,  ins_dh,  bus_dh
            });
        }
    }
    cout << string(105, '=') << "\n";
    return resultados;
}

// ───────────────────────────────────────────────────────────────
// FUNCIÓN PRINCIPAL
// ───────────────────────────────────────────────────────────────
int main() {
    cout << "================================================\n";
    cout << "  TABLAS HASH — Practica N.o 3 | SIS319\n";
    cout << "  Dataset: sintetico e-commerce (user_XXXXX)\n";
    cout << "================================================\n";

    // 1. Genera 10 000 claves únicas tipo e-commerce
    vector<Registro> datos = generarClaves(10000, 42);

    // 2. Parámetros del benchmark (según enunciado)
    vector<size_t> tamanios = {503, 1009, 2003, 4001};
    vector<double> lambdas  = {0.3, 0.5, 0.7, 0.9};

    // 3. Ejecuta 16 experimentos × 3 métodos
    vector<Fila> resultados = benchmark(datos, tamanios, lambdas, 200);

    // 4. Resumen por método fijando m=1009 (Figura 1 del informe)
    cout << "\n--- Resumen: colisiones para m=1009 ---\n";
    cout << setw(6) << "lam"
         << setw(10) << "Col_Enc"
         << setw(10) << "Col_SL"
         << setw(10) << "Col_DH" << "\n";
    for (const auto& f : resultados) {
        if (f.m == 1009) {
            cout << setw(6)  << fixed << setprecision(1) << f.lambda
                 << setw(10) << f.col_enc
                 << setw(10) << f.col_sl
                 << setw(10) << f.col_dh << "\n";
        }
    }

    // 5. Resumen tiempos de inserción para λ=0.7 (Figura 2 del informe)
    cout << "\n--- Resumen: insercion (us) para lambda=0.7 ---\n";
    cout << setw(6) << "m"
         << setw(14) << "Ins_Enc(us)"
         << setw(13) << "Ins_SL(us)"
         << setw(13) << "Ins_DH(us)" << "\n";
    for (const auto& f : resultados) {
        if (abs(f.lambda - 0.7) < 1e-9) {
            cout << setw(6)  << f.m
                 << setw(14) << fixed << setprecision(1) << f.ins_enc_us
                 << setw(13) << fixed << setprecision(1) << f.ins_sl_us
                 << setw(13) << fixed << setprecision(1) << f.ins_dh_us
                 << "\n";
        }
    }

    cout << "\nEjecucion completada.\n";
    return 0;
}
