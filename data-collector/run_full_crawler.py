#!/usr/bin/env python3
"""
企业级智能技术助手 - 完整文档爬取启动脚本
一键启动完整文档爬取（所有页面）
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def install_full_requirements():
    """安装完整爬取所需的依赖包"""
    print("正在安装完整爬取依赖包...")
    
    # 完整爬取需要额外的依赖
    full_requirements = [
        "aiohttp>=3.8.0",
        "beautifulsoup4>=4.12.0", 
        "requests>=2.31.0",
        "lxml>=4.9.0",
        "asyncio>=3.4.3"
    ]
    
    try:
        for package in full_requirements:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 安装 {package} 成功")
            else:
                print(f"❌ 安装 {package} 失败: {result.stderr}")
                return False
                
        return True
            
    except Exception as e:
        print(f"❌ 安装依赖包时出错: {e}")
        return False

def run_full_crawler():
    """运行完整文档爬取器"""
    print("\n开始完整爬取技术文档（所有页面）...")
    
    try:
        # 运行完整爬取器
        result = subprocess.run([
            sys.executable, "full_docs_crawler.py", 
            "--output-dir", "full_tech_docs"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 完整文档爬取完成")
            print(result.stdout)
            return True
        else:
            print(f"❌ 完整文档爬取失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行完整爬取器时出错: {e}")
        return False

def check_full_documents():
    """检查完整爬取的文档"""
    print("\n检查完整爬取的文档...")
    
    docs_dir = "full_tech_docs"
    if not os.path.exists(docs_dir):
        print("❌ 完整文档目录不存在")
        return False
    
    total_docs = 0
    for filename in os.listdir(docs_dir):
        if filename.endswith('_full_docs.json'):
            filepath = os.path.join(docs_dir, filename)
            
            import json
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                
                tech_name = filename.replace('_full_docs.json', '')
                print(f"   {tech_name}: {len(docs)} 个完整文档片段")
                total_docs += len(docs)
                
            except Exception as e:
                print(f"   读取 {filename} 失败: {e}")
    
    # 检查合并的文档文件
    all_filepath = os.path.join(docs_dir, "all_tech_full_docs.json")
    if os.path.exists(all_filepath):
        try:
            with open(all_filepath, 'r', encoding='utf-8') as f:
                docs = json.load(f)
            
            print(f"   合并文件: {len(docs)} 个文档片段")
            total_docs += len(docs)
            
        except Exception as e:
            print(f"   读取合并文件失败: {e}")
    
    print(f"\n总计: {total_docs} 个完整文档片段")
    return total_docs > 0

def integrate_full_knowledge():
    """集成完整知识库"""
    print("\n开始集成完整知识库到Elasticsearch...")
    
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
        
        # 运行集成器，指定完整文档目录
        result = subprocess.run([
            sys.executable, "knowledge_integrator.py",
            "--docs-dir", "full_tech_docs",
            "--es-host", "localhost", 
            "--es-port", "9200"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 完整知识库集成完成")
            print(result.stdout)
            return True
        else:
            print(f"❌ 完整知识库集成失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 运行集成器时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("企业级智能技术助手 - 完整文档爬取工具")
    print("=" * 60)
    
    start_time = time.time()
    
    # 检查当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"工作目录: {current_dir}")
    
    # 安装完整依赖
    if not install_full_requirements():
        print("\n❌ 完整依赖安装失败")
        return
    
    # 运行完整爬取器
    if not run_full_crawler():
        print("\n❌ 完整文档爬取失败")
        return
    
    # 检查文档
    if not check_full_documents():
        print("\n❌ 未找到完整有效文档")
        return
    
    # 运行集成器
    if not integrate_full_knowledge():
        print("\n⚠️  完整知识库集成失败，但文档已爬取完成")
    
    # 统计信息
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("完整文档爬取和集成完成!")
    print(f"总耗时: {duration:.2f} 秒")
    print("\n完整爬取特性:")
    print("• 深度爬取所有相关页面")
    print("• 包含完整的目录结构")
    print("• 最大爬取深度: 10层")
    print("• 每个技术栈最多: 500页面")
    print("\n下一步操作:")
    print("1. 启动后端服务: cd ../ai-QNA--server && mvn spring-boot:run")
    print("2. 访问前端界面: http://localhost:5175/")
    print("3. 开始使用完整知识库进行问答")
    print("=" * 60)

if __name__ == "__main__":
    main()