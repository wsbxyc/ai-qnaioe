#!/usr/bin/env python3
"""
企业级智能技术助手 - 文档爬取和集成启动脚本
一键启动文档爬取和知识库集成
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    
    try:
        # 检查是否已安装pip
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
        
        # 安装依赖
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖包安装成功")
            return True
        else:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装依赖包时出错: {e}")
        return False

def run_crawler():
    """运行文档爬取器"""
    print("\n开始爬取技术文档...")
    
    try:
        # 运行爬取器
        result = subprocess.run([
            sys.executable, "tech_docs_crawler.py", 
            "--max-pages", "25",
            "--output-dir", "tech_docs"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 文档爬取完成")
            print(result.stdout)
            return True
        else:
            print(f"❌ 文档爬取失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行爬取器时出错: {e}")
        return False

def run_integrator():
    """运行知识库集成器"""
    print("\n开始集成知识库到Elasticsearch...")
    
    try:
        # 检查Elasticsearch是否运行
        import requests
        try:
            response = requests.get("http://localhost:9200", timeout=5)
            if response.status_code == 200:
                print("✅ Elasticsearch服务正常")
            else:
                print("⚠️  Elasticsearch可能未运行，但继续尝试集成...")
        except:
            print("⚠️  Elasticsearch可能未运行，但继续尝试集成...")
        
        # 运行集成器
        result = subprocess.run([
            sys.executable, "knowledge_integrator.py",
            "--docs-dir", "tech_docs",
            "--es-host", "localhost",
            "--es-port", "9200"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 知识库集成完成")
            print(result.stdout)
            return True
        else:
            print(f"❌ 知识库集成失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行集成器时出错: {e}")
        return False

def check_documents():
    """检查爬取的文档"""
    print("\n检查爬取的文档...")
    
    docs_dir = "tech_docs"
    if not os.path.exists(docs_dir):
        print("❌ 文档目录不存在")
        return False
    
    total_docs = 0
    for filename in os.listdir(docs_dir):
        if filename.endswith('_docs.json'):
            filepath = os.path.join(docs_dir, filename)
            
            import json
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                
                tech_name = filename.replace('_docs.json', '')
                print(f"   {tech_name}: {len(docs)} 个文档片段")
                total_docs += len(docs)
                
            except Exception as e:
                print(f"   读取 {filename} 失败: {e}")
    
    print(f"\n📈 总计: {total_docs} 个文档片段")
    return total_docs > 0

def main():
    """主函数"""
    print("=" * 60)
    print("企业级智能技术助手 - 文档爬取和集成工具")
    print("=" * 60)
    
    start_time = time.time()
    
    # 检查当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"工作目录: {current_dir}")
    
    # 安装依赖
    if not install_requirements():
        print("\n❌ 依赖安装失败，请手动安装: pip install -r requirements.txt")
        return
    
    # 运行爬取器
    if not run_crawler():
        print("\n❌ 文档爬取失败")
        return
    
    # 检查文档
    if not check_documents():
        print("\n❌ 未找到有效文档")
        return
    
    # 运行集成器
    if not run_integrator():
        print("\n⚠️  知识库集成失败，但文档已爬取完成")
    
    # 统计信息
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("文档爬取和集成完成!")
    print(f"总耗时: {duration:.2f} 秒")
    print("\n下一步操作:")
    print("1. 启动Elasticsearch服务（如果尚未启动）")
    print("2. 启动后端服务: cd ../ai-QNA--server && mvn spring-boot:run")
    print("3. 访问前端界面: http://localhost:5175/")
    print("4. 开始使用技术助手进行问答")
    print("=" * 60)

if __name__ == "__main__":
    main()