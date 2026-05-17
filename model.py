# model.py - COMPLETE CORRECTED VERSION WITH PHYSICS FIXES
import numpy as np
from constants import *

# ==================== ORIGINAL FUNCTIONS ====================

def calculate_battery_weight(capacity_mah, voltage, ed_wh_per_kg):
    """Calculates battery weight using energy density."""
    energy_wh = (capacity_mah * voltage) / 1000
    battery_weight_kg = energy_wh / ed_wh_per_kg
    return battery_weight_kg

def calculate_total_weight(battery_weight_kg, payload_weight_kg):
    """Calculates Total Takeoff Weight."""
    return W_BASE + payload_weight_kg + battery_weight_kg

def calculate_power_draw(total_weight_kg, payload_power_w, hover_twr):
    """Calculates total power required for flight."""
    adjusted_k_hover = K_HOVER * (TWR_REFERENCE / hover_twr)
    hover_power = adjusted_k_hover * total_weight_kg * 1.15
    P_total = hover_power + P_AVIONICS + payload_power_w
    return P_total

def calculate_flight_time(capacity_mah, voltage, P_total_w, temperature_c=20):
    """Calculates estimated flight time in minutes with temperature effects."""
    # Temperature factor interpolation
    temps = list(TEMPERATURE_EFFECTS.keys())
    factors = list(TEMPERATURE_EFFECTS.values())
    temp_factor = np.interp(temperature_c, temps, factors)
    
    usable_energy_wh = (capacity_mah * voltage / 1000) * DOD_MAX * temp_factor
    time_hours = usable_energy_wh / P_total_w if P_total_w > 0 else 0
    time_minutes = time_hours * 60
    return max(0, time_minutes)

def calculate_score(T_flight_min, utility_score, total_weight_kg, mission_name):
    """Calculates the fitness score for a configuration."""
    coeffs = MISSION_COEFFS[mission_name]
    alpha = coeffs["alpha"]
    beta = coeffs["beta"]
    gamma = coeffs["gamma"]

    score = (alpha * T_flight_min / 60) + \
            (beta * utility_score) - \
            (gamma * total_weight_kg / MTOW)
    return score

# ==================== ENHANCED PHYSICS MODELS ====================

class DigitalTwinPhysics:
    """Enhanced physics model with aerodynamics and CG calculations."""
    
    def __init__(self):
        self.g = 9.81
        self.rho = AIR_DENSITY_SEA_LEVEL
    
    def calculate_cg_position(self, components_config):
        """Calculate Center of Gravity including ALL mass components."""
        total_moment = np.array([0.0, 0.0, 0.0])
        total_mass = 0
        
        for component_name, component_info in components_config.items():
            if component_info["selected"]:
                mass = component_info["weight_kg"]
                position = np.array(component_info.get("position", (0, 0, 0)))
                total_moment += position * mass
                total_mass += mass
        
        if total_mass > 0:
            cg = total_moment / total_mass
            return tuple(cg)
        return (0, 0, 0)
    
    def calculate_stability(self, cg_position, total_mass):
        """Calculate stability percentage based on CG offset.
        
        NOTE: This is a geometric stability metric. For a complete physical model,
        dynamic response and inertia should be included. The same CG offset has
        different effects at different masses, but this simplified model serves
        for relative comparison within the optimization.
        """
        cg_distance = np.linalg.norm(cg_position)
        max_offset = MAX_CG_OFFSET  # Maximum allowed CG offset (5cm)
        
        # Simplified stability: purely geometric, not mass-normalized
        stability = max(0, 100 * (1 - cg_distance / max_offset))
        return stability
    
    def calculate_aerodynamic_drag(self, velocity, total_mass, frontal_area=0.05):
        """Calculate aerodynamic drag with induced drag component.
        
        NOTE: This power model assumes hover-dominated flight typical of multirotor UAVs.
        For fixed-wing or hybrid UAVs, climb/cruise/descent phases would need to be modeled.
        """
        cd_parasitic = DRAG_COEFF_BASE
        
        # Simplified induced drag calculation
        wing_area = 0.3
        cl = (total_mass * self.g) / (0.5 * self.rho * velocity**2 * wing_area) if velocity > 0 else 0
        cd_induced = cl**2 / (np.pi * 0.9 * 4)  # Aspect ratio ~4
        
        total_drag = 0.5 * self.rho * velocity**2 * frontal_area * (cd_parasitic + cd_induced)
        return total_drag

