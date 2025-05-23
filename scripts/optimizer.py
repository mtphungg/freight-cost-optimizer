import csv
import sys
import os
import argparse
from tabulate import tabulate
import matplotlib.pyplot as plt

def load_data(file_path):
    """Load freight rate data from a CSV file."""
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def calculate_total_cost(row, weight_kg):
    return float(row['rate_per_km']) * float(row['distance_km']) * weight_kg

def find_best_option(data, origin, destination, weight_kg):
    options = [row for row in data if row['origin'] == origin and row['destination'] == destination]
    for row in options:
        row['total_cost'] = calculate_total_cost(row, weight_kg)
    return sorted(options, key=lambda x: x['total_cost'])

def parse_weight(weight_str):
    """Convert user input string to float weight in kg."""
    try:
        weight_str = weight_str.strip().lower()
        if weight_str.endswith('kg'):
            return float(weight_str.replace('kg', '').strip())
        elif weight_str.endswith('lbs') or weight_str.endswith('lb'):
            weight_val = float(weight_str.replace('lbs', '').replace('lb', '').strip())
            return weight_val * 0.453592
        else:
            return float(weight_str)  # Assume kg if no unit
    except ValueError:
        print("❌ Error: Invalid weight format. Use 1000, '1000kg', or '2204 lbs'.")
        sys.exit(1)

def generate_charts(results):
    modes = [row['mode'] for row in results]
    costs = [row['total_cost'] for row in results]
    times = [float(row['transit_days']) for row in results]
    emissions = [float(row['co2_per_km']) for row in results]

    def plot_bar(values, ylabel, title, filename):
        plt.figure()
        plt.bar(modes, values, color='skyblue')
        plt.xlabel('Transport Mode')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.xticks(rotation=15)
        plt.tight_layout()
        plt.savefig(f'output/{filename}')
        plt.close()

    plot_bar(costs, 'Total Cost (USD)', 'Total Cost by Mode', 'chart_cost.png')
    plot_bar(times, 'Transit Time (Days)', 'Transit Time by Mode', 'chart_time.png')
    plot_bar(emissions, 'CO₂ Emissions (kg/km)', 'CO₂ Emissions by Mode', 'chart_emissions.png')

    print("📊 Charts saved to output/: chart_cost.png, chart_time.png, chart_emissions.png")

def main():
    parser = argparse.ArgumentParser(description="📦 Freight Cost Optimizer")
    parser.add_argument('origin', help="Origin city (e.g., Shanghai)")
    parser.add_argument('destination', help="Destination city (e.g., Los Angeles)")
    parser.add_argument('weight', help="Shipment weight (e.g., 1000, 1000kg, or 2204 lbs)")
    parser.add_argument('--data', default='data/freight_rates.csv', help="Path to freight_rates.csv file")
    args = parser.parse_args()

    origin = args.origin
    destination = args.destination
    weight_kg = parse_weight(args.weight)
    data_file = args.data

    try:
        data = load_data(data_file)
    except FileNotFoundError:
        print(f"❌ Error: File not found → {data_file}")
        return
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    results = find_best_option(data, origin, destination, weight_kg)

    if not results:
        print("⚠️ No available routes for this origin and destination.")
        return

    print("\n📦 Available Shipping Options:")
    print(tabulate(results, headers="keys", floatfmt=".2f"))

    cheapest = min(results, key=lambda x: x['total_cost'])
    fastest = min(results, key=lambda x: float(x['transit_days']))
    greenest = min(results, key=lambda x: float(x['co2_per_km']))

    print("\n📊 Summary Insight:")
    print(f"  🔹 Cheapest: {cheapest['mode']} at ${cheapest['total_cost']:.2f}")
    print(f"  🚀 Fastest: {fastest['mode']} in {fastest['transit_days']} days")
    print(f"  🌱 Greenest: {greenest['mode']} with {greenest['co2_per_km']} kg CO₂/km")

    os.makedirs('output', exist_ok=True)
    output_file = f"output/recommendations_{origin}_{destination}_{int(weight_kg)}kg.csv"
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Results saved to: {output_file}")

    generate_charts(results)

if __name__ == "__main__":
    main()
