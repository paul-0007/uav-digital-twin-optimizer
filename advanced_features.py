# advanced_features.py - OPTIONAL ENHANCEMENTS
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from constants import TEMPERATURE_EFFECTS, MTOW

def create_mission_planning_tab():
    """Add mission planning with waypoints and coverage analysis."""
    
    st.subheader("Mission Planning")
    
    # Mission type selection
    mission_type = st.selectbox(
        "Mission Type",
        ["Area Mapping", "Linear Inspection", "Search Pattern", "Delivery Route"],
        key="mission_type"
    )
    
    if mission_type == "Area Mapping":
        col1, col2 = st.columns(2)
        with col1:
            area_km2 = st.number_input("Area to Map (km²)", 0.1, 50.0, 2.0, 0.1)
            altitude = st.slider("Flight Altitude (m)", 50, 500, 100)
        with col2:
            overlap = st.slider("Image Overlap (%)", 60, 90, 75)
            gsd = st.number_input("Ground Sampling Distance (cm/pixel)", 1.0, 20.0, 5.0, 0.1)
        
        # Coverage calculation
        coverage_rate = 0.15  # km² per minute at 100m altitude
        altitude_factor = 100 / altitude
        required_time = area_km2 / (coverage_rate * altitude_factor)
        
        st.info(f"""
        **Mission Analysis:**
        - Required Flight Time: **{required_time:.1f} minutes**
        - Coverage Rate: **{coverage_rate * altitude_factor:.2f} km²/min**
        - Images Required: **{int(area_km2 * 100 / (gsd * 0.01)):,}**
        """)
    
    elif mission_type == "Linear Inspection":
        length_km = st.number_input("Inspection Length (km)", 0.1, 100.0, 5.0, 0.1)
        inspection_speed = st.slider("Inspection Speed (m/s)", 2, 10, 5)
        
        required_time = (length_km * 1000 / inspection_speed) / 60  # Convert to minutes
        
        st.info(f"""
        **Inspection Analysis:**
        - Required Time: **{required_time:.1f} minutes**
        - Speed: **{inspection_speed} m/s**
        - Total Distance: **{length_km:.1f} km**
        """)
    
    return mission_type

