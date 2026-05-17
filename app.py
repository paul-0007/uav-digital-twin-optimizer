# app.py - COMPLETE CORRECTED VERSION WITH FIXED CUSTOM INPUTS
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time

# Import local modules
from constants import *
from model import run_grid_search_optimization, DigitalTwinPhysics
from advanced_features import (
    create_mission_planning_tab, 
    create_cost_analysis_tab,
    create_sensitivity_analysis_tab,
    create_comparison_tool
)

# ==================== STREAMLIT CONFIG ====================
st.set_page_config(
    page_title="UAV Digital Twin Optimizer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #1E88E5, #43A047);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: Black;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #1E88E5;
        margin: 0.5rem 0;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        transition: all 0.3s;
        font-size: 1rem;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .tab-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3D VISUALIZATION FUNCTIONS ====================

def create_3d_uav_visualization(config):
    """Create 3D visualization of UAV with payloads and CG."""
    
    fig = go.Figure()
    
    if not config:
        # Show default UAV
        fig.add_trace(go.Scatter3d(
            x=[0, 0.25, 0, -0.25, 0],
            y=[0, 0, 0.25, 0, -0.25],
            z=[0, 0, 0, 0, 0],
            mode='lines+markers',
            line=dict(color='gray', width=4),
            marker=dict(size=8, color='gray'),
            name='UAV Frame'
        ))
        
        fig.update_layout(
            scene=dict(
                xaxis=dict(title='X (m)', range=[-0.3, 0.3]),
                yaxis=dict(title='Y (m)', range=[-0.3, 0.3]),
                zaxis=dict(title='Z (m)', range=[-0.2, 0.2])
            ),
            height=500,
            title="Default UAV Configuration"
        )
        
        return fig
    
    # Extract data from config
    payload_data = config.get('payload_data', {})
    cg_position = config.get('cg_position', (0, 0, 0))
    
    # UAV Frame (Simplified Quadcopter)
    arm_length = UAV_DIMENSIONS["arm_length"]
    
    # Arms
    arm_positions = [
        (arm_length, 0, 0),
        (-arm_length, 0, 0),
        (0, arm_length, 0),
        (0, -arm_length, 0)
    ]
    
    for x, y, z in arm_positions:
        fig.add_trace(go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, 0],
            mode='lines',
            line=dict(color='#666666', width=6),
            showlegend=False
        ))
        
        # Propellers
        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[0],
            mode='markers',
            marker=dict(
                size=12,
                color='#999999',
                symbol='circle',
                line=dict(width=2, color='black')
            ),
            showlegend=False
        ))
    
    # Center Body
    body_length = UAV_DIMENSIONS["body_length"]
    body_width = UAV_DIMENSIONS["body_width"]
    body_height = UAV_DIMENSIONS["body_height"]
    
    # Draw a simple box for the body
    fig.add_trace(go.Mesh3d(
        x=[-body_length/2, body_length/2, body_length/2, -body_length/2,
           -body_length/2, body_length/2, body_length/2, -body_length/2],
        y=[-body_width/2, -body_width/2, body_width/2, body_width/2,
           -body_width/2, -body_width/2, body_width/2, body_width/2],
        z=[0, 0, 0, 0, body_height, body_height, body_height, body_height],
        i=[7, 0, 0, 0, 4, 4, 6, 6],
        j=[3, 4, 1, 2, 5, 6, 5, 2],
        k=[0, 7, 2, 3, 6, 7, 1, 1],
        color='rgba(80, 80, 100, 0.7)',
        opacity=0.8,
        name='UAV Body'
    ))
    
    # Payload (if exists)
    if payload_data:
        pos = payload_data.get('position', (0.2, 0, 0))
        color = payload_data.get('color', '#FF0000')
        size = payload_data.get('size', (0.1, 0.1, 0.1))
        
        # Simple payload box
        fig.add_trace(go.Scatter3d(
            x=[pos[0]], y=[pos[1]], z=[pos[2]],
            mode='markers',
            marker=dict(
                size=payload_data.get('weight_kg', 0.1) * 20,
                color=color,
                symbol='square',
                line=dict(width=2, color='black')
            ),
            name=config.get('payload', 'Payload')
        ))
    
    # Center of Gravity
    fig.add_trace(go.Scatter3d(
        x=[cg_position[0]], y=[cg_position[1]], z=[cg_position[2]],
        mode='markers',
        marker=dict(
            size=15,
            color='yellow',
            symbol='diamond',
            line=dict(width=2, color='black')
        ),
        name='Center of Gravity'
    ))
    
    # Stability sphere
    max_offset = 0.05
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    x_sphere = max_offset * np.outer(np.cos(u), np.sin(v))
    y_sphere = max_offset * np.outer(np.sin(u), np.sin(v))
    z_sphere = max_offset * np.outer(np.ones(np.size(u)), np.cos(v))
    
    fig.add_trace(go.Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        opacity=0.1,
        colorscale=[[0, 'rgba(255,0,0,0.1)'], [1, 'rgba(255,0,0,0.1)']],
        showscale=False,
        name='Stability Limit'
    ))
    
    # Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X (m)', range=[-0.3, 0.3]),
            yaxis=dict(title='Y (m)', range=[-0.3, 0.3]),
            zaxis=dict(title='Z (m)', range=[-0.2, 0.2]),
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0.8),
                up=dict(x=0, y=0, z=1)
            )
        ),
        height=500,
        title=f"UAV Configuration - CG: ({cg_position[0]:.3f}, {cg_position[1]:.3f}, {cg_position[2]:.3f}) m",
        showlegend=True,
        legend=dict(x=0.8, y=0.9)
    )
    
    return fig

