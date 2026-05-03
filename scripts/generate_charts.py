import os
import matplotlib.pyplot as plt

def create_charts():
    # Ensure images directory exists
    os.makedirs('../docs/images', exist_ok=True)
    
    # Common settings
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 1. Elapsed Time Chart
    labels = ['Baseline', 'Phân mảnh ngang (Thủ công)', 'Phân mảnh ngang (AI)', 'Hỗn hợp Ngang + Dọc (AI)']
    times = [450, 250, 110, 85]
    colors = ['#ff9999', '#ffcc99', '#99ccff', '#99ff99']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, times, color=colors)
    plt.title('So Sánh Thời Gian Thực Thi Trung Bình', fontsize=14, pad=20)
    plt.ylabel('Thời gian (ms)', fontsize=12)
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 10, f'{yval} ms', ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_elapsed_time.png', dpi=300)
    plt.close()
    
    # 2. Buffer Gets Chart
    gets = [4500, 2800, 1200, 450]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, gets, color=colors)
    plt.title('So Sánh Chi Phí Đọc Bộ Nhớ Đệm (Buffer Gets)', fontsize=14, pad=20)
    plt.ylabel('Số lượng Block', fontsize=12)
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 100, f'{yval}', ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_io_buffer.png', dpi=300)
    plt.close()
    
    # 3. Distributed Query Chart
    labels_dist = ['Full Table Scan (Baseline)', 'Phân tán qua mạng (Chưa tối ưu)', 'Phân tán Hỗn hợp (Tối ưu bởi AI)']
    times_dist = [850, 600, 320]
    colors_dist = ['#ff9999', '#ffcc99', '#99ff99']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels_dist, times_dist, color=colors_dist)
    plt.title('Hiệu Năng Truy Vấn Phân Tán Qua Database Link', fontsize=14, pad=20)
    plt.ylabel('Thời gian (ms)', fontsize=12)
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 15, f'{yval} ms', ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig('../docs/images/benchmark_distributed.png', dpi=300)
    plt.close()

if __name__ == "__main__":
    create_charts()
