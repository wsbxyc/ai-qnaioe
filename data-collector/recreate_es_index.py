#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新创建Elasticsearch索引以修复日期格式问题
"""

import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESIndexReconstructor:
    """Elasticsearch索引重建器"""
    
    def __init__(self, hosts: list = None, old_index: str = "tech_documents", new_index: str = "tech_documents_fixed"):
        self.hosts = hosts or ["http://localhost:9200"]
        self.old_index = old_index
        self.new_index = new_index
        self.es_client = None
        
    def connect(self) -> bool:
        """连接Elasticsearch"""
        try:
            self.es_client = Elasticsearch(self.hosts)
            if self.es_client.ping():
                logger.info("Elasticsearch连接成功")
                return True
            else:
                logger.error("Elasticsearch连接失败")
                return False
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def create_new_index(self) -> bool:
        """创建新索引"""
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
            
        try:
            # 删除已存在的新索引
            if self.es_client.indices.exists(index=self.new_index):
                self.es_client.indices.delete(index=self.new_index)
                logger.info(f"已删除旧的新索引: {self.new_index}")
            
            # 创建新索引
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "url": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "ik_smart"},
                        "content": {"type": "text", "analyzer": "ik_smart"},
                        "techStack": {"type": "keyword"},
                        "theme": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "qualityScore": {"type": "float"},
                        "relevanceScore": {"type": "float"},
                        "chunkIndex": {"type": "integer"},
                        "totalChunks": {"type": "integer"},
                        "depth": {"type": "integer"},
                        "createdAt": {
                            "type": "date",
                            "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
                        },
                        "updatedAt": {
                            "type": "date",
                            "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
                        }
                    }
                }
            }
            
            self.es_client.indices.create(index=self.new_index, body=index_body)
            logger.info(f"新索引创建成功: {self.new_index}")
            return True
            
        except Exception as e:
            logger.error(f"创建新索引失败: {e}")
            return False
    
    def copy_documents(self) -> bool:
        """复制文档到新索引"""
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
            
        try:
            # 搜索所有文档
            search_body = {
                "query": {
                    "match_all": {}
                },
                "size": 1000
            }
            
            result = self.es_client.search(index=self.old_index, body=search_body)
            
            actions = []
            
            for hit in result['hits']['hits']:
                doc = hit['_source']
                doc_id = hit['_id']
                
                # 修复日期格式
                if 'createdAt' in doc and isinstance(doc['createdAt'], str):
                    if len(doc['createdAt']) == 10:  # yyyy-MM-dd
                        doc['createdAt'] += 'T00:00:00.000Z'
                
                if 'updatedAt' in doc and isinstance(doc['updatedAt'], str):
                    if len(doc['updatedAt']) == 10:  # yyyy-MM-dd
                        doc['updatedAt'] += 'T00:00:00.000Z'
                
                # 准备批量操作
                action = {
                    "_index": self.new_index,
                    "_id": doc_id,
                    "_source": doc
                }
                actions.append(action)
            
            # 批量索引
            if actions:
                success, errors = bulk(self.es_client, actions, stats_only=True)
                logger.info(f"复制文档完成: {success} 成功, {len(errors) if errors else 0} 失败")
            
            return True
            
        except Exception as e:
            logger.error(f"复制文档失败: {e}")
            return False
    
    def swap_indices(self) -> bool:
        """交换索引"""
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
            
        try:
            # 删除旧索引
            if self.es_client.indices.exists(index=self.old_index):
                self.es_client.indices.delete(index=self.old_index)
                logger.info(f"已删除旧索引: {self.old_index}")
            
            # 重命名新索引
            self.es_client.indices.put_alias(index=self.new_index, name=self.old_index)
            logger.info(f"索引交换完成: {self.new_index} -> {self.old_index}")
            
            return True
            
        except Exception as e:
            logger.error(f"交换索引失败: {e}")
            return False

def main():
    """主函数"""
    reconstructor = ESIndexReconstructor()
    
    print("=" * 70)
    print("Elasticsearch索引重建工具")
    print("=" * 70)
    
    print("\n问题描述:")
    print("- 日期格式不兼容: '2026-04-11' 无法转换为 LocalDateTime")
    print("- 需要重新创建索引并修复日期格式")
    
    print("\n开始重建流程...")
    
    if reconstructor.connect():
        # 创建新索引
        if reconstructor.create_new_index():
            # 复制文档
            if reconstructor.copy_documents():
                # 交换索引
                reconstructor.swap_indices()
                print("\n索引重建完成!")
            else:
                print("\n文档复制失败")
        else:
            print("\n新索引创建失败")
    else:
        print("\nElasticsearch连接失败")
    
    print("=" * 70)

if __name__ == "__main__":
    main()