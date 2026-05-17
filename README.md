# UAV Digital Twin Optimizer

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.20%2B-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A physics-based digital twin and multi-objective optimization dashboard for Unmanned Aerial Vehicles (UAVs). This tool simulates, optimizes, and visualizes UAV payload, battery, and stability limits under various environmental conditions, enabling engineers to find the optimal hardware configuration before physical prototyping.

---

## Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Mathematical Models](#-mathematical-models)
4. [System Architecture](#-system-architecture)
5. [Installation & Setup](#-installation--setup)
6. [Usage Guide](#-usage-guide)
7. [Advanced Analytics](#-advanced-analytics)
8. [License](#-license)

---

## Overview

Designing the optimal UAV configuration requires balancing competing engineering objectives: maximizing flight time, maximizing payload utility, and minimizing weight and cost. 

This repository provides a "Digital Twin" of a baseline 5kg MTOW (Maximum Takeoff Weight) UAV. It utilizes a grid-search algorithm paired with a simplified NSGA-II inspired Pareto frontier selector to evaluate hundreds of payload and battery combinations, surfacing non-dominated solutions tailored to specific mission profiles (e.g., Surveillance, Mapping, or Delivery).

---

## Key Features

* **Physics-Based Simulation:** Calculates flight endurance using aerodynamic drag models, baseline thrust-to-weight ratios (TWR), and environmental capacity degradation.
* **3D CG & Stability Tracking:** Computes the 3D spatial Center of Gravity (CG) of the frame, payload, and battery, enforcing geometric stability limits.
* **Pareto Frontier Optimization:** Evaluates non-dominated solutions to find the perfect trade-off between weight, cost, and utility.
* **Interactive 3D Visualization:** Renders interactive Plotly 3D models of the UAV, visualizing payload placement and the CG stability sphere.
* **Cost-Benefit Analysis:** Computes daily operating costs, battery cycle degradation, and estimated payback periods for commercial drone operations.

---

## Mathematical Models

The digital twin leverages several physical approximations to simulate real-world UAV behavior (refer to `model.py` for implementation):

### 1. Power Draw Estimation
Total power required is calculated as a function of total weight, thrust-to-weight ratio efficiency, and auxiliary draw:

$$P_{total} = \left( K_{hover} \cdot \frac{TWR_{ref}}{TWR_{actual}} \cdot W_{total} \cdot 1.15 \right) + P_{avionics} + P_{payload}$$

### 2. Flight Endurance (with Temperature Degradation)
Battery capacity is adjusted based on depth of discharge ($DOD_{max}$) and environmental temperature coefficients ($\eta_{temp}$):

$$T_{flight} = \frac{E_{battery} \cdot DOD_{max} \cdot \eta_{temp}}{P_{total}} \cdot 60$$

### 3. Center of Gravity (CG)
The 3D spatial CG is calculated using the mass ($m_i$) and positional vectors ($\vec{r}_i$) of all selected components:

$$\vec{CG} = \frac{\sum m_i \vec{r}_i}{\sum m_i}$$

### 4. Multi-Objective Fitness Score
Configurations are ranked using mission-specific heuristic weights ($\alpha, \beta, \gamma$):

$$Score = \alpha \left(\frac{T_{flight}}{60}\right) + \beta (U_{payload}) - \gamma \left(\frac{W_{total}}{MTOW}\right)$$

---

## System Architecture

The codebase is modular and designed for easy extension:

* **`app.py`**: The main Streamlit application, handling UI routing, state management, and 3D Plotly rendering.
* **`model.py`**: The core physics engine (`DigitalTwinPhysics`) and the multi-objective optimization algorithms.
* **`constants.py`**: The single source of truth for baseline UAV specifications, battery chemistries, spatial coordinates, and aerodynamic constants.
* **`advanced_features.py`**: Modular extensions for mission planning, financial ROI analysis, parameter sensitivity mapping, and radar chart comparisons.

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR-USERNAME/uav-digital-twin-optimizer.git](https://github.com/YOUR-USERNAME/uav-digital-twin-optimizer.git)
   cd uav-digital-twin-optimizer
