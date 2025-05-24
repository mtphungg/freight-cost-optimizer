import streamlit as st
import pandas as pd
from scripts.optimizer import load_data, find_best_option, parse_weight, generate_charts

st.set_page_config(page_title="Freight Cost Optimizer", layout="centered")

# 🚛 Page title
st.markdown("<h1 style='text-align: center;'>🚛 Freight Cost Optimizer</h1>", unsafe_allow_html=True)
st.markdown("Compare freight modes (air, sea, rail) by cost, speed, and CO₂ emissions.")

# 📦 Sidebar input
st.sidebar.header("📦 Shipment Details")
data_file = st.sidebar.text_input("📄 CSV Path", value="data/freight_rates.csv")

# Load data to populate dropdowns
try:
    df_preview = pd.read_csv(data_file)
    origin_options = df_preview['origin'].unique().tolist()
    destination_options = df_preview['destination'].unique().tolist()
except Exception as e:
    st.sidebar.error("⚠️ Failed to load CSV. Check the path.")
    origin_options = []
    destination_options = []

origin = st.sidebar.selectbox("🌍 Origin", origin_options)
destination = st.sidebar.selectbox("🏁 Destination", destination_options)
weight_input = st.sidebar.text_input("⚖️ Weight (e.g., 1000, 2204 lbs)", value="1000")

goal = st.sidebar.selectbox("🎯 Optimization Goal", ["Cheapest", "Fastest", "Greenest"])

# NEW: Constraint inputs
st.sidebar.markdown("### ⚙️ Optional Filters")
max_cost = st.sidebar.number_input("💰 Max Cost (USD)", min_value=0, value=100000000)
max_days = st.sidebar.number_input("⏱ Max Transit Days", min_value=1, value=999)

# Bulk input
st.sidebar.markdown("---")
bulk_text = st.sidebar.text_area(
    "📋 Paste multiple shipments:\nFormat: origin,destination,weight",
    height=140,
    placeholder="Shanghai,Los Angeles,1000kg\nHamburg,New York,1500\nSingapore,Sydney,2204 lbs"
)

def parse_bulk_input(input_text):
    lines = input_text.strip().split('\n')
    rows = []
    for line in lines:
        parts = [x.strip() for x in line.split(',')]
        if len(parts) == 3:
            origin, destination, weight_str = parts
            rows.append((origin, destination, weight_str))
    return rows

def filter_constraints(routes, max_cost, max_days):
    return [
        row for row in routes
        if row['total_cost'] <= max_cost and float(row['transit_days']) <= max_days
    ]

# 🧮 Run optimization when button is clicked
if st.sidebar.button("Calculate"):
    try:
        weight_kg = parse_weight(weight_input)
        data = load_data(data_file)
        results = find_best_option(data, origin, destination, weight_kg)

        # Filter by constraints
        filtered = filter_constraints(results, max_cost, max_days)

        if not filtered:
            st.warning("⚠️ No routes match your filters (max cost/time). Try adjusting them.")
        else:
            st.success("✅ Valid routes found!")

            # Recommend based on goal
            if goal == "Cheapest":
                best = min(filtered, key=lambda x: x['total_cost'])
                st.markdown("### 🎯 Recommended Route: Cheapest")
            elif goal == "Fastest":
                best = min(filtered, key=lambda x: float(x['transit_days']))
                st.markdown("### 🎯 Recommended Route: Fastest")
            elif goal == "Greenest":
                best = min(filtered, key=lambda x: float(x['co2_per_km']))
                st.markdown("### 🎯 Recommended Route: Greenest")

            st.write({
                "Mode": best['mode'],
                "Cost": f"${best['total_cost']:.2f}",
                "Transit Days": best['transit_days'],
                "CO₂ per km": best['co2_per_km']
            })

            st.markdown("### 📦 Filtered Shipping Options")
            st.dataframe(filtered)

            generate_charts(filtered)

            st.markdown("### 📈 Charts")
            st.image("output/chart_cost.png", caption="Cost by Mode", use_column_width=True)
            st.image("output/chart_time.png", caption="Transit Time by Mode", use_column_width=True)
            st.image("output/chart_emissions.png", caption="CO₂ Emissions by Mode", use_column_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# 🧮 Bulk input logic
if bulk_text:
    try:
        bulk_rows = parse_bulk_input(bulk_text)
        data = load_data(data_file)
        df_output = []

        for origin, destination, weight_str in bulk_rows:
            weight_kg = parse_weight(weight_str)
            results = find_best_option(data, origin, destination, weight_kg)
            filtered = filter_constraints(results, max_cost, max_days)
            if filtered:
                if goal == "Cheapest":
                    best = min(filtered, key=lambda x: x['total_cost'])
                elif goal == "Fastest":
                    best = min(filtered, key=lambda x: float(x['transit_days']))
                elif goal == "Greenest":
                    best = min(filtered, key=lambda x: float(x['co2_per_km']))
                df_output.append({
                    'origin': origin,
                    'destination': destination,
                    'mode': best['mode'],
                    'total_cost': best['total_cost'],
                    'transit_days': best['transit_days'],
                    'co2_per_km': best['co2_per_km']
                })
            else:
                df_output.append({
                    'origin': origin,
                    'destination': destination,
                    'mode': 'N/A',
                    'total_cost': 'No valid route',
                    'transit_days': '',
                    'co2_per_km': ''
                })

        st.markdown("### 📋 Bulk Optimization Results")
        st.dataframe(pd.DataFrame(df_output))

    except Exception as e:
        st.error(f"❌ Error processing bulk input: {e}")
