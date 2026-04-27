"""Generate charts from benchmark results for the project report."""
import json
import os
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'DejaVu Sans'

OUTPUT_DIR = "benchmark_charts"


def load_combined_results(filename):
    """Load the combined benchmark JSON file."""
    with open(filename) as f:
        data = json.load(f)
    return data["scenarios"]


def plot_latency_comparison(baseline, static, gendba, output_file):
    """Create grouped bar chart comparing query latency across 3 scenarios."""
    queries = list(baseline.keys())
    labels = [baseline[q]["name"][:25] for q in queries]

    base_vals = [baseline[q]["avg_elapsed_ms"] for q in queries]
    static_vals = [static[q]["avg_elapsed_ms"] for q in queries]
    gendba_vals = [gendba[q]["avg_elapsed_ms"] for q in queries]

    x = np.arange(len(queries))
    width = 0.25

    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width, base_vals, width, label='Baseline (No Partition)', color='#e74c3c', alpha=0.85)
    bars2 = ax.bar(x, static_vals, width, label='Static Partition (Yearly)', color='#f39c12', alpha=0.85)
    bars3 = ax.bar(x + width, gendba_vals, width, label='Gen-DBA Optimized', color='#2ecc71', alpha=0.85)

    ax.set_xlabel('TPC-H Queries', fontsize=12)
    ax.set_ylabel('Average Execution Time (ms)', fontsize=12)
    ax.set_title('Query Latency Comparison: Baseline vs Static vs Gen-DBA', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"  Saved: {output_file}")


def plot_improvement_vs_baseline(baseline, gendba, output_file):
    """Create horizontal bar chart showing % improvement of Gen-DBA vs Baseline."""
    queries = list(baseline.keys())
    improvements = []
    names = []

    for q in queries:
        base = baseline[q]["avg_elapsed_ms"]
        opt = gendba[q]["avg_elapsed_ms"]
        if base > 0:
            pct = ((base - opt) / base) * 100
            improvements.append(pct)
            names.append(baseline[q]["name"][:30])

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in improvements]
    bars = ax.barh(names, improvements, color=colors, alpha=0.85)

    # Add value labels on bars
    for bar, val in zip(bars, improvements):
        x_pos = bar.get_width() + 1 if val >= 0 else bar.get_width() - 5
        ax.text(x_pos, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%',
                va='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Improvement (%)', fontsize=12)
    ax.set_title('Gen-DBA vs Baseline: Performance Change per Query', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"  Saved: {output_file}")


def plot_gendba_vs_static(static, gendba, output_file):
    """Create horizontal bar chart showing Gen-DBA advantage over static partitioning."""
    queries = list(static.keys())
    improvements = []
    names = []

    for q in queries:
        s = static[q]["avg_elapsed_ms"]
        g = gendba[q]["avg_elapsed_ms"]
        if s > 0:
            pct = ((s - g) / s) * 100
            improvements.append(pct)
            names.append(static[q]["name"][:30])

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in improvements]
    bars = ax.barh(names, improvements, color=colors, alpha=0.85)

    for bar, val in zip(bars, improvements):
        x_pos = bar.get_width() + 1 if val >= 0 else bar.get_width() - 5
        ax.text(x_pos, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%',
                va='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Improvement (%)', fontsize=12)
    ax.set_title('Gen-DBA vs Static Partition: Performance Change per Query', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"  Saved: {output_file}")


def plot_buffer_gets_comparison(baseline, gendba, output_file):
    """Compare buffer gets (I/O operations) between baseline and Gen-DBA."""
    queries = list(baseline.keys())
    base_vals = [baseline[q]["avg_buffer_gets"] for q in queries]
    gendba_vals = [gendba[q]["avg_buffer_gets"] for q in queries]
    names = [baseline[q]["name"][:20] for q in queries]

    x = np.arange(len(queries))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width/2, base_vals, width, label='Baseline', color='#e74c3c', alpha=0.85)
    ax.bar(x + width/2, gendba_vals, width, label='Gen-DBA', color='#2ecc71', alpha=0.85)

    ax.set_ylabel('Buffer Gets (I/O Operations)', fontsize=12)
    ax.set_title('I/O Reduction: Buffer Gets Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right', fontsize=8)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"  Saved: {output_file}")


def plot_partition_pruning_summary(baseline, static, gendba, output_file):
    """Create a summary table-style chart showing partition pruning status."""
    queries = list(baseline.keys())
    names = [baseline[q]["name"][:28] for q in queries]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('off')

    col_labels = ['Query', 'Baseline', 'Static', 'Gen-DBA']
    table_data = []
    for q in queries:
        row = [
            baseline[q]["name"][:28],
            "NO" if not baseline[q]["partition_pruning"] else "YES",
            "YES" if static[q]["partition_pruning"] else "NO",
            "YES" if gendba[q]["partition_pruning"] else "NO",
        ]
        table_data.append(row)

    table = ax.table(cellText=table_data, colLabels=col_labels,
                     loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)

    # Color coding for YES/NO cells
    for i, row in enumerate(table_data):
        for j in range(1, 4):
            cell = table[i + 1, j]
            if row[j] == "YES":
                cell.set_facecolor('#d5f5e3')
            else:
                cell.set_facecolor('#fadbd8')

    # Header styling
    for j in range(4):
        table[0, j].set_facecolor('#2c3e50')
        table[0, j].set_text_props(color='white', fontweight='bold')

    ax.set_title('Partition Pruning Status Across Scenarios', fontsize=14,
                 fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"  Saved: {output_file}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load the combined benchmark results
    combined_file = "benchmark_combined_20260423_142137.json"
    print(f"Loading results from: {combined_file}")
    scenarios = load_combined_results(combined_file)

    baseline = scenarios["baseline"]
    static = scenarios["static"]
    gendba = scenarios["gendba"]

    print("\nGenerating charts...")

    plot_latency_comparison(
        baseline, static, gendba,
        os.path.join(OUTPUT_DIR, "latency_comparison.png")
    )

    plot_improvement_vs_baseline(
        baseline, gendba,
        os.path.join(OUTPUT_DIR, "gendba_vs_baseline.png")
    )

    plot_gendba_vs_static(
        static, gendba,
        os.path.join(OUTPUT_DIR, "gendba_vs_static.png")
    )

    plot_buffer_gets_comparison(
        baseline, gendba,
        os.path.join(OUTPUT_DIR, "buffer_gets_comparison.png")
    )

    plot_partition_pruning_summary(
        baseline, static, gendba,
        os.path.join(OUTPUT_DIR, "partition_pruning_summary.png")
    )

    print(f"\nAll charts saved to: {OUTPUT_DIR}/")
