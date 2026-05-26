#!/usr/bin/env python3
"""
爬取进度实时监控工具
"""

import os
import time
import json
from datetime import datetime

def monitor_chinese_crawler():
    """监控中文文档爬取进度"""
    print("=" * 60)
    print("中文文档爬取进度监控")
    print("=" * 60)
    
    # 检查中文文档目录
    chinese_dir = "chinese_tech_docs"
    
    print("\n中文爬取状态:")
    
    if not os.path.exists(chinese_dir):
        print("   中文文档目录尚未创建")
        print("   爬取器可能正在处理第一个技术栈")
        return False
    
    files = os.listdir(chinese_dir)
    if not files:
        print("   中文文档目录为空")
        print("   爬取器可能正在下载和翻译内容")
        return False
    
    # 检查技术栈文件
    tech_stacks = ["spring-boot", "java", "docker", "python", "vue", "react", "redis", "mysql"]
    
    completed_techs = []
    total_docs = 0
    
    for tech in tech_stacks:
        filename = os.path.join(chinese_dir, f"{tech}_chinese_docs.json")
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                doc_count = len(documents)
                total_docs += doc_count
                completed_techs.append((tech, doc_count))
                print(f"   [完成] {tech}: {doc_count} 个文档片段")
            except:
                print(f"   [警告] {tech}: 文件存在但无法读取")
        else:
            print(f"   [未开始] {tech}: 尚未完成")
    
    # 检查合并文件
    all_filename = os.path.join(chinese_dir, "all_tech_chinese_docs.json")
    if os.path.exists(all_filename):
        print(f"   合并文件: 已生成")
    else:
        print(f"   合并文件: 尚未生成")
    
    # 进度统计
    progress = len(completed_techs) / len(tech_stacks) * 100
    print(f"\n总体进度: {progress:.1f}%")
    print(f"已完成技术栈: {len(completed_techs)}/{len(tech_stacks)}")
    print(f"总文档片段: {total_docs}")
    
    return len(completed_techs) > 0

def monitor_real_time():
    """实时监控"""
    print("\n开始实时监控（每30秒更新一次）...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            monitor_chinese_crawler()
            
            print(f"\n最后更新: {datetime.now().strftime('%H:%M:%S')}")
            print("等待30秒后更新...")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='爬取进度监控工具')
    parser.add_argument('--monitor', action='store_true', help='开启实时监控模式')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_real_time()
    else:
        monitor_chinese_crawler()

if __name__ == "__main__":
    main()