def create_performance_dashboard(config):
    """Create comprehensive performance dashboard."""
    
    if not config:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('', 'Weight Breakdown',
                       'Flight Time vs Temperature', 'Stability Analysis'),
        specs=[[{'type': 'domain'}, {'type': 'xy'}],
               [{'type': 'xy'}, {'type': 'xy'}]]
    )
    
    # 1. Power Distribution Pie Chart
    prop_power = config.get('P_total', 0) * 0.7
    payload_power = config.get('payload_data', {}).get('power_w', 0)
    
    fig.add_trace(go.Pie(
    labels=['Propulsion', 'Payload', 'Avionics'],
    values=[prop_power, payload_power, P_AVIONICS],
    hole=0.4,
    textinfo='label+percent',
    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1']),
    ), row=1, col=1)

    
    # 2. Weight Breakdown Bar Chart
    components = ['UAV Base', 'Payload', 'Battery']
    weights = [
        W_BASE,
        config.get('payload_data', {}).get('weight_kg', 0),
        config.get('battery', {}).get('weight', 0.5)
    ]
    
    fig.add_trace(go.Bar(
        x=components,
        y=weights,
        marker_color=['#1E88E5', '#43A047', '#FB8C00'],
        name="Weight"
    ), row=1, col=2)
    
    # 3. Flight Time vs Temperature
    temperatures = np.arange(-10, 41, 5)
    flight_times = []
    
    for temp in temperatures:
        # Simplified temperature effect
        factor = np.interp(temp, [-10, 0, 10, 20, 30, 40], [0.7, 0.8, 0.9, 1.0, 0.95, 0.85])
        flight_times.append(config.get('flight_time', 30) * factor)
    
    fig.add_trace(go.Scatter(
        x=temperatures,
        y=flight_times,
        mode='lines+markers',
        line=dict(color='#1E88E5', width=3),
        fill='tozeroy',
        fillcolor='rgba(30, 136, 229, 0.2)',
        name="Temperature Effect"
    ), row=2, col=1)
    
    # 4. Stability Visualization
    cg = config.get('cg_position', (0, 0, 0))
    stability = config.get('stability', 100)
    
    # Create stability circle
    theta = np.linspace(0, 2*np.pi, 100)
    max_radius = 0.05
    current_radius = max_radius * (1 - stability/100)
    
    fig.add_trace(go.Scatter(
        x=np.cos(theta) * max_radius,
        y=np.sin(theta) * max_radius,
        mode='lines',
        line=dict(color='red', dash='dash'),
        name='Stability Limit'
    ), row=2, col=2)
    
    fig.add_trace(go.Scatter(
        x=np.cos(theta) * current_radius,
        y=np.sin(theta) * current_radius,
        mode='lines',
        line=dict(color='green', width=2),
        fill='toself',
        fillcolor='rgba(76, 175, 80, 0.3)',
        name='Current Stability'
    ), row=2, col=2)
    
    fig.add_trace(go.Scatter(
        x=[cg[0]], y=[cg[1]],
        mode='markers',
        marker=dict(size=12, color='yellow', symbol='star'),
        name='Current CG'
    ), row=2, col=2)
    
    # Update layout
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text="Performance Dashboard"
    )
    
    fig.update_xaxes(title_text="Temperature (°C)", row=2, col=1)
    fig.update_yaxes(title_text="Flight Time (min)", row=2, col=1)
    fig.update_xaxes(title_text="X Position (m)", row=2, col=2)
    fig.update_yaxes(title_text="Y Position (m)", row=2, col=2)
    
    return fig

