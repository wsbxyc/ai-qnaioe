#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版Elasticsearch集成工具 - 专门为智能技术助手设计
"""

import json
import time
from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ElasticsearchOptimizedIntegrator:
    """优化版Elasticsearch集成工具"""
    
    def __init__(self, hosts: List[str] = None, index_name: str = "tech_documents"):
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_name = index_name
        self.es_client = None
        
    def connect(self) -> bool:
        """连接Elasticsearch"""
        try:
            self.es_client = Elasticsearch(["http://localhost:9200"])
            
            if self.es_client.ping():
                logger.info("Elasticsearch连接成功")
                return True
            else:
                logger.error("Elasticsearch连接失败")
                return False
                
        except Exception as e:
            logger.error(f"连接Elasticsearch失败: {e}")
            return False
    
    def create_optimized_index(self) -> bool:
        """创建优化版索引映射"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return False
        
        # 删除已存在的索引
        if self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.delete(index=self.index_name)
            logger.info(f"已删除旧索引: {self.index_name}")
        
        # 优化版索引映射
        index_mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_smart_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_smart",
                            "filter": ["lowercase"]
                        },
                        "ik_max_analyzer": {
                            "type": "custom", 
                            "tokenizer": "ik_max_word",
                            "filter": ["lowercase"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_smart_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "standard": {"type": "text", "analyzer": "standard"}
                        }
                    },
                    "tech_stack": {
                        "type": "keyword",
                        "fields": {
                            "text": {"type": "text", "analyzer": "ik_smart_analyzer"}
                        }
                    },
                    "theme": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "quality_score": {"type": "float"},
                    "relevance_score": {"type": "float"},
                    "chunk_index": {"type": "integer"},
                    "total_chunks": {"type": "integer"},
                    "depth": {"type": "integer"},
                    "created_at": {
                        "type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
                    },
                    "updated_at": {
                        "type": "date", 
                        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
                    },
                    "optimized": {"type": "boolean"},
                    "tags": {"type": "keyword"}
                }
            }
        }
        
        try:
            self.es_client.indices.create(
                index=self.index_name,
                body=index_mapping
            )
            logger.info(f"优化版索引创建成功: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def enhance_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """增强文档数据"""
        enhanced_doc = document.copy()
        
        # 添加时间戳
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        enhanced_doc['created_at'] = current_time
        enhanced_doc['updated_at'] = current_time
        
        # 生成标签
        tags = self.generate_tags(document)
        enhanced_doc['tags'] = tags
        
        # 确保必要字段存在
        enhanced_doc.setdefault('quality_score', 0.5)
        enhanced_doc.setdefault('relevance_score', 0.5)
        enhanced_doc.setdefault('optimized', True)
        
        return enhanced_doc
    
    def generate_tags(self, document: Dict[str, Any]) -> List[str]:
        """生成文档标签"""
        tags = []
        
        # 技术栈标签
        tech_stack = document.get('tech_stack', '')
        if tech_stack:
            tags.append(f"tech:{tech_stack}")
        
        # 主题标签
        theme = document.get('theme', '')
        if theme:
            tags.append(f"theme:{theme}")
        
        # 类别标签
        category = document.get('category', '')
        if category:
            tags.append(f"category:{category}")
        
        # 质量标签
        quality_score = document.get('quality_score', 0)
        if quality_score >= 0.8:
            tags.append("quality:excellent")
        elif quality_score >= 0.6:
            tags.append("quality:good")
        elif quality_score >= 0.4:
            tags.append("quality:fair")
        else:
            tags.append("quality:poor")
        
        # 相关性标签
        relevance_score = document.get('relevance_score', 0)
        if relevance_score >= 0.8:
            tags.append("relevance:high")
        elif relevance_score >= 0.6:
            tags.append("relevance:medium")
        else:
            tags.append("relevance:low")
        
        return tags
    
    def index_documents_batch(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """批量索引文档"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return {"success": False, "error": "客户端未连接"}
        
        total_docs = len(documents)
        logger.info(f"开始批量索引 {total_docs} 个文档")
        
        success_count = 0
        error_count = 0
        
        # 分批处理
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            actions = []
            
            for doc in batch:
                # 增强文档数据
                enhanced_doc = self.enhance_document(doc)
                
                # 准备批量操作
                action = {
                    "_index": self.index_name,
                    "_id": enhanced_doc['id'],
                    "_source": enhanced_doc
                }
                actions.append(action)
            
            try:
                # 批量索引
                success, errors = bulk(self.es_client, actions, stats_only=True)
                success_count += success
                
                if errors:
                    error_count += len(errors)
                    logger.warning(f"批次 {i//batch_size + 1} 有 {len(errors)} 个错误")
                
                logger.info(f"批次 {i//batch_size + 1} 完成: {success} 成功, {len(errors) if errors else 0} 失败")
                
            except Exception as e:
                error_count += len(batch)
                logger.error(f"批次 {i//batch_size + 1} 失败: {e}")
        
        # 刷新索引
        self.es_client.indices.refresh(index=self.index_name)
        
        # 统计信息
        stats = self.es_client.count(index=self.index_name)
        indexed_count = stats['count']
        
        result = {
            "success": True,
            "total_documents": total_docs,
            "indexed_count": indexed_count,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_count / total_docs * 100, 2) if total_docs > 0 else 0
        }
        
        logger.info(f"批量索引完成: {result}")
        return result
    
    def load_optimized_documents(self, tech_stack: str) -> List[Dict[str, Any]]:
        """加载优化后的文档"""
        file_path = f"chinese_tech_docs/{tech_stack}_chinese_docs_optimized.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"加载 {tech_stack} 优化文档: {len(documents)} 个")
            return documents
            
        except Exception as e:
            logger.error(f"加载文档失败 {file_path}: {e}")
            return []
    
    def integrate_tech_stack(self, tech_stack: str) -> Dict[str, Any]:
        """集成特定技术栈的文档"""
        logger.info(f"开始集成 {tech_stack} 文档到Elasticsearch")
        
        # 加载文档
        documents = self.load_optimized_documents(tech_stack)
        if not documents:
            return {"success": False, "error": f"无法加载 {tech_stack} 文档"}
        
        # 索引文档
        result = self.index_documents_batch(documents)
        result['tech_stack'] = tech_stack
        
        return result
    
    def run_full_integration(self) -> Dict[str, Any]:
        """运行完整的集成流程"""
        logger.info("开始完整的Elasticsearch集成流程")
        
        # 连接Elasticsearch
        if not self.connect():
            return {"success": False, "error": "Elasticsearch连接失败"}
        
        # 创建索引
        if not self.create_optimized_index():
            return {"success": False, "error": "索引创建失败"}
        
        # 集成所有技术栈
        tech_stacks = ['spring-boot', 'docker', 'python', 'vue']
        integration_results = {}
        
        for tech_stack in tech_stacks:
            result = self.integrate_tech_stack(tech_stack)
            integration_results[tech_stack] = result
        
        # 生成总体报告
        overall_report = self.generate_integration_report(integration_results)
        
        # 保存报告
        with open("es_integration_report.json", 'w', encoding='utf-8') as f:
            json.dump({
                "integration_results": integration_results,
                "overall_report": overall_report
            }, f, ensure_ascii=False, indent=2)
        
        logger.info("完整的Elasticsearch集成流程完成")
        return {
            "success": True,
            "integration_results": integration_results,
            "overall_report": overall_report
        }
    
    def generate_integration_report(self, integration_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成集成报告"""
        total_documents = 0
        total_indexed = 0
        total_success = 0
        total_errors = 0
        
        successful_integrations = 0
        
        for tech_stack, result in integration_results.items():
            if result.get('success', False):
                total_documents += result.get('total_documents', 0)
                total_indexed += result.get('indexed_count', 0)
                total_success += result.get('success_count', 0)
                total_errors += result.get('error_count', 0)
                successful_integrations += 1
        
        return {
            "total_tech_stacks": len(integration_results),
            "successful_integrations": successful_integrations,
            "total_documents": total_documents,
            "total_indexed": total_indexed,
            "total_success": total_success,
            "total_errors": total_errors,
            "overall_success_rate": round(total_success / total_documents * 100, 2) if total_documents > 0 else 0,
            "indexing_efficiency": round(total_indexed / total_documents * 100, 2) if total_documents > 0 else 0
        }
    
    def test_search_performance(self, sample_queries: List[str] = None) -> Dict[str, Any]:
        """测试搜索性能"""
        if not self.es_client:
            return {"error": "Elasticsearch客户端未连接"}
        
        if sample_queries is None:
            sample_queries = [
                "Spring Boot配置",
                "Docker网络",
                "Python装饰器",
                "Vue路由"
            ]
        
        performance_results = {}
        
        for query in sample_queries:
            start_time = time.time()
            
            try:
                search_body = {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "content", "tech_stack"],
                            "type": "best_fields"
                        }
                    },
                    "size": 10,
                    "sort": [
                        {"_score": {"order": "desc"}},
                        {"quality_score": {"order": "desc"}},
                        {"relevance_score": {"order": "desc"}}
                    ]
                }
                
                result = self.es_client.search(
                    index=self.index_name,
                    body=search_body
                )
                
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)  # 毫秒
                
                performance_results[query] = {
                    "response_time_ms": response_time,
                    "hits_count": result['hits']['total']['value'],
                    "max_score": result['hits']['max_score'] if result['hits']['hits'] else 0
                }
                
                logger.info(f"查询 '{query}' 响应时间: {response_time}ms, 命中: {result['hits']['total']['value']}")
                
            except Exception as e:
                performance_results[query] = {"error": str(e)}
                logger.error(f"查询 '{query}' 失败: {e}")
        
        return performance_results

def main():
    """主函数"""
    integrator = ElasticsearchOptimizedIntegrator()
    
    print("=" * 70)
    print("优化版Elasticsearch集成工具")
    print("=" * 70)
    
    print("\n集成特性:")
    print("- 智能索引映射优化")
    print("- 中文分词器支持 (IK Analyzer)")
    print("- 多维度标签系统")
    print("- 批量处理性能优化")
    print("- 搜索性能测试")
    
    print("\n开始集成流程...")
    
    try:
        # 运行完整集成
        result = integrator.run_full_integration()
        
        if result.get('success', False):
            print("\n" + "=" * 70)
            print("Elasticsearch集成完成!")
            print("=" * 70)
            
            # 显示集成结果
            overall_report = result.get('overall_report', {})
            print(f"总体集成统计:")
            print(f"- 技术栈数量: {overall_report.get('total_tech_stacks', 0)}")
            print(f"- 成功集成: {overall_report.get('successful_integrations', 0)}")
            print(f"- 总文档数: {overall_report.get('total_documents', 0)}")
            print(f"- 索引成功: {overall_report.get('total_indexed', 0)}")
            print(f"- 总体成功率: {overall_report.get('overall_success_rate', 0)}%")
            
            # 测试搜索性能
            print(f"\n搜索性能测试:")
            performance_results = integrator.test_search_performance()
            
            for query, perf in performance_results.items():
                if 'error' not in perf:
                    print(f"- '{query}': {perf['response_time_ms']}ms, 命中 {perf['hits_count']} 个文档")
            
            print("\n下一步操作:")
            print("1. 启动后端服务测试检索功能")
            print("2. 在前端界面验证搜索性能")
            print("3. 查看详细报告: es_integration_report.json")
            
        else:
            print(f"\n[ERROR] 集成失败: {result.get('error', '未知错误')}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 集成流程失败: {e}")
        print("=" * 70)

if __name__ == "__main__":
    main()