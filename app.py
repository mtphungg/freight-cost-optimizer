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

# Load data first to get dropdown options
try:
    df_preview = pd.read_csv(data_file)
    origin_options = df_preview['origin'].unique().tolist()
    destination_options = df_preview['destination'].unique().tolist()
except Exception as e:
    st.sidebar.error("⚠️ Failed to load CSV. Check the path.")
    origin_options = []
    destination_options = []

# Use dropdowns for city selection
origin = st.sidebar.selectbox("🌍 Origin", origin_options)
destination = st.sidebar.selectbox("🏁 Destination", destination_options)
weight_input = st.sidebar.text_input("⚖️ Weight (e.g., 1000, 2204 lbs)", value="1000")

# 🧮 Run optimization when user clicks
if st.sidebar.button("Calculate"):
    try:
        weight_kg = parse_weight(weight_input)
        data = load_data(data_file)
        results = find_best_option(data, origin, destination, weight_kg)

        if not results:
            st.warning("⚠️ No available routes for this origin and destination.")
        else:
            st.success("✅ Results found!")

            st.markdown("### 📦 Shipping Options")
            st.dataframe(results)

            cheapest = min(results, key=lambda x: x['total_cost'])
            fastest = min(results, key=lambda x: float(x['transit_days']))
            greenest = min(results, key=lambda x: float(x['co2_per_km']))

            st.markdown("### 📊 Summary Insight")
            st.write(f"**🔹 Cheapest:** {cheapest['mode']} at ${cheapest['total_cost']:.2f}")
            st.write(f"**🚀 Fastest:** {fastest['mode']} in {fastest['transit_days']} days")
            st.write(f"**🌱 Greenest:** {greenest['mode']} with {greenest['co2_per_km']} kg CO₂/km")

            generate_charts(results)

            st.markdown("### 📈 Charts")
            st.image("output/chart_cost.png", caption="Cost by Mode", use_column_width=True)
            st.image("output/chart_time.png", caption="Transit Time by Mode", use_column_width=True)
            st.image("output/chart_emissions.png", caption="CO₂ Emissions by Mode", use_column_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