def create_pareto_visualization(pareto_front):
    """Create 3D Pareto frontier visualization."""
    
    if not pareto_front:
        return None
    
    df = pd.DataFrame(pareto_front)
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=df['flight_time'],
            y=df['payload_score'],
            z=df['total_cost'],
            mode='markers',
            marker=dict(
                size=10,
                color=df['flight_time'],
                colorscale='Viridis',
                opacity=0.8,
                colorbar=dict(title="Flight Time")
            ),
            text=[f"{row['payload']}<br>Score: {row['score']:.2f}" 
                  for _, row in df.iterrows()],
            hoverinfo='text'
        )
    ])
    
    fig.update_layout(
        scene=dict(
            xaxis_title='Flight Time (min) ↑',
            yaxis_title='Payload Score ↑',
            zaxis_title='Total Cost ($) ↓',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        height=600,
        title="Pareto Frontier: Trade-off Analysis"
    )
    
    return fig

# ==================== SIDEBAR CONFIGURATION ====================

def create_sidebar():
    """Create interactive sidebar configuration."""
    
    st.sidebar.title("Configuration")
    
    # Mission Selection
    st.sidebar.subheader("1. Mission Profile")
    mission_name = st.sidebar.selectbox(
        "Select Mission Type",
        list(MISSION_COEFFS.keys()),
        index=0
    )
    
    # Display mission coefficients
    coeffs = MISSION_COEFFS[mission_name]
    st.sidebar.markdown(f"""
    **Mission Priorities:**
    - Flight Time: {coeffs['alpha']*100:.0f}%
    - Payload Utility: {coeffs['beta']*100:.0f}%
    - Weight: {coeffs['gamma']*100:.0f}%
    """)
    
    # UAV Performance
    st.sidebar.subheader("2. UAV Performance")
    hover_twr = st.sidebar.slider(
        "Thrust-to-Weight Ratio (TWR)",
        min_value=1.5,
        max_value=3.0,
        value=2.0,
        step=0.1,
        help="Higher TWR = better efficiency"
    )
    
    # Environmental Conditions
    st.sidebar.subheader("3. Environmental Conditions")
    temperature = st.sidebar.slider(
        "Temperature (°C)",
        min_value=-10,
        max_value=40,
        value=20,
        step=5
    )
    
    # Custom Payload
    st.sidebar.subheader("4. Custom Payload")
    custom_payload_name = st.sidebar.text_input("Payload Name", "Custom Sensor")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        custom_weight = st.sidebar.number_input("Weight (kg)", 0.01, 2.0, 0.5, 0.01)
        custom_power = st.sidebar.number_input("Power (W)", 1, 50, 10)
    with col2:
        custom_utility = st.sidebar.slider("Utility Score", 1, 10, 5)
        custom_cost = st.sidebar.number_input("Cost ($)", 100, 10000, 1000, 100)
    
    # Create custom payload with correct format
    custom_payload = {
        'name': custom_payload_name,
        'weight_kg': custom_weight,
        'power_w': custom_power,
        'utility_score': custom_utility,
        'cost': custom_cost,
        'color': '#FFA500',
        'position': (0.2, 0, 0),
        'size': (0.1, 0.1, 0.1)
    }
    
    # Custom Battery
    st.sidebar.subheader("5. Custom Battery")
    custom_battery_name = st.sidebar.text_input("Battery Name", "Custom LiPo")
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        custom_voltage = st.sidebar.selectbox(
            "Voltage (V)",
            [11.1, 14.8, 22.2],
            index=1
        )
        custom_capacity = st.sidebar.selectbox(
            "Capacity (mAh)",
            [5000, 7000, 10000, 15000, 20000],
            index=2
        )
    with col4:
        custom_ed = st.sidebar.selectbox(
            "Energy Density (Wh/kg)",
            [150, 200, 250, 300],
            index=1
        )
        custom_batt_cost = st.sidebar.number_input("Battery Cost ($)", 50, 500, 150, 10)
    
    # Calculate battery weight based on energy density and capacity
    battery_energy_wh = (custom_capacity / 1000) * custom_voltage
    battery_weight = battery_energy_wh / custom_ed
    
    # Create custom battery with correct format
    custom_battery = {
        'name': custom_battery_name,
        'type': 'Custom',
        'voltage': custom_voltage,
        'capacity_mah': custom_capacity,
        'ed_wh_kg': custom_ed,
        'weight': battery_weight,
        'cost': custom_batt_cost
    }
    
    # Use custom configuration option
    st.sidebar.subheader("6. Optimization Mode")
    use_custom_payload = st.sidebar.checkbox("Use Custom Payload", value=True)
    use_custom_battery = st.sidebar.checkbox("Use Custom Battery", value=True)
    
    # Run Optimization Button
    st.sidebar.markdown("---")
    run_optimization = st.sidebar.button(
        "OPTIMIZE",
        type="primary",
        use_container_width=True
    )
    
    return {
        'mission_name': mission_name,
        'hover_twr': hover_twr,
        'temperature': temperature,
        'custom_payload': custom_payload,
        'custom_battery': custom_battery,
        'custom_ed_wh_kg': custom_ed,
        'use_custom_payload': use_custom_payload,
        'use_custom_battery': use_custom_battery,
        'run_optimization': run_optimization
    }

# ==================== MAIN APPLICATION ====================

def main():
    """Main Streamlit application."""
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'current_config' not in st.session_state:
        st.session_state.current_config = None
    if 'previous_configs' not in st.session_state:
        st.session_state.previous_configs = []
    if 'custom_configs' not in st.session_state:
        st.session_state.custom_configs = {}
    
    # Header
    st.markdown("<h1 class='main-header'>✈️ UAV Digital Twin Optimizer</h1>", unsafe_allow_html=True)
    st.markdown("### Physics-Based Simulation & Multi-Objective Optimization")
    
    # Sidebar
    config_inputs = create_sidebar()
    
    # Store custom configurations
    st.session_state.custom_configs = {
        'custom_payload': config_inputs['custom_payload'],
        'custom_battery': config_inputs['custom_battery']
    }
    
    # Display custom configurations in dashboard
    st.sidebar.markdown("---")
    st.sidebar.subheader("Current Custom Configuration")
    st.sidebar.write(f"**Payload:** {config_inputs['custom_payload']['name']}")
    st.sidebar.write(f"**Weight:** {config_inputs['custom_payload']['weight_kg']} kg")
    st.sidebar.write(f"**Battery:** {config_inputs['custom_battery']['name']}")
    st.sidebar.write(f"**Capacity:** {config_inputs['custom_battery']['capacity_mah']/1000:.1f} Ah")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dashboard", 
        "Optimization", 
        "3D Visualization", 
        "Analysis",
        "Advanced"
    ])
    
    with tab1:
        # Real-Time Metrics
        st.subheader("Real-Time Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("MTOW Limit", f"{MTOW} kg", help="Maximum Takeoff Weight")
        
        with col2:
            st.metric("Base UAV Weight", f"{W_BASE} kg", help="Empty UAV weight")
        
        with col3:
            st.metric("Hover Power", f"{K_HOVER} W/kg", help="Power required per kg for hover")
        
        with col4:
            if st.session_state.current_config:
                config = st.session_state.current_config
                st.metric(
                    "Current Flight Time", 
                    f"{config.get('flight_time', 0):.1f} min",
                    help="Estimated flight time for current configuration"
                )
            else:
                st.metric("Expected Range", "15-45 min", help="Typical flight time range")
        
        # Mission Info
        st.subheader(f"Mission: {config_inputs['mission_name']}")
        
        # Visualize mission priorities
        coeffs = MISSION_COEFFS[config_inputs['mission_name']]
        
        fig_priority = go.Figure(data=[
            go.Bar(
                x=['Flight Time', 'Payload Utility', 'Weight'],
                y=[coeffs['alpha'], coeffs['beta'], coeffs['gamma']],
                marker_color=[coeffs['color'] for _ in range(3)],
                text=[f"{coeffs['alpha']*100:.0f}%", 
                      f"{coeffs['beta']*100:.0f}%", 
                      f"{coeffs['gamma']*100:.0f}%"],
                textposition='auto'
            )
        ])
        
        fig_priority.update_layout(
            title="Mission Priority Weights",
            yaxis=dict(range=[0, 1]),
            height=300
        )
        
        st.plotly_chart(fig_priority, use_container_width=True)
        
        # Display Standard and Custom Payloads
        st.subheader("Available Payloads")
        
        # Create combined payloads dictionary
        all_payloads = PAYLOADS.copy()
        
        # Add custom payload to the list
        if config_inputs['custom_payload']:
            custom_payload_key = config_inputs['custom_payload']['name']
            all_payloads[custom_payload_key] = config_inputs['custom_payload']
        
        for payload_name, payload_data in all_payloads.items():
            with st.expander(f"{payload_name}" + (" (Custom)" if payload_name == custom_payload_key else "")):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Weight:** {payload_data.get('weight_kg', payload_data.get('weight', 'N/A'))} kg")
                    st.write(f"**Power:** {payload_data.get('power_w', payload_data.get('power', 'N/A'))} W")
                with col2:
                    st.write(f"**Utility:** {payload_data.get('utility_score', payload_data.get('utility', 'N/A'))}")
                    st.write(f"**Cost:** ${payload_data.get('cost', 0)}")
    
    # Run optimization when button is clicked
    if config_inputs['run_optimization']:
        with st.spinner("Running digital twin simulation and optimization..."):
            # Add progress bar
            progress_bar = st.progress(0)
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # Create custom configurations dictionary for optimization
            optimization_config = {
                'mission_name': config_inputs['mission_name'],
                'hover_twr': config_inputs['hover_twr'],
                'temperature': config_inputs['temperature'],
                'use_custom_payload': config_inputs['use_custom_payload'],
                'use_custom_battery': config_inputs['use_custom_battery']
            }
            
            # Add custom payload and battery if selected
            if config_inputs['use_custom_payload']:
                optimization_config['custom_payload'] = config_inputs['custom_payload']
            
            if config_inputs['use_custom_battery']:
                optimization_config['custom_battery'] = config_inputs['custom_battery']
                optimization_config['custom_ed_wh_kg'] = config_inputs['custom_ed_wh_kg']
            
            # Run optimization
            results = run_grid_search_optimization(**optimization_config)
            
            st.session_state.results = results
            if results['best_config']:
                st.session_state.current_config = results['best_config']
                # Store for comparison
                st.session_state.previous_configs.append(results['best_config'])
            
            progress_bar.empty()
            st.success("Optimization complete!")
    
    with tab2:
        st.subheader("Optimization Results")
        
        if st.session_state.results:
            results = st.session_state.results
            
            # Best Configuration
            if results['best_config']:
                best = results['best_config']
                
                # Check if custom configuration was used
                used_custom = False
                if config_inputs['use_custom_payload']:
                    if best['payload'] == config_inputs['custom_payload']['name']:
                        used_custom = True
                        st.success(f"### Custom Payload '{best['payload']}' Selected!")
                    else:
                        st.info(f"### Optimal Configuration Found (Standard Payload)")
                else:
                    st.success("### Optimal Configuration Found")
                
                # Display in two columns
                col1, col2 = st.columns(2)
                
                with col1:
                    payload_type = "Custom" if used_custom else "Standard"
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Payload Configuration ({payload_type})</h4>
                        <p><strong>{best['payload']}</strong></p>
                        <p>Weight: {best['payload_data']['weight_kg']:.2f} kg</p>
                        <p>Power: {best['payload_data']['power_w']} W</p>
                        <p>Utility Score: {best['payload_data']['utility_score']}</p>
                        <p>Cost: ${best['payload_data'].get('cost', 0)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Battery Configuration</h4>
                        <p><strong>{best.get('battery_type', 'Custom' if config_inputs['use_custom_battery'] else 'Standard')}</strong></p>
                        <p>Capacity: {best.get('capacity_mah', 0)/1000:.1f} Ah</p>
                        <p>Voltage: {best.get('battery', {}).get('voltage', 'N/A')} V</p>
                        <p>Energy Density: {best.get('battery', {}).get('ed_wh_kg', 'N/A')} Wh/kg</p>
                        <p>Cost: ${best.get('battery', {}).get('cost', 0)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Performance Metrics
                st.subheader("Performance Summary")
                
                perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                
                with perf_col1:
                    st.metric("Flight Time", f"{best['flight_time']:.1f} min")
                
                with perf_col2:
                    st.metric("Total Weight", f"{best['total_weight']:.2f} kg", 
                             delta=f"{best['total_weight']/MTOW*100:.1f}% of MTOW")
                
                with perf_col3:
                    stability_color = "green" if best['stability'] > 70 else "orange" if best['stability'] > 40 else "red"
                    st.metric("Stability", f"{best['stability']:.0f}%", 
                             delta_color="off")
                
                with perf_col4:
                    st.metric("Total Cost", f"${best['total_cost']:,.0f}")
                
                # Constraints check
                st.subheader("Constraint Analysis")
                
                if best['total_weight'] > MTOW:
                    st.error(f"❌ **Weight Constraint Violated:** {best['total_weight']:.2f}kg > {MTOW}kg")
                elif best['total_weight'] > MTOW * 0.9:
                    st.warning(f"⚠️ **Weight Warning:** {best['total_weight']:.2f}kg ({best['total_weight']/MTOW*100:.1f}% of MTOW)")
                else:
                    st.success(f"✅ **Weight OK:** {best['total_weight']:.2f}kg ({best['total_weight']/MTOW*100:.1f}% of MTOW)")
                
                if best['stability'] < 40:
                    st.error(f"❌ **Stability Too Low:** {best['stability']:.0f}% < 40% minimum")
                elif best['stability'] < 70:
                    st.warning(f"⚠️ **Marginal Stability:** {best['stability']:.0f}%")
                else:
                    st.success(f"✅ **Stability Good:** {best['stability']:.0f}%")
            
            # Pareto Frontier
            if results['pareto_front']:
                st.subheader("Pareto Frontier Analysis")
                
                pareto_fig = create_pareto_visualization(results['pareto_front'])
                if pareto_fig:
                    st.plotly_chart(pareto_fig, use_container_width=True)
                    
                    # Show Pareto solutions
                    df_pareto = pd.DataFrame(results['pareto_front'])
                    st.dataframe(
                        df_pareto[['payload', 'flight_time', 'total_weight', 'total_cost', 'score']]
                        .sort_values('score', ascending=False)
                        .head(8)
                        .style.format({
                            'flight_time': '{:.1f}',
                            'total_weight': '{:.2f}',
                            'total_cost': '{:,.0f}',
                            'score': '{:.2f}'
                        })
                    )
        else:
            st.info("Configure parameters and click **OPTIMIZE** to see results")
            
            # Show what optimization does
            st.markdown("""
            ### What Optimization Will Analyze:
            
            **1. Flight Time Maximization**
            - Find optimal cruise parameters
            - Battery utilization efficiency
            - Temperature compensation
            
            **2. Payload Efficiency**
            - Weight vs. capability trade-off
            - Power consumption optimization
            - Aerodynamic impact
            
            **3. Cost-Performance Balance**
            - Component cost analysis
            - Mission requirement matching
            - Return on investment
            
            **Custom Inputs:** Your custom payload and battery configurations will be included in the optimization.
            """)
    
    with tab3:
        st.subheader("3D Configuration Visualization")
        
        if st.session_state.current_config:
            config_data = st.session_state.current_config
            
            # Create 3D visualization
            fig_3d = create_3d_uav_visualization(config_data)
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # CG Information
            cg_position = config_data.get('cg_position', (0, 0, 0))
            stability = config_data.get('stability', 100)
            
            col_cg1, col_cg2 = st.columns(2)
            
            with col_cg1:
                st.info(f"""
                **Center of Gravity Analysis:**
                - Position: X={cg_position[0]:.3f}m, Y={cg_position[1]:.3f}m, Z={cg_position[2]:.3f}m
                - Distance from origin: {np.linalg.norm(cg_position):.3f}m
                - Maximum allowed: 0.05m
                """)
            
            with col_cg2:
                if stability > 70:
                    st.success(f"**Stability:** {stability:.0f}% - Excellent")
                elif stability > 40:
                    st.warning(f"**Stability:** {stability:.0f}% - Acceptable")
                else:
                    st.error(f"**Stability:** {stability:.0f}% - Unstable")
            
            # Performance Dashboard
            st.subheader("Performance Dashboard")
            perf_fig = create_performance_dashboard(config_data)
            if perf_fig:
                st.plotly_chart(perf_fig, use_container_width=True)
        else:
            st.info("Run optimization first to see 3D visualization")
            
            # Show default UAV
            default_fig = create_3d_uav_visualization(None)
            st.plotly_chart(default_fig, use_container_width=True)
    
    with tab4:
        st.subheader("Detailed Analysis")
        
        if st.session_state.current_config:
            config_data = st.session_state.current_config
            
            # Export Configuration
            st.subheader("Export Configuration")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if st.button("Generate Report"):
                    report = {
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "mission": config_inputs['mission_name'],
                        "optimization_parameters": {
                            "hover_twr": config_inputs['hover_twr'],
                            "temperature": config_inputs['temperature'],
                            "use_custom_payload": config_inputs['use_custom_payload'],
                            "use_custom_battery": config_inputs['use_custom_battery']
                        },
                        "configuration": {
                            "payload": config_data['payload'],
                            "payload_details": config_data['payload_data'],
                            "battery": config_data['battery'],
                            "total_weight_kg": config_data['total_weight'],
                            "cg_position": config_data['cg_position']
                        },
                        "performance_metrics": {
                            "flight_time_min": config_data.get('flight_time', 0),
                            "total_power_w": config_data.get('P_total', 0),
                            "stability_percent": config_data.get('stability', 100),
                            "total_cost_usd": config_data.get('total_cost', 0),
                            "score": config_data.get('score', 0)
                        }
                    }
                    
                    st.download_button(
                        label="Download JSON Report",
                        data=json.dumps(report, indent=2),
                        file_name="uav_digital_twin_report.json",
                        mime="application/json"
                    )
            
            with export_col2:
                if st.button("Export to CSV"):
                    df_export = pd.DataFrame([config_data])
                    csv = df_export.to_csv(index=False)
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="uav_configuration.csv",
                        mime="text/csv"
                    )
            
            # Temperature Sensitivity Analysis
            st.subheader("Temperature Sensitivity")
            
            temperatures = np.arange(-10, 41, 2)
            flight_times = []
            
            for temp in temperatures:
                factor = np.interp(temp, [-10, 0, 10, 20, 30, 40], [0.7, 0.8, 0.9, 1.0, 0.95, 0.85])
                flight_times.append(config_data.get('flight_time', 30) * factor)
            
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=temperatures,
                y=flight_times,
                mode='lines+markers',
                line=dict(color='#FF6B6B', width=3),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 107, 0.2)',
                name='Flight Time'
            ))
            
            # Add current temperature marker
            current_temp = config_inputs['temperature']
            current_flight = config_data.get('flight_time', 30)
            
            fig_temp.add_trace(go.Scatter(
                x=[current_temp],
                y=[current_flight],
                mode='markers',
                marker=dict(size=15, color='yellow', symbol='star'),
                name='Current Configuration'
            ))
            
            fig_temp.update_layout(
                title="Flight Time vs Temperature",
                xaxis_title="Temperature (°C)",
                yaxis_title="Flight Time (min)",
                height=400
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # Power vs Weight Analysis
            st.subheader("Power vs Weight Analysis")
            
            # Generate theoretical curve
            weights = np.linspace(W_BASE, MTOW, 20)
            powers = []
            
            for w in weights:
                p = K_HOVER * w * 1.15 + P_AVIONICS
                powers.append(p)
            
            fig_power = go.Figure()
            fig_power.add_trace(go.Scatter(
                x=weights,
                y=powers,
                mode='lines',
                line=dict(color='#4ECDC4', width=3),
                name='Theoretical Curve'
            ))
            
            # Add current point
            fig_power.add_trace(go.Scatter(
                x=[config_data.get('total_weight', 0)],
                y=[config_data.get('P_total', 0)],
                mode='markers',
                marker=dict(size=15, color='#FF6B6B', symbol='circle'),
                name='Current Configuration'
            ))
            
            fig_power.update_layout(
                title="Power Requirement vs Total Weight",
                xaxis_title="Total Weight (kg)",
                yaxis_title="Power Required (W)",
                height=400
            )
            
            st.plotly_chart(fig_power, use_container_width=True)
        else:
            st.info("Run optimization first to see detailed analysis")
    
    with tab5:
        st.subheader("Advanced Features")
        
        if st.session_state.current_config:
            # Mission Planning
            mission_type = create_mission_planning_tab()
            
            # Cost Analysis
            create_cost_analysis_tab(st.session_state.current_config)
            
            # Sensitivity Analysis
            create_sensitivity_analysis_tab(st.session_state.current_config)
            
            # Configuration Comparison
            if len(st.session_state.previous_configs) >= 2:
                create_comparison_tool(st.session_state.previous_configs[-3:])  # Last 3 configs
            else:
                st.info("Run optimization multiple times to compare configurations")
        else:
            st.info("Run optimization first to access advanced features")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>UAV Digital Twin Optimizer • Physics-Based Simulation • Multi-Objective Optimization</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    main()