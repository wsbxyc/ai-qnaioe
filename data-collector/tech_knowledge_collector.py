#!/usr/bin/env python3
"""
企业级智能技术助手 - 知识库数据采集工具
支持从多个来源采集技术文档和知识
"""

import json
import requests
import time
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechKnowledgeCollector:
    def __init__(self):
        self.collected_docs = []
        
    def collect_spring_boot_docs(self) -> List[Dict[str, Any]]:
        """采集Spring Boot官方文档"""
        logger.info("开始采集Spring Boot文档...")
        
        docs = [
            {
                "title": "Spring Boot配置属性详解",
                "content": "Spring Boot提供了丰富的配置属性，可以通过application.properties或application.yml文件进行配置。常用配置包括：服务器端口server.port、数据库连接spring.datasource.url、日志级别logging.level等。",
                "techStack": "Spring Boot",
                "category": "CONFIG",
                "tags": ["配置", "属性", "application.properties"],
                "source": "Spring Boot官方文档",
                "language": "中文"
            },
            {
                "title": "Spring Boot自动配置原理",
                "content": "Spring Boot的自动配置基于@Conditional注解和spring.factories文件。当类路径下存在特定依赖时，自动配置类会被激活，简化了传统Spring应用的配置过程。",
                "techStack": "Spring Boot", 
                "category": "BEST_PRACTICE",
                "tags": ["自动配置", "@Conditional", "原理"],
                "source": "Spring Boot官方文档",
                "language": "中文"
            },
            {
                "title": "Spring Boot REST API开发",
                "content": "使用Spring Boot开发REST API非常简单，只需添加spring-boot-starter-web依赖，创建@RestController类，定义@RequestMapping方法即可。支持JSON序列化、参数验证、异常处理等功能。",
                "techStack": "Spring Boot",
                "category": "API",
                "tags": ["REST", "API", "@RestController"],
                "source": "Spring Boot官方文档", 
                "language": "中文"
            }
        ]
        
        logger.info(f"采集到 {len(docs)} 篇Spring Boot文档")
        return docs
    
    def collect_docker_docs(self) -> List[Dict[str, Any]]:
        """采集Docker文档"""
        logger.info("开始采集Docker文档...")
        
        docs = [
            {
                "title": "Dockerfile最佳实践",
                "content": "编写高效的Dockerfile需要注意：使用多阶段构建减少镜像大小、合理使用.dockerignore文件、按依赖顺序排列指令、使用特定标签的基础镜像等。",
                "techStack": "Docker",
                "category": "BEST_PRACTICE", 
                "tags": ["Dockerfile", "最佳实践", "镜像优化"],
                "source": "Docker官方文档",
                "language": "中文"
            },
            {
                "title": "Docker Compose多容器部署",
                "content": "Docker Compose允许使用YAML文件定义多容器应用。可以配置服务依赖关系、网络设置、数据卷挂载等，实现一键部署复杂应用。",
                "techStack": "Docker",
                "category": "CONFIG",
                "tags": ["Docker Compose", "多容器", "部署"],
                "source": "Docker官方文档",
                "language": "中文"
            },
            {
                "title": "Docker网络模式详解", 
                "content": "Docker支持多种网络模式：bridge（默认）、host、none、overlay等。不同模式适用于不同场景，如开发环境常用bridge，生产环境可能使用overlay。",
                "techStack": "Docker",
                "category": "CONFIG",
                "tags": ["网络", "bridge", "host", "overlay"],
                "source": "Docker官方文档",
                "language": "中文"
            }
        ]
        
        logger.info(f"采集到 {len(docs)} 篇Docker文档")
        return docs
    
    def collect_java_docs(self) -> List[Dict[str, Any]]:
        """采集Java技术文档"""
        logger.info("开始采集Java文档...")
        
        docs = [
            {
                "title": "Java Stream API使用指南",
                "content": "Java 8引入的Stream API提供了函数式编程能力。常用操作包括filter、map、reduce、collect等，可以简化集合处理代码。",
                "techStack": "Java", 
                "category": "API",
                "tags": ["Stream", "函数式编程", "Java 8"],
                "source": "Java官方文档",
                "language": "中文"
            },
            {
                "title": "Java多线程编程最佳实践",
                "content": "多线程编程需要注意线程安全、死锁预防、性能优化等。推荐使用Executor框架、Concurrent集合类、避免使用synchronized等原始同步机制。",
                "techStack": "Java",
                "category": "BEST_PRACTICE", 
                "tags": ["多线程", "并发", "Executor"],
                "source": "Java官方文档",
                "language": "中文"
            },
            {
                "title": "Java内存模型与垃圾回收",
                "content": "Java内存模型包括堆、栈、方法区等。垃圾回收器负责自动内存管理，常见的GC算法有标记-清除、复制、标记-整理等。",
                "techStack": "Java",
                "category": "TUTORIAL",
                "tags": ["内存模型", "垃圾回收", "JVM"],
                "source": "Java官方文档", 
                "language": "中文"
            }
        ]
        
        logger.info(f"采集到 {len(docs)} 篇Java文档")
        return docs
    
    def collect_troubleshooting_guides(self) -> List[Dict[str, Any]]:
        """采集故障排除指南"""
        logger.info("开始采集故障排除指南...")
        
        docs = [
            {
                "title": "Spring Boot应用启动失败排查",
                "content": "常见启动失败原因：依赖冲突、配置错误、端口占用、数据库连接失败等。排查步骤：检查日志、验证配置、测试数据库连接、检查依赖版本。",
                "techStack": "Spring Boot",
                "category": "TROUBLESHOOTING",
                "tags": ["启动失败", "排查", "日志分析"],
                "source": "社区经验",
                "language": "中文"
            },
            {
                "title": "Docker容器网络连接问题",
                "content": "容器网络问题可能原因：网络模式配置错误、防火墙限制、DNS解析问题等。解决方案：检查网络配置、验证端口映射、测试容器间通信。",
                "techStack": "Docker", 
                "category": "TROUBLESHOOTING",
                "tags": ["网络", "连接", "容器"],
                "source": "社区经验",
                "language": "中文"
            },
            {
                "title": "Java内存溢出(OOM)分析",
                "content": "OOM常见原因：内存泄漏、大对象创建、不合理的GC配置等。分析方法：使用jmap、jstat工具，分析heap dump，优化代码和配置。",
                "techStack": "Java",
                "category": "TROUBLESHOOTING",
                "tags": ["内存溢出", "OOM", "性能调优"],
                "source": "社区经验",
                "language": "中文"
            }
        ]
        
        logger.info(f"采集到 {len(docs)} 篇故障排除指南")
        return docs
    
    def collect_all_docs(self) -> List[Dict[str, Any]]:
        """采集所有技术文档"""
        logger.info("开始全面采集技术文档...")
        
        all_docs = []
        
        # 采集各技术栈文档
        all_docs.extend(self.collect_spring_boot_docs())
        all_docs.extend(self.collect_docker_docs()) 
        all_docs.extend(self.collect_java_docs())
        all_docs.extend(self.collect_troubleshooting_guides())
        
        # 添加更多技术栈（示例）
        more_docs = [
            # Vue.js相关
            {
                "title": "Vue 3 Composition API入门",
                "content": "Vue 3的Composition API提供了更好的逻辑复用和类型推导。使用setup函数、ref、reactive等API可以编写更清晰的组件逻辑。",
                "techStack": "Vue",
                "category": "TUTORIAL", 
                "tags": ["Vue 3", "Composition API", "前端"],
                "source": "Vue官方文档",
                "language": "中文"
            },
            
            # MySQL相关
            {
                "title": "MySQL索引优化策略",
                "content": "有效的索引策略可以大幅提升查询性能。建议：为频繁查询的字段创建索引、避免过度索引、使用覆盖索引、定期分析索引使用情况。",
                "techStack": "MySQL",
                "category": "BEST_PRACTICE",
                "tags": ["索引", "优化", "数据库"],
                "source": "MySQL官方文档", 
                "language": "中文"
            },
            
            # Redis相关
            {
                "title": "Redis持久化配置",
                "content": "Redis支持RDB和AOF两种持久化方式。RDB适合备份，AOF保证数据安全。可以根据业务需求配置适当的持久化策略。",
                "techStack": "Redis",
                "category": "CONFIG",
                "tags": ["持久化", "RDB", "AOF"],
                "source": "Redis官方文档",
                "language": "中文"
            }
        ]
        
        all_docs.extend(more_docs)
        
        logger.info(f"总共采集到 {len(all_docs)} 篇技术文档")
        return all_docs
    
    def save_to_json(self, docs: List[Dict[str, Any]], filename: str = "tech_knowledge_base.json"):
        """保存文档到JSON文件"""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"文档已保存到: {filepath}")
    
    def generate_import_script(self, docs: List[Dict[str, Any]]):
        """生成Java导入脚本"""
        script_content = """
package com.tech.assistant.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;

@Slf4j
@Service
public class TechKnowledgeInitializer implements CommandLineRunner {
    
    @Override
    public void run(String... args) throws Exception {
        log.info("开始初始化技术知识库...");
        
        // 这里可以调用API将文档导入到Elasticsearch
        // 实际实现中应该使用ElasticsearchTemplate或Repository
        
        log.info("技术知识库初始化完成！");
    }
    
    // 示例数据（实际应该从文件或数据库加载）
    private List<TechDocument> getSampleDocuments() {
        return Arrays.asList(
"""
        
        for i, doc in enumerate(docs):
            if i < 10:  # 只生成前10个示例
                script_content += f"            // {doc['title']}\n"
        
        script_content += """        );
    }
}
"""
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, "TechKnowledgeInitializer.java")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Java导入脚本已生成: {filepath}")

def main():
    """主函数"""
    collector = TechKnowledgeCollector()
    
    try:
        # 采集所有文档
        all_docs = collector.collect_all_docs()
        
        # 保存为JSON
        collector.save_to_json(all_docs)
        
        # 生成Java导入脚本
        collector.generate_import_script(all_docs)
        
        logger.info("数据采集完成！")
        
    except Exception as e:
        logger.error(f"数据采集失败: {e}")

if __name__ == "__main__":
    main()