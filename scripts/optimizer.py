import csv
import sys
import os
from tabulate import tabulate
import matplotlib.pyplot as plt

def load_data(file_path):
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
    weight_str = weight_str.strip().lower()
    if weight_str.endswith('lbs') or weight_str.endswith('lb'):
        weight_val = float(weight_str.replace('lbs','').replace('lb','').strip())
        return weight_val * 0.453592  # lbs to kg
    else:
        return float(weight_str)  # assume kg

def main():
    if len(sys.argv) != 4:
        print("Usage: python optimizer.py <origin> <destination> <weight_kg or weight_lbs>")
        return

    origin = sys.argv[1]
    destination = sys.argv[2]
    weight_kg = parse_weight(sys.argv[3])

    data = load_data('data/freight_rates.csv')
    results = find_best_option(data, origin, destination, weight_kg)

    if not results:
        print("No available routes for this origin and destination.")
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
        plt.tight_layout()
        plt.savefig(f'output/{filename}')
        plt.close()

    plot_bar(costs, 'Total Cost (USD)', 'Total Cost by Mode', 'chart_cost.png')
    plot_bar(times, 'Transit Time (Days)', 'Transit Time by Mode', 'chart_time.png')
    plot_bar(emissions, 'CO₂ Emissions (kg/km)', 'CO₂ Emissions by Mode', 'chart_emissions.png')

    print("📊 Charts saved to output/: chart_cost.png, chart_time.png, chart_emissions.png")

if __name__ == "__main__":
    main()
