# Resumen del Trabajo de Luna — Sprint 2

## Objetivo General

Luna esta construyendo un **pipeline de datos** para predecir inequidades en el transporte publico en **Miami-Dade County**. El objetivo final es identificar que census tracts (zonas) tienen mayor necesidad de mejoras en transito y por que.

---

## Que Hizo Luna (Commits Recientes)

### Sprint 2a: Indicadores de Equidad Compuestos (COMPLETADO)
**Notebook:** `Sprint 2/Sprint 2a/Sprint2a_Composite_Equity_Indicators_v3.ipynb`

Creo **7 indicadores de equidad** a nivel de census tract cruzando 3 fuentes de datos:

| # | Indicador | Que Mide |
|---|-----------|----------|
| 1 | Transit Dependency | Que tan dependiente es una zona del transito publico (sin carro + sin alternativas) |
| 2 | Temporal Mismatch | Si el servicio de buses existe cuando la gente lo necesita (noches, fines de semana) |
| 3 | Structural Access Gap | Diferencia entre empleos accesibles por carro vs transito (la brecha estructural) |
| 4 | Time Tax | Cuanto tiempo extra pierde una persona usando transito vs carro para llegar al trabajo |
| 5 | Service Coverage | Cantidad y calidad de paradas, rutas y viajes en cada zona |
| 6 | Economic Vulnerability | Pobreza + SNAP + carga de renta + desempleo combinados |
| 7 | Multimodal Deficit | Falta de opciones combinadas (transito + bici + caminar) |

**Resultado:** Un score final de equidad (`equity_priority_score`) y una clasificacion en 4 tiers:
- **Critical:** 53 tracts (10.2%)
- **High:** 104 tracts (19.9%)
- **Moderate:** 156 tracts (29.9%)
- **Low:** 209 tracts (40.0%)

---

### Sprint 2b: Feature Engineering para Modelado (EN PROGRESO)
**Notebook:** `Sprint 2/Sprint2b_Feature_Engineering.ipynb`

Toma los indicadores de 2a y les agrega features adicionales para alimentar modelos de ML. El proceso:

1. **Spatial Join** — Asigna cada parada de bus a un census tract usando geometrias del GeoPackage
2. **GTFS Features** — Extrae metricas del schedule de transito:
   - Headways (minutos entre buses)
   - Service span (horas de operacion)
   - Frecuencia por banda horaria
   - Brecha fin de semana vs dia de semana
   - Diversidad de rutas, accesibilidad en silla de ruedas
3. **ACS Trend Slopes** — Regresion lineal por tract en 5 anos (2019-2023) para capturar tendencias (pobreza subiendo, vehiculos bajando, etc.)
4. **Spatial Features** — Score promedio de equidad de tracts vecinos
5. **Interaction Terms** — Cruces como `pobreza × pocas horas de servicio`
6. **Validacion** — 8 checks automatizados (sin NaN, sin duplicados, sin features redundantes)

**Output:** `Sprint2b_Modeling_Features_NotebookOutput.csv` — **504 tracts × 67 columnas**, listo para modelar.

---

## Datos que Usa

### 1. ACS Census Data (American Community Survey)
**Ubicacion:** `Sprint 2/ACS Tract Level Data/`

| Archivo | Descripcion |
|---------|-------------|
| `ACS_MiamiDade_Tracts_2019.csv` | 520 tracts (boundaries 2010) |
| `ACS_MiamiDade_Tracts_2020.csv` | 708 tracts (boundaries 2020) |
| `ACS_MiamiDade_Tracts_2021.csv` | 708 tracts |
| `ACS_MiamiDade_Tracts_2022.csv` | 708 tracts |
| `ACS_MiamiDade_Tracts_2023.csv` | 708 tracts |
| `Census_MiamiDade_Tracts_Combined.csv` | Combinado multi-anual |
| `Clean_Census_MiamiDade_Tracts_Combined.csv` | Limpio con flags derivados |
| `DP03_MiamiDade_Tracts.csv` | Perfil economico detallado |
| `DP04_MiamiDade_Tracts.csv` | Perfil de vivienda detallado |
| `DP05_MiamiDade_Tracts.csv` | Perfil demografico detallado |