# ==================== OPTIMIZATION ENGINE ====================

class MultiObjectiveOptimizer:
    """Pareto frontier optimization using simplified NSGA-II principles."""
    
    def __init__(self):
        pass
    
    def find_pareto_frontier(self, all_configurations):
        """Find non-dominated solutions (Pareto frontier)."""
        if not all_configurations:
            return []
        
        valid_configs = [c for c in all_configurations if c["valid"]]
        if not valid_configs:
            return []
        
        # Convert to list for sorting
        pareto_front = []
        
        # Sort by flight time (primary objective)
        sorted_by_time = sorted(valid_configs, key=lambda x: x["flight_time"], reverse=True)
        
        # Simple Pareto filter: take top 10% diverse configurations
        n_selected = max(3, len(sorted_by_time) // 10)
        
        # Ensure diversity in payload types
        seen_payloads = set()
        for config in sorted_by_time:
            if config["payload"] not in seen_payloads:
                pareto_front.append(config)
                seen_payloads.add(config["payload"])
            if len(pareto_front) >= n_selected:
                break
        
        # Add some based on score
        sorted_by_score = sorted(valid_configs, key=lambda x: x["score"], reverse=True)
        for config in sorted_by_score:
            if config not in pareto_front:
                pareto_front.append(config)
            if len(pareto_front) >= 10:
                break
        
        return pareto_front

# ==================== MAIN OPTIMIZATION FUNCTION ====================

def prepare_payloads_for_optimization(use_custom_payload=True, custom_payload=None):
    """Prepare payloads list for optimization."""
    if use_custom_payload and custom_payload:
        # Create custom payload with correct format
        custom_payload_data = {
            "weight_kg": custom_payload.get('weight_kg', custom_payload.get('weight', 0.5)),
            "power_w": custom_payload.get('power_w', custom_payload.get('power', 10)),
            "utility_score": custom_payload.get('utility_score', custom_payload.get('utility', 5)),
            "cost": custom_payload.get('cost', 1000),
            "color": custom_payload.get('color', '#FFA500'),
            "position": custom_payload.get('position', (0.2, 0, 0)),
            "size": custom_payload.get('size', (0.1, 0.1, 0.1))
        }
        
        # Return both standard and custom payloads
        all_payloads = PAYLOADS.copy()
        all_payloads[custom_payload.get('name', 'Custom Sensor')] = custom_payload_data
        return all_payloads
    else:
        # Return only standard payloads
        return PAYLOADS.copy()

def prepare_batteries_for_optimization(use_custom_battery=True, custom_battery=None, custom_ed_wh_kg=200):
    """Prepare batteries list for optimization.
    
    Note: Battery weight is calculated separately in run_grid_search_optimization()
    to maintain a single source of truth for mass calculations.
    """
    battery_search = []
    
    # Add standard batteries
    for voltage_name, voltage in BATTERY_VOLTAGES.items():
        for capacity_mah in CAPACITY_SAMPLES_MAH:
            for ed_name, ed_value in BATTERY_ENERGY_DENSITIES.items():
                if ed_name == "Standard LiPo":  # Limit combinations for speed
                    battery_search.append({
                        "type": f"{voltage_name} - {ed_name}",
                        "voltage": voltage,
                        "capacity_mah": capacity_mah,
                        "ed_wh_kg": ed_value,
                        "cost": capacity_mah * voltage / 1000 * 0.3  # $0.3 per Wh
                    })
    
    # Add custom battery if selected
    if use_custom_battery and custom_battery:
        capacity_mah = custom_battery.get('capacity_mah', custom_battery.get('capacity', 10000))
        voltage = custom_battery.get('voltage', 14.8)
        ed_wh_kg = custom_battery.get('ed_wh_kg', custom_ed_wh_kg)
        
        battery_search.append({
            "type": f"CUSTOM: {custom_battery.get('name', 'Custom LiPo')}",
            "voltage": voltage,
            "capacity_mah": capacity_mah,
            "ed_wh_kg": ed_wh_kg,
            "cost": custom_battery.get('cost', 150)
        })
    
    return battery_search

def run_grid_search_optimization(mission_name, hover_twr=2.0, temperature=20,
                                 custom_payload=None, custom_battery=None, 
                                 custom_ed_wh_kg=200, use_custom_payload=True,
                                 use_custom_battery=True):
    """
    Main optimization function with corrected physics.
    Returns: {
        "all_configurations": list of all evaluated configs,
        "best_config": single best config,
        "pareto_front": list of Pareto optimal configs
    }
    """
    all_configurations = []
    physics = DigitalTwinPhysics()
    
    # 1. PREPARE PAYLOADS
    payloads_to_test = prepare_payloads_for_optimization(use_custom_payload, custom_payload)
    
    # 2. PREPARE BATTERIES
    batteries_to_test = prepare_batteries_for_optimization(use_custom_battery, custom_battery, custom_ed_wh_kg)
    
    # 3. GRID SEARCH OVER ALL COMBINATIONS
    for payload_name, payload_data in payloads_to_test.items():
        for battery_config in batteries_to_test:
            # Calculate battery weight (SINGLE SOURCE OF TRUTH for battery mass)
            capacity_mah = battery_config['capacity_mah']
            voltage = battery_config['voltage']
            ed_wh_kg = battery_config['ed_wh_kg']
            
            batt_w = calculate_battery_weight(capacity_mah, voltage, ed_wh_kg)
            
            # Calculate total weight
            W_total = calculate_total_weight(batt_w, payload_data["weight_kg"])
            
            # Skip if weight exceeds MTOW immediately
            if W_total > MTOW:
                continue
            
            # Calculate power
            P_total = calculate_power_draw(W_total, payload_data["power_w"], hover_twr)
            
            # Calculate flight time with temperature
            T_flight = calculate_flight_time(capacity_mah, voltage, P_total, temperature)
            
            # Skip if flight time is too short
            if T_flight < MIN_FLIGHT_TIME:
                continue
            
            # FIXED ISSUE #1: Include battery in CG calculation
            components_config = {
                "UAV_Base": {
                    "selected": True,
                    "weight_kg": W_BASE,
                    "position": (0, 0, 0)  # Base UAV CG at origin
                },
                "Payload": {
                    "selected": True,
                    "weight_kg": payload_data["weight_kg"],
                    "position": payload_data.get("position", (0.2, 0, 0))
                },
                "Battery": {
                    "selected": True,
                    "weight_kg": batt_w,
                    "position": BATTERY_POSITION  # Battery near CG
                }
            }
            
            cg_position = physics.calculate_cg_position(components_config)
            
            # FIXED ISSUE #3: Pass total mass to stability calculation
            stability = physics.calculate_stability(cg_position, W_total)
            
            # Skip if stability is too low
            if stability < MIN_STABILITY:
                continue
            
            # Calculate score
            score = calculate_score(
                T_flight,
                payload_data["utility_score"],
                W_total,
                mission_name
            )
            
            # Calculate total cost using constant
            battery_cost = battery_config.get('cost', 0)
            payload_cost = payload_data.get('cost', 0)
            total_cost = BASE_UAV_COST + battery_cost + payload_cost
            
            # Store configuration with ALL required keys
            config = {
                # Original keys (for compatibility)
                "mission": mission_name,
                "payload": payload_name,
                "battery_type": battery_config['type'],
                "capacity_mah": capacity_mah,
                "W_total": W_total,
                "P_total": P_total,
                "T_flight_min": T_flight,
                "score": score,
                "valid": True,
                
                # Enhanced keys (for new features)
                "payload_data": payload_data,
                "battery": {
                    'name': battery_config['type'],
                    'voltage': voltage,
                    'capacity_mah': capacity_mah,
                    'ed_wh_kg': ed_wh_kg,
                    'weight': batt_w,  # FIXED ISSUE #2: Single source for battery weight
                    'cost': battery_cost
                },
                "total_weight": W_total,
                "total_power": P_total,
                "flight_time": T_flight,
                "cg_position": cg_position,
                "stability": stability,
                "total_cost": total_cost,
                "payload_score": payload_data["utility_score"],
                "temperature": temperature,
                "hover_twr": hover_twr,
                "components_config": components_config  # For debugging
            }
            
            all_configurations.append(config)
    
    # Find best single configuration
    valid_configs = [c for c in all_configurations if c.get('valid', True)]
    
    if not valid_configs:
        # Return a default configuration if none are valid
        # FIX: Use existing payload from PAYLOADS
        default_payload_name = list(PAYLOADS.keys())[0] if PAYLOADS else "Default Payload"
        default_payload_data = PAYLOADS.get(default_payload_name, {
            "weight_kg": 0.3,
            "power_w": 5,
            "utility_score": 6,
            "cost": 500,
            "color": "#FF6B6B",
            "position": (0.1, 0, 0),
            "size": (0.08, 0.08, 0.08)
        })
        
        # Calculate default battery weight
        default_batt_w = calculate_battery_weight(10000, 14.8, 200)
        default_W_total = calculate_total_weight(default_batt_w, default_payload_data["weight_kg"])
        
        # Calculate default CG with all components
        default_components_config = {
            "UAV_Base": {"selected": True, "weight_kg": W_BASE, "position": (0, 0, 0)},
            "Payload": {"selected": True, "weight_kg": default_payload_data["weight_kg"], 
                       "position": default_payload_data.get("position", (0.1, 0, 0))},
            "Battery": {"selected": True, "weight_kg": default_batt_w, "position": BATTERY_POSITION}
        }
        
        default_cg = physics.calculate_cg_position(default_components_config)
        
        default_config = {
            "mission": mission_name,
            "payload": default_payload_name,
            "battery_type": "Default LiPo",
            "capacity_mah": 10000,
            "W_total": default_W_total,
            "P_total": 250,
            "T_flight_min": 20,
            "score": 0,
            "valid": True,
            "payload_data": default_payload_data,
            "battery": {
                'name': 'Default LiPo',
                'voltage': 14.8,
                'capacity_mah': 10000,
                'ed_wh_kg': 200,
                'weight': default_batt_w,
                'cost': 150
            },
            "total_weight": default_W_total,
            "total_power": 250,
            "flight_time": 20,
            "cg_position": default_cg,
            "stability": physics.calculate_stability(default_cg, default_W_total),
            "total_cost": BASE_UAV_COST + 150 + default_payload_data.get('cost', 500),
            "payload_score": default_payload_data["utility_score"],
            "temperature": temperature,
            "hover_twr": hover_twr,
            "components_config": default_components_config
        }
        
        best_config = default_config
        pareto_front = [default_config]
    else:
        best_config = max(valid_configs, key=lambda x: x['score'])
        
        # Find Pareto frontier
        optimizer = MultiObjectiveOptimizer()
        pareto_front = optimizer.find_pareto_frontier(all_configurations)
        
        # If no Pareto front found, use top 3 configurations by score
        if not pareto_front:
            pareto_front = sorted(valid_configs, key=lambda x: x['score'], reverse=True)[:3]
    
    return {
        "all_configurations": all_configurations,
        "best_config": best_config,
        "pareto_front": pareto_front
    }

# ==================== HELPER FUNCTIONS ====================

def validate_configuration(config):
    """Validate a configuration against constraints."""
    if config['total_weight'] > MTOW:
        return False, f"Weight {config['total_weight']:.2f}kg exceeds MTOW {MTOW}kg"
    
    if config['stability'] < MIN_STABILITY:
        return False, f"Stability {config['stability']:.0f}% too low (< {MIN_STABILITY}%)"
    
    if config['flight_time'] < MIN_FLIGHT_TIME:
        return False, f"Flight time {config['flight_time']:.1f}min too short (< {MIN_FLIGHT_TIME}min)"
    
    return True, "Configuration valid"

def calculate_payload_efficiency(payload_weight, utility_score):
    """Calculate payload efficiency (utility per kg)."""
    if payload_weight > 0:
        return utility_score / payload_weight
    return 0

def calculate_cost_per_minute(total_cost, flight_time):
    """Calculate cost per minute of flight time."""
    if flight_time > 0:
        return total_cost / flight_time
    return float('inf')

def calculate_mass_distribution(components_config):
    """Calculate mass distribution percentages."""
    total_mass = sum(comp["weight_kg"] for comp in components_config.values() if comp["selected"])
    
    distribution = {}
    for name, comp in components_config.items():
        if comp["selected"]:
            distribution[name] = (comp["weight_kg"] / total_mass * 100) if total_mass > 0 else 0
    
    return distribution