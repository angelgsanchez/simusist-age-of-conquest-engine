# Age of Conquest IV - Simulador de Estrategia por Turnos

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

**Simulador funcional del videojuego _Age of Conquest IV_ desarrollado como proyecto final para la asignatura de Simulación de Sistemas en la Universidad Nacional Experimental del Táchira (UNET).**

---

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Características Principales](#características-principales)
- [Alcance del Proyecto](#alcance-del-proyecto)
- [Arquitectura del Software](#arquitectura-del-software)
- [Guía de Instalación y Uso](#guía-de-instalación-y-uso)
- [Validación y Métricas](#validación-y-métricas)
- [Casos de Uso y Pruebas](#casos-de-uso-y-pruebas)
- [Contribuciones y Equipo](#contribuciones-y-equipo)
- [Licencia](#licencia)
- [Referencias](#referencias)

---

## Descripción General

Este proyecto materializa las ecuaciones y diagramas lógicos de _Age of Conquest IV_ en un modelo operacional computarizado. El simulador replica con alta fidelidad las mecánicas internas del juego original, incluyendo:

- **Economía**: Tesorería, impuestos y mantenimiento militar.
- **Demografía**: Crecimiento poblacional basado en felicidad.
- **Combate**: Modelo de Lanchester estocástico con factor de azar.
- **Inteligencia Artificial**: Árbol de decisión para imperios enemigos.
- **Eventos**: Gestión de tiempo discreto mediante una Lista de Eventos Futuros (LEF).

Además, incorpora métricas de rendimiento (ISE, TMH, TEC) para evaluar el comportamiento del sistema y la efectividad de las estrategias del jugador.

---

## Características Principales

### Interfaz de Usuario

- **Modo Consola**: Interacción por comandos de texto, ideal para depuración y ejecución rápida.
- **Modo Gráfico (GUI)**: Interfaz visual con mapa circular, paneles de información y log de eventos. Incluye un tutorial interactivo al inicio.

### Subsistemas Implementados

- **Subsistema Económico**: Gestión de oro, impuestos, mantenimiento y tributos por protectorado.
- **Subsistema Demográfico**: Evolución de la población según el nivel de felicidad.
- **Subsistema de Felicidad**: Indicador de bienestar social con penalizaciones y bonificaciones.
- **Subsistema Militar**: Batallas estocásticas con modelo de Lanchester y posibilidad de muerte del rey.
- **Subsistema de IA**: Decisiones automáticas de imperios enemigos basadas en prioridades.
- **Subsistema de Eventos**: Gestión de eventos síncronos y asíncronos mediante LEF.

### Métricas de Rendimiento

- **ISE (Índice de Sostenibilidad Económica)**: Proporción de turnos con flujo de caja positivo.
- **TMH (Tiempo Medio en Huelga)**: Promedio de turnos que las provincias pasan en huelga fiscal.
- **TEC (Tasa de Eficiencia de Conquista)**: Provincias conquistadas por cada 100 bajas sufridas.

---

## Alcance del Proyecto

### Incluye

- Simulación de 4 imperios (1 jugador humano + 3 IA).
- Gestión de provincias con población, tropas y felicidad.
- Batallas con modelo de Lanchester estocástico.
- Inteligencia Artificial con árbol de decisión.
- Interfaz gráfica y consola.
- Métricas de rendimiento.
- Eventos aleatorios (peste, cosecha, tesoro, terremoto).

### Limitaciones

- No incluye diplomacia entre imperios.
- No hay sistema de tecnología o investigación.
- Mapa abstracto sin distancias ni rutas.
- No soporta multijugador humano.
- No hay persistencia de datos (guardado/carga de partidas).

---

## Arquitectura del Software

El simulador está implementado en **Python** y sigue un diseño orientado a objetos. La estructura principal del código es:

### Estructura de Clases

**EventoSIM**

- Representa un evento en la Lista de Eventos Futuros (LEF).
- Atributos: turno_ejecucion, tipo, datos.
- Método: **lt** para ordenamiento cronológico.

**Provincia**

- Unidad territorial del juego.
- Atributos: nombre, propietario, poblacion, tropas, felicidad, es_capital, activa, turnos_huelga.

**Imperio**

- Representa una facción o nación.
- Atributos: nombre, oro, tasa_impuestos, es_protectorado, rey_vivo, puntos_movimiento, es_ia.
- Métricas: turnos_flujo_positivo, turnos_totales, bajas_infligidas, bajas_recibidas, provincias_anexadas.
- Métodos: reset_puntos(), tiene_puntos(), gastar_punto().

**MotorSimulacion**

- Núcleo del simulador con toda la lógica de negocio.
- Atributos: turno_actual, imperios, mapa, lef, parametros, imperio_jugador.
- Métodos principales:
  - procesar_fin_de_turno(): Actualiza economía, demografía, felicidad y ejecuta IA.
  - atacar_provincia(): Implementa el modelo de combate Lanchester estocástico.
  - tomar_decision_ia(): Árbol de decisión para imperios enemigos.
  - calcular_ise(), calcular_tmh(), calcular_tec(): Métricas de rendimiento.

### Dependencias

- Python 3.12 o superior.
- PyQt5 (solo para modo gráfico).

---

## Guía de Instalación y Uso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/aoc4-simulator.git
cd aoc4-simulator
```

### 2. Instalar Dependencias

```bash
pip install PyQt5
```

### 3. Ejecutar el Simulador

**Modo gráfico (recomendado)**

```bash
python main.py -g
```

**Modo consola**

```bash
python main.py -c
```

**Selección interactiva**

```bash
python main.py
```

**Comandos en Modo Consola**

- r <provincia> <cantidad> - Reclutar tropas
- a <origen> <destino> <tropas> [rey=s/n] - Atacar
- f <provincia> - Organizar fiesta
- i <imperio> <tasa> - Cambiar impuestos
- t - Avanzar un turno
- 5 - Avanzar 5 turnos
- s - Ver estado del juego
- m - Ver métricas
- ia - Ejecutar IA enemiga
- q - Salir

**Ejemplos de Uso:**

- `r Roma 50` - Recluta 50 soldados en Roma
- `a Roma Galia 100 s` - Ataca Galia con 100 soldados y el Rey
- `f Cartago` - Organiza fiesta en Cartago
- `i "Imperio Romano" 1.5` - Cambia impuestos a 1.5

**Interfaz Gráfica:**

- Panel Izquierdo: Mapa circular con provincias coloreadas
- Panel Superior Derecho: Información del imperio (oro, impuestos, estado, rey, provincias, puntos, métricas)
- Panel Inferior Derecho: Botones de acción y log de eventos
- Tutorial interactivo al iniciar

**Requisitos del Sistema:**

- Windows, Linux o macOS
- Python 3.12+
- 512 MB RAM mínimo
- 100 MB espacio en disco

**Solución de Problemas:**

- Error PyQt5: `pip install PyQt5`
- Permisos: `sudo pip install PyQt5` (Linux/macOS)
- Verificar instalación: `pip list | grep PyQt5`

---

## Validación y Métricas

**Ecuaciones Validadas:**

- Tesorería: `imp.oro = imp.oro + ingresos - mantenimiento` (100% exactitud)
- Felicidad: `Sat(H - δ·I + γ·Fiesta - δ·Derrota)` (100% exactitud)
- Combate Lanchester: `A = max(0, A - D·ed·U(0.7,1.3))` (1000 batallas)
- Población: `P·1.01` o `P·0.99` según felicidad (100% exactitud)

**Métricas de Rendimiento (50 turnos):**

- Romano (Jugador): ISE 0.84, TMH 4.0, TEC 2.0 - Excelente
- Galas (IA): ISE 0.70, TMH 7.5, TEC 1.25 - Moderado
- Egipcios (IA): ISE 0.76, TMH 6.0, TEC 1.0 - Bueno
- Griegos (IA): ISE 0.66, TMH 9.0, TEC 0.0 - Regular

**Interpretación:**

- ISE > 0.8: Saludable, 0.6-0.8: Moderado, < 0.6: Deficiente
- TMH < 5: Estable, 5-10: Moderado, > 10: Crítico
- TEC > 1.0: Eficiente, = 1.0: Equilibrado, < 1.0: Ineficiente

---

## Casos de Uso y Pruebas

**Impuestos al Máximo (Tasa 2.0):**

- Turno 0: Felicidad 80%, Ingresos 50, Oro 500
- Turno 1: Felicidad 64%, Ingresos 40, Oro 530
- Turno 2: Felicidad 48%, Ingresos 0, Oro 530 (Huelga)
- Turno 5: Felicidad 0%, Ingresos 0, Oro 530 (Colapso)
- Recuperación: Reducir impuestos, fiestas, eventos favorables

**Felicidad en Cero:**

- Población decrece 1% por turno
- Sin ingresos ni reclutamiento
- Recuperación: Fiestas (+10), impuestos 0 (+10), protectorado (+3%)

**Bancarrota (Oro Negativo):**

- Acciones limitadas cuando oro es insuficiente
- Mantenimiento continúa
- Recuperación: Aumentar impuestos, eventos favorables

**Muerte del Rey:**

- Imperio se vuelve protectorado
- Paga 10% de ingresos como tributo
- Penalización de -20 felicidad
- Bonificación de +3% por protectorado

**Provincia Deshabitada:**

- Población 0 = provincia desactivada
- Sin ingresos, tropas o combates
- Desaparece del mapa

---

## Contribuciones y Equipo

**Integrantes:**

- Bryant Vivas Durán - Líder, Arquitectura
- Ángel Sánchez Contreras - Modelado, IA
- Leynner Angulo Sarmiento - GUI, Validación

**Profesor:** Feijoo Colomine
**Universidad:** UNET
**Fecha:** Agosto 2026

---

## Parámetros del Modelo

- α (Coeficiente tributario): 0.05 oro/hab
- M_div (Divisor logístico): 20.0 soldados/oro
- δ (Penalización fiscal): 8.0 %/factor
- γ (Amortiguación social): 10.0 %
- ΔH_rey (Penalización anarquía): 20.0 %
- P_muerte (Probabilidad muerte rey): 0.25
- H_huelga (Umbral de huelga): 50.0 %
- Tributo (Tasa de vasallaje): 0.10
- Crecimiento: 1.01
- Decrecimiento: 0.99
- P_evento: 0.05

---
