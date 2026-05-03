import os
import json
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statistics import mean

def get_latest_json(pattern):
    """Find the most recent JSON file matching a pattern."""
    files = glob.glob(pattern)
    if not files:
        return None
    return sorted(files)[-1]

def load_json(filepath):
    """Load and return benchmark results from JSON."""
    if not filepath or not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def calc_averages(data):
    """Calculate average elapsed time and buffer gets across all queries."""
    results = data.get("results", {})
    times = [v["avg_elapsed_ms"] for v in results.values()]
    buffers = [v["avg_buffer_gets"] for v in results.values()]
    return {
        "avg_time": mean(times) if times else 0,
        "avg_buffer": mean(buffers) if buffers else 0,
        "raw": results
    }

def main():
    # Load all 4 benchmark JSON files
    base = load_json(get_latest_json("benchmark_baseline_*.json"))
    static = load_json(get_latest_json("benchmark_static_partition_*.json"))
    gendba = load_json(get_latest_json("benchmark_gendba_optimized_*.json"))
    dist = load_json(get_latest_json("benchmark_full_distributed_*.json"))
    
    if not all([base, static, gendba, dist]):
        print("ERROR: Missing benchmark JSON files. Run benchmarks first.")
        return
    
    b = calc_averages(base)
    s = calc_averages(static)
    g = calc_averages(gendba)
    d = calc_averages(dist)
    
    print(f"Baseline avg time: {b['avg_time']:.2f}ms, avg buffer: {b['avg_buffer']:.0f}")
    print(f"Static avg time: {s['avg_time']:.2f}ms, avg buffer: {s['avg_buffer']:.0f}")
    print(f"GenDBA avg time: {g['avg_time']:.2f}ms, avg buffer: {g['avg_buffer']:.0f}")
    print(f"Distributed avg time: {d['avg_time']:.2f}ms, avg buffer: {d['avg_buffer']:.0f}")
    
    os.makedirs('../docs/images', exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    
    labels = ['Baseline', 'Static Partition', 'Gen-DBA\n(Ngang)', 'Phan tan\nHon hop']
    colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
    
    # Chart 1: Elapsed Time
    times = [b['avg_time'], s['avg_time'], g['avg_time'], d['avg_time']]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, times, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_title('So Sanh Thoi Gian Thuc Thi Trung Binh (ms)\n(Du lieu thuc te tu Benchmark JSON)', 
                 fontsize=14, pad=15)
    ax.set_ylabel('Thoi gian (ms)', fontsize=12)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 2, 
                f'{yval:.1f}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_elapsed_time.png', dpi=200)
    plt.close()
    print("Saved: benchmark_elapsed_time.png")
    
    # Chart 2: Buffer Gets
    buffers = [b['avg_buffer'], s['avg_buffer'], g['avg_buffer'], d['avg_buffer']]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, buffers, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_title('So Sanh Chi Phi Doc Bo Nho Dem (Buffer Gets)\n(Du lieu thuc te tu Benchmark JSON)', 
                 fontsize=14, pad=15)
    ax.set_ylabel('So luong Block', fontsize=12)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 10, 
                f'{int(yval)}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_io_buffer.png', dpi=200)
    plt.close()
    print("Saved: benchmark_io_buffer.png")
    
    # Chart 3: Distributed comparison for Q6 (Revenue Forecast)
    q6_key = "Q6_revenue_forecast"
    q6_base = base["results"][q6_key]["avg_elapsed_ms"]
    q6_static = static["results"][q6_key]["avg_elapsed_ms"]
    q6_dist = dist["results"][q6_key]["avg_elapsed_ms"]
    
    labels_dist = ['Baseline\n(Full Scan)', 'Static\nPartition', 'Phan tan\nHon hop (AI)']
    colors_dist = ['#e74c3c', '#f39c12', '#2ecc71']
    times_dist = [q6_base, q6_static, q6_dist]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels_dist, times_dist, color=colors_dist, edgecolor='white', linewidth=1.5)
    ax.set_title('Hieu Nang Truy Van Phan Tan (Q6 - Revenue Forecast)\n(Du lieu thuc te tu Benchmark JSON)', 
                 fontsize=14, pad=15)
    ax.set_ylabel('Thoi gian (ms)', fontsize=12)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, 
                f'{yval:.2f}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_distributed.png', dpi=200)
    plt.close()
    print("Saved: benchmark_distributed.png")
    
    print("\nAll 3 charts generated from REAL benchmark data successfully!")

if __name__ == "__main__":
    main()
