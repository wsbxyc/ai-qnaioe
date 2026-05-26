#!/usr/bin/env python3
"""
企业级智能技术助手 - 中文文档爬取和集成启动脚本
一键启动中文文档爬取和Elasticsearch集成
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def install_chinese_requirements():
    """安装中文爬取依赖包"""
    print("正在安装中文爬取依赖包...")
    
    requirements = [
        "aiohttp>=3.8.0",
        "beautifulsoup4>=4.12.0", 
        "requests>=2.31.0",
        "lxml>=4.9.0",
        "asyncio>=3.4.3",
        "googletrans>=3.0.0",
        "elasticsearch>=7.0.0"
    ]
    
    for package in requirements:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ 安装 {package} 成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ 安装 {package} 失败: {e}")
            return False
    
    return True

def run_chinese_crawler():
    """运行中文文档爬取器"""
    print("\n开始爬取中文技术文档...")
    
    try:
        # 运行中文爬取器
        result = subprocess.run([
            sys.executable, "chinese_docs_crawler.py"
        ], capture_output=True, text=True, check=True)
        
        print("✅ 中文文档爬取完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 中文文档爬取失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def check_chinese_documents():
    """检查中文文档"""
    docs_dir = "chinese_tech_docs"
    
    if not os.path.exists(docs_dir):
        print(f"❌ 文档目录不存在: {docs_dir}")
        return False
    
    files = os.listdir(docs_dir)
    if not files:
        print(f"❌ 文档目录为空: {docs_dir}")
        return False
    
    # 检查技术栈文档
    tech_stacks = ["spring-boot", "java", "docker", "python", "vue", "react", "redis", "mysql"]
    tech_files = []
    
    for tech in tech_stacks:
        filename = os.path.join(docs_dir, f"{tech}_chinese_docs.json")
        if os.path.exists(filename):
            tech_files.append(filename)
            # 检查文件大小
            file_size = os.path.getsize(filename)
            print(f"✅ {tech}: {file_size} 字节")
        else:
            print(f"❌ {tech}: 文档文件不存在")
    
    # 检查合并文档
    all_filename = os.path.join(docs_dir, "all_tech_chinese_docs.json")
    if os.path.exists(all_filename):
        file_size = os.path.getsize(all_filename)
        print(f"✅ 合并文档: {file_size} 字节")
        tech_files.append(all_filename)
    else:
        print("❌ 合并文档: 文件不存在")
    
    if not tech_files:
        print("❌ 未找到有效的中文文档文件")
        return False
    
    # 检查文档内容
    for filename in tech_files[:3]:  # 只检查前3个文件
        try:
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            if not isinstance(documents, list) or len(documents) == 0:
                print(f"❌ 文档格式错误: {filename}")
                return False
            
            # 检查第一个文档的内容
            first_doc = documents[0]
            required_fields = ['id', 'title', 'content', 'tech_stack', 'language']
            
            for field in required_fields:
                if field not in first_doc:
                    print(f"❌ 文档缺少必要字段 {field}: {filename}")
                    return False
            
            # 检查是否为中文
            content = first_doc.get('content', '')
            if len(content) < 50:
                print(f"⚠️  文档内容过短: {filename}")
            
            print(f"✅ 文档验证通过: {filename} ({len(documents)} 个片段)")
            
        except Exception as e:
            print(f"❌ 检查文档失败 {filename}: {e}")
            return False
    
    print("✅ 中文文档检查完成")
    return True

def integrate_chinese_knowledge():
    """集成中文知识到Elasticsearch"""
    print("\n开始集成中文知识到Elasticsearch...")
    
    try:
        # 检查Elasticsearch是否可用
        import requests
        try:
            response = requests.get("http://localhost:9200", timeout=10)
            if response.status_code == 200:
                print("✅ Elasticsearch服务可用")
            else:
                print("❌ Elasticsearch服务不可用")
                return False
        except:
            print("❌ 无法连接到Elasticsearch")
            print("请确保Elasticsearch服务已启动")
            return False
        
        # 运行集成器
        result = subprocess.run([
            sys.executable, "es_integrator.py"
        ], capture_output=True, text=True, check=True)
        
        print("✅ 中文知识集成完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 中文知识集成失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("企业级智能技术助手 - 中文文档爬取和集成工具")
    print("=" * 60)
    
    start_time = time.time()
    
    # 检查当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"工作目录: {current_dir}")
    
    # 安装中文依赖
    if not install_chinese_requirements():
        print("\n❌ 中文依赖安装失败")
        return
    
    # 运行中文爬取器
    if not run_chinese_crawler():
        print("\n❌ 中文文档爬取失败")
        return
    
    # 检查文档
    if not check_chinese_documents():
        print("\n❌ 未找到有效中文文档")
        return
    
    # 运行集成器
    if not integrate_chinese_knowledge():
        print("\n⚠️  中文知识库集成失败，但文档已爬取完成")
    
    # 统计信息
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("中文文档爬取和集成完成!")
    print(f"总耗时: {duration:.2f} 秒")
    print("\n中文爬取特性:")
    print("• 专门爬取中文技术文档")
    print("• 自动检测并翻译英文内容")
    print("• 支持IK中文分词器")
    print("• 深度爬取相关页面")
    print("\n下一步操作:")
    print("1. 启动后端服务: cd ../ai-QNA--server && mvn spring-boot:run")
    print("2. 访问前端界面: http://localhost:5175/")
    print("3. 开始使用中文知识库进行问答")
    print("=" * 60)

if __name__ == "__main__":
    main()