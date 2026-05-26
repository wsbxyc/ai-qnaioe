#!/usr/bin/env python3
"""
爬取进度监控工具
实时监控文档爬取进度和状态
"""

import os
import time
import json
from datetime import datetime

def check_crawler_status():
    """检查爬取器状态"""
    print("=" * 60)
    print("爬取进度监控")
    print("=" * 60)
    
    # 检查快速爬取目录
    quick_dir = "tech_docs"
    full_dir = "full_tech_docs"
    
    print("\n快速爬取状态:")
    quick_status = check_directory_status(quick_dir)
    
    print("\n完整爬取状态:")
    full_status = check_directory_status(full_dir)
    
    print("\n爬取完成判断标准:")
    print("快速爬取完成: 每个技术栈都有对应的 _docs.json 文件")
    print("完整爬取完成: 每个技术栈都有对应的 _full_docs.json 文件")
    print("知识库集成完成: 存在 all_tech_docs.json 或 all_tech_full_docs.json")
    
    return quick_status, full_status

def check_directory_status(directory: str):
    """检查目录状态"""
    if not os.path.exists(directory):
        print(f"   ❌ 目录不存在: {directory}")
        return False
    
    files = os.listdir(directory)
    if not files:
        print(f"   ⏳ 目录为空: {directory}")
        return False
    
    # 检查技术栈文件
    tech_stacks = ["spring-boot", "java", "docker", "python", "vue", "react", "redis", "mysql"]
    
    tech_files = {}
    total_docs = 0
    
    for filename in files:
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            
            # 获取文件大小和修改时间
            file_size = os.path.getsize(filepath)
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # 统计文档数量
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                doc_count = len(docs)
                total_docs += doc_count
            except:
                doc_count = 0
            
            # 识别技术栈
            tech_name = "unknown"
            for tech in tech_stacks:
                if tech in filename:
                    tech_name = tech
                    break
            
            tech_files[tech_name] = {
                'filename': filename,
                'size': file_size,
                'mod_time': mod_time,
                'doc_count': doc_count
            }
    
    # 显示状态
    print(f"   目录: {directory}")
    print(f"   文件数: {len(files)}")
    print(f"   总文档片段: {total_docs}")
    
    # 显示各技术栈状态
    for tech in tech_stacks:
        if tech in tech_files:
            file_info = tech_files[tech]
            print(f"   [完成] {tech}: {file_info['doc_count']} 个片段 ({file_info['filename']})")
        else:
            print(f"   [未开始] {tech}: 未找到文档文件")
    
    return len(tech_files) > 0

def monitor_real_time():
    """实时监控"""
    print("\n开始实时监控（每30秒更新一次）...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            check_crawler_status()
            
            # 检查是否有新的日志输出
            check_recent_logs()
            
            print(f"\n最后更新: {datetime.now().strftime('%H:%M:%S')}")
            print("等待30秒后更新...")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")

def check_recent_logs():
    """检查最近的日志输出"""
    log_files = ["crawler.log", "full_crawler.log"]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                # 读取最后几行日志
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n📋 最近日志 ({log_file}):")
                        for line in lines[-5:]:  # 最后5行
                            print(f"   {line.strip()}")
            except:
                pass

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='爬取进度监控工具')
    parser.add_argument('--monitor', action='store_true', help='开启实时监控模式')
    parser.add_argument('--check', action='store_true', help='单次检查状态')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_real_time()
    else:
        check_crawler_status()

if __name__ == "__main__":
    main()