def create_cost_analysis_tab(config):
    """Add detailed cost-benefit analysis."""
    
    if not config:
        st.info("Run optimization first to see cost analysis")
        return
    
    st.subheader("Cost-Benefit Analysis")
    
    # Input parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Operational Costs")
        missions_per_day = st.slider("Missions per Day", 1, 10, 3, key="missions_per_day")
        operator_cost = st.number_input("Operator Cost ($/hr)", 30, 200, 75, key="operator_cost")
        maintenance_rate = st.slider("Maintenance Rate (% of cost/year)", 5, 30, 15, key="maintenance_rate")
    
    with col2:
        st.markdown("#### Revenue Model")
        daily_revenue = st.number_input("Daily Revenue ($)", 200, 5000, 800, 50, key="daily_revenue")
        operating_days = st.slider("Operating Days/Year", 100, 365, 250, key="operating_days")
        discount_rate = st.slider("Discount Rate (%)", 1, 15, 8, key="discount_rate") / 100
    
    with col3:
        st.markdown("#### Battery Life")
        battery_cycles = st.slider("Battery Cycles", 100, 1000, 300, key="battery_cycles")
        battery_cost = config.get('battery', {}).get('cost', 150)
        
        cost_per_cycle = battery_cost / battery_cycles
        st.metric("Battery Cost/Cycle", f"${cost_per_cycle:.2f}")
    
    # Calculations
    uav_cost = config.get('total_cost', 5000)
    flight_time_hours = config.get('flight_time', 30) / 60
    
    # Daily costs
    daily_flight_hours = flight_time_hours * missions_per_day
    daily_operator_cost = operator_cost * daily_flight_hours
    daily_battery_cost = (battery_cost / battery_cycles) * missions_per_day
    
    # Annual costs
    annual_operating_cost = (daily_operator_cost + daily_battery_cost) * operating_days
    annual_maintenance = uav_cost * (maintenance_rate / 100)
    
    # Revenue
    annual_revenue = daily_revenue * operating_days
    
    # ROI Calculation
    total_annual_cost = annual_operating_cost + annual_maintenance
    annual_profit = annual_revenue - total_annual_cost
    
    if annual_profit > 0:
        payback_months = (uav_cost / annual_profit) * 12
        roi = (annual_profit / uav_cost) * 100
        
        st.success(f"""
        **Financial Analysis:**
        - Payback Period: **{payback_months:.1f} months**
        - ROI: **{roi:.1f}% per year**
        - Annual Profit: **${annual_profit:,.0f}**
        """)
    else:
        st.warning(f"""
        **Financial Analysis:**
        - Annual Loss: **${abs(annual_profit):,.0f}**
        - Daily Revenue Needed: **${(total_annual_cost/operating_days)+1:,.0f}**
        """)
    
    # Cost breakdown chart
    cost_data = {
        'Component': ['UAV Purchase', 'Annual Maintenance', 'Operator Costs', 'Battery Costs'],
        'Cost ($)': [uav_cost, annual_maintenance, annual_operating_cost*0.7, annual_operating_cost*0.3]
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=cost_data['Component'],
            y=cost_data['Cost ($)'],
            marker_color=['#1E88E5', '#43A047', '#FB8C00', '#FF5252']
        )
    ])
    
    fig.update_layout(
        title="Cost Breakdown (First Year)",
        yaxis_title="Cost ($)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_sensitivity_analysis_tab(config):
    """Create sensitivity analysis for key parameters."""
    
    st.subheader("Sensitivity Analysis")
    
    if not config:
        st.info("Run optimization first to see sensitivity analysis")
        return
    
    # Parameter ranges
    st.markdown("#### Impact of Key Parameters on Flight Time")
    
    # Create sensitivity analysis for different parameters
    parameters = {
        "Battery Capacity": np.linspace(0.5, 1.5, 5),  # 50% to 150%
        "Temperature": [-10, 0, 10, 20, 30, 40],
        "Payload Weight": np.linspace(0.5, 1.5, 5),
        "TWR (Efficiency)": np.linspace(0.8, 1.2, 5)
    }
    
    base_flight_time = config.get('flight_time', 30)
    
    # Create sensitivity plot
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for idx, (param_name, param_values) in enumerate(parameters.items()):
        flight_times = []
        
        for val in param_values:
            if param_name == "Temperature":
                # Temperature effect from constants
                temps = list(TEMPERATURE_EFFECTS.keys())
                factors = list(TEMPERATURE_EFFECTS.values())
                factor = np.interp(val, temps, factors)
                flight_times.append(base_flight_time * factor)
            else:
                # Linear approximation for other parameters
                flight_times.append(base_flight_time * val)
        
        fig.add_trace(go.Scatter(
            x=param_values,
            y=flight_times,
            mode='lines+markers',
            name=param_name,
            line=dict(color=colors[idx % len(colors)], width=3)
        ))
    
    fig.update_layout(
        title="Parameter Sensitivity Analysis",
        xaxis_title="Parameter Value (Normalized)",
        yaxis_title="Flight Time (min)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations based on sensitivity
    st.markdown("#### Recommendations")
    
    reco_col1, reco_col2 = st.columns(2)
    
    with reco_col1:
        st.info("**Most Impactful Improvements:**")
        st.write("1. **Increase battery capacity** - Linear improvement")
        st.write("2. **Optimize flight temperature** - 20°C is optimal")
        st.write("3. **Reduce payload weight** - Quadratic power savings")
    
    with reco_col2:
        st.info("**Cost-Effective Optimizations:**")
        st.write("1. **Maintain TWR > 2.0** - Best efficiency")
        st.write("2. **Use high-density batteries** - More Wh/kg")
        st.write("3. **Schedule flights in mild weather** - Avoid extremes")

def create_comparison_tool(configs_list):
    """Create tool to compare multiple configurations."""
    
    st.subheader("Configuration Comparison Tool")
    
    if len(configs_list) < 2:
        st.info("Run at least 2 optimizations to compare")
        return
    
    # Create comparison table
    comparison_data = []
    for i, config in enumerate(configs_list):
        comparison_data.append({
            "Config": f"#{i+1}",
            "Payload": config.get('payload', 'Unknown'),
            "Flight Time (min)": f"{config.get('flight_time', 0):.1f}",
            "Total Weight (kg)": f"{config.get('total_weight', 0):.2f}",
            "Cost ($)": f"{config.get('total_cost', 0):,.0f}",
            "Score": f"{config.get('score', 0):.2f}"
        })
    
    # Display as table
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    st.table(df)
    
    # Create radar chart for comparison
    st.subheader("Radar Chart Comparison")
    
    categories = ['Flight Time', 'Payload Utility', 'Weight Efficiency', 'Cost Efficiency', 'Stability']
    
    fig = go.Figure()
    
    for i, config in enumerate(configs_list):
        values = [
            config.get('flight_time', 0) / 60,  # Normalize to 0-1
            config.get('payload_score', 0) / 10,
            1 - (config.get('total_weight', 0) / MTOW),
            1 - min(1, config.get('total_cost', 0) / 10000),
            config.get('stability', 100) / 100
        ]
        
        # Close the radar chart
        values = values + [values[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            name=f"Config #{i+1}",
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)