**Variables clave (46 por ano):**
- Empleo: tasa de desempleo, tasa de empleo
- Commute: % transito publico, % carro solo, % WFH, tiempo promedio
- Ingreso: mediana household income, per capita income, 10 brackets
- Pobreza: poverty rate
- Vehiculos: % sin carro, % 1 carro, % 2+
- Vivienda: % owner vs renter, renta mediana, carga de renta
- Demografia: poblacion, edad mediana, % <18, % 65+, % Hispanic, % Black, % foreign born

### 2. GTFS (General Transit Feed Specification)
**Ubicacion:** `Sprint 1 EDAs/transit_data.xlsx`

Datos del schedule de **Miami-Dade Transit**:
- **943K registros** de stop_times (llegadas/salidas)
- **6,530 paradas** de bus/tren
- **128 rutas**
- **calendar** con service_ids para weekday/saturday/sunday

### 3. GeoPackage — AllAccess MPO Data
**Ubicacion:** `MiamiDadeMpoAllAccessGpkg-expanded/`

Datos de accesibilidad del Metropolitan Planning Organization:
- **36,507 census blocks** con geometrias
- Isocronas de acceso a empleos por modo:
  - `au_2021_08.gpkg` — Auto, 30 min
  - `tr_2021_0700-0859-avg.gpkg` — Transito, hora pico AM
  - `bi_2021_1200_lts1.gpkg` — Bicicleta (stress bajo), 10 min (proxy para caminar)

### 4. Crosswalk 2010-2020
**Archivo:** `Sprint 2/tab20_tract20_tract10_st12.txt`

Mapeo de boundaries de census tracts de 2010 a 2020 (necesario porque 2019 ACS usa boundaries viejos). Usa area-weighted mapping para alinear los datos.

---

## Estructura de Archivos

```
Sprint 2/
├── README.md
├── Sprint 2a/
│   ├── Sprint2a_Composite_Equity_Indicators_v3.ipynb   ← 7 indicadores de equidad
│   ├── Sprint2a_Equity_Indicators_v3_tract.csv         ← Output: 512 tracts × 43 cols
│   └── Sprint2a_Equity_Results_Overview_v3.xlsx        ← Resumen en Excel (4 hojas)
├── Sprint2b_Feature_Engineering.ipynb                  ← Feature engineering para ML
├── Sprint2b_Modeling_Features_NotebookOutput.csv       ← Output: 504 tracts × 67 cols
├── tab20_tract20_tract10_st12.txt                      ← Crosswalk census boundaries
└── ACS Tract Level Data/
    ├── ACS_MiamiDade_Tracts_{2019-2023}.csv            ← 5 anos de datos ACS
    ├── Census_MiamiDade_Tracts_Combined.csv
    ├── Clean_Census_MiamiDade_Tracts_Combined.csv
    ├── DP03/DP04/DP05_MiamiDade_Tracts.csv             ← Tablas detalladas
    └── EDA_ACS_Tract_Level_MiamiDade.ipynb             ← EDA exploratorio
```

---

## Bugs que Corrigio (v2 → v3)

| Bug | Problema | Fix |
|-----|----------|-----|
| Census sentinels | Valores -666666666 del Census API pasaban como numeros reales | Reemplazar con NaN antes de cualquier calculo |
| Weekend ratio | Dividía weekday arrivals entre 5 (pensando Mon-Fri sumados), pero GTFS ya da un dia | Quitar la division por 5 |
| Duplicate tracts | Spatial join creaba filas duplicadas por casos de borde | `drop_duplicates` al final |
| Multicollinear bands | 5 bandas de headway con r>0.96 entre si | Colapsar a solo `peak_am` y `early` |
| bike_friendly_pct | r=1.000 con wheelchair_pct (son identicos en Miami GTFS) | Eliminar bike_friendly_pct |
| Headsign fill | Tracts sin transito tenian mediana en vez de 0 | Cambiar a fillna(0) |

---

## Que Falta (Proximo)

Segun su `todo.md`, lo que sigue en Sprint 2b:
- **2b.4:** Modelo de regresion (coeficientes interpretables)
- **2b.5:** Modelo ML (XGBoost/LightGBM para simulacion)
- **2b.6:** Risk scoring (identificar tracts fragiles)
- **2b.7:** Validacion y reporte

Despues vienen Sprint 3 (simulacion de escenarios) y Sprint 4 (dashboard/presentacion).
