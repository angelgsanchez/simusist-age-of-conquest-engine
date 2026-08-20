# 🏛️ Simulator of Age of Conquest IV

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://www.riverbankcomputing.com/)
[![Academic Context](https://img.shields.io/badge/UNET-Simulación%20de%20Sistemas-blue)](http://www.unet.edu.ve)

Un motor de simulación funcional de **Age of Conquest IV** desarrollado en Python como proyecto final para la asignatura _Simulación de Sistemas_ de la **Universidad Nacional Experimental del Táchira (UNET)**.

Este proyecto modela computacionalmente un sistema de estrategia discreto, no lineal y realimentado, integrando simulación de eventos discretos (SED) mediante una Lista de Eventos Futuros (LEF) y dinámicas de sistemas para subsistemas económicos, demográficos y militares.

---

## 📌 Tabla de Contenidos

1. [Características Principales](#-características-principales)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Modelos Matemáticos y Mecánicas](#-modelos-matemáticos-y-mecánicas)
4. [Instalación y Requisitos](#-instalación-y-requisitos)
5. [Modos de Uso](#-modos-de-uso)
6. [Métricas de Rendimiento](#-métricas-de-rendimiento)
7. [Integrantes del Proyecto](#-integrantes-del-proyecto)

---

## 🚀 Características Principales

- **Gestión Temporal Discreta (LEF):** Control de sucesos mediante una Lista de Eventos Futuros para eventos síncronos, estocásticos y dinámicos.
- **Doble Interfaz de Usuario:**
  - **Modo Consola (CLI):** Ejecución ligera basada en texto para pruebas rápidas y métricas.
  - **Modo Gráfico (GUI):** Interfaz visual desarrollada en PyQt5 con mapa interactivo, log de eventos y tutorial integrado.
- **Subsistema de Inteligencia Artificial:** Árboles de decisión dinámicos para imperios enemigos prioritarios en estabilidad interna, solvencia económica y expansión militar.
- **Combate Estocástico:** Modelo de Lanchester estocástico con factores de variabilidad, bonificación de unidades especiales (Rey) y mecánicas de vasallaje/protectorado.

---

## 🏗️ Arquitectura del Sistema

El simulador está diseñado bajo una arquitectura modular orientada a objetos en Python:

- `EventoSIM`: Estructura fundamental para agendar y ordenar temporalmente eventos en la LEF.
- `Provincia`: Entidad territorial que contiene variables de población, tropas, nivel de felicidad y estatus de huelga.
- `Imperio`: Entidad gestora de tesorería, impuestos, estatus de soberanía y capacidades de acción.
- `MotorSimulacion`: Núcleo (`Core`) encargado del procesamiento de fin de turno, resolución de combates, toma de decisiones de la IA y métricas.

---

## 🧮 Modelos Matemáticos y Mecánicas

### 1. Economía y Tesorería

$$E(t+1) = E(t) + \sum R_i(t) - G(M_t) - F(t) - T(t)$$
_Los ingresos fiscales sólo se recaudan si el nivel de felicidad de la provincia es superior o igual al 50%._

### 2. Bienestar Social (Felicidad)

$$H_i(t+1) = \text{Sat}(H_i(t) - \beta \cdot I_i(t) + \gamma \cdot \text{Fiesta}_i(t) - \delta \cdot \text{Derrota}_i(t))$$
_Donde $\text{Sat}(x)$ satura el rango en $[0, 100]$._

### 3. Modelo Militante (Lanchester Estocástico)

$$A_{k+1} = \max(0, A_k - D_k \cdot \text{Eficacia}_D \cdot X_D)$$
$$D_{k+1} = \max(0, D_k - A_k \cdot \text{Eficacia}_A \cdot \mu_{\text{rey}} \cdot X_A)$$
_Donde $X \sim U(0.7, 1.3)$ representa el factor estocástico de batalla._

---

## 📦 Instalación y Requisitos

### Requisitos previos

- Python 3.10 o superior instalado.
- Entorno de ejecución en Windows, Linux o macOS.

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/angelgsanchez/simusist-age-of-conquest-engine.git]
   cd simusist-age-of-conquest-engine
   ```
