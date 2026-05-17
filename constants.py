# constants.py
# Foundation for the UAV Configuration Optimizer

import numpy as np

# --- 1. UAV BASE PLATFORM CONSTANTS (WINGS-5KG MODEL) ---
MTOW = 5.0              # Max Takeoff Weight limit for the airframe
W_BASE = 2.5            # Weight of frame, motors, ESCs, flight controller, etc.
TWR_REFERENCE = 2.0     # Reference TWR for K_HOVER baseline calculation
K_HOVER = 110           # Hover Power Constant (W/kg)
P_AVIONICS = 15         # Avionics Power Draw (W)
DOD_MAX = 0.8           # Max Depth of Discharge (80% usable capacity)
BASE_UAV_COST = 3000  # Base cost of UAV without payload/battery
BATTERY_POSITION = (0, 0, 0)  # Battery is typically near CG
MAX_CG_OFFSET = 0.05  # Maximum allowed CG offset (5cm)
MIN_STABILITY = 30  # Minimum stability percentage
MIN_FLIGHT_TIME = 5  # Minimum flight time in minutes
# --- 2. STANDARD PAYLOAD MODULES (Enhanced with 3D positions) ---
PAYLOADS = {
    "FPV Camera (Standard)": {
        "weight_kg": 0.05,
        "power_w": 3,
        "utility_score": 1,
        "cost": 200,
        "color": "#FF0000",
        "position": (0.15, 0, 0.05),
        "size": (0.05, 0.03, 0.03)
    },
    "HD Gimbal (Standard)": {
        "weight_kg": 0.35,
        "power_w": 8,
        "utility_score": 3,
        "cost": 800,
        "color": "#00FF00",
        "position": (0.0, 0, -0.05),
        "size": (0.12, 0.08, 0.06)
    },
    "Delivery Box (Standard)": {
        "weight_kg": 1.5,
        "power_w": 12,
        "utility_score": 5,
        "cost": 1500,
        "color": "#0000FF",
        "position": (0.0, 0, -0.15),
        "size": (0.2, 0.15, 0.15)
    },
}

# --- 3. AERODYNAMIC & ENVIRONMENTAL CONSTANTS ---
AIR_DENSITY_SEA_LEVEL = 1.225  # kg/m³
DRAG_COEFF_BASE = 0.035
INDUCED_DRAG_FACTOR = 0.1

# --- 4. BATTERY PHYSICS ---
BATTERY_VOLTAGES = {
    "4S (14.8V)": 14.8,
    "6S (22.2V)": 22.2,
}

# Energy densities for different battery chemistries (Wh/kg)
BATTERY_ENERGY_DENSITIES = {
    "Standard LiPo": 150,
    "High-Capacity LiPo": 180,
    "Li-Ion": 200,
    "Experimental": 250
}

CAPACITY_SAMPLES_MAH = [5000, 7000, 9000, 10000, 12000]

# --- 5. MISSION PROFILES with Visualization Colors ---
MISSION_COEFFS = {
    "Surveillance (Max Endurance)": {
        "alpha": 0.5,
        "beta": 0.3,
        "gamma": 0.2,
        "color": "#1E88E5"
    },
    "Mapping (Max Utility)": {
        "alpha": 0.3,
        "beta": 0.6,
        "gamma": 0.1,
        "color": "#43A047"
    },
    "Delivery (Balanced)": {
        "alpha": 0.4,
        "beta": 0.4,
        "gamma": 0.2,
        "color": "#FB8C00"
    },
}

# --- 6. UAV 3D MODEL PARAMETERS ---
UAV_DIMENSIONS = {
    "arm_length": 0.25,
    "body_length": 0.4,
    "body_width": 0.1,
    "body_height": 0.08,
    "propeller_radius": 0.1
}

# --- 7. TEMPERATURE EFFECTS (Capacity multiplier) ---
TEMPERATURE_EFFECTS = {
    -10: 0.7,   # 30% capacity loss
    0: 0.8,     # 20% capacity loss
    10: 0.9,    # 10% capacity loss
    20: 1.0,    # Normal
    30: 0.95,   # 5% capacity loss
    40: 0.85    # 15% capacity loss
}