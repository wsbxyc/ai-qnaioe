#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新Elasticsearch索引映射以修复日期格式问题
"""

import json
from elasticsearch import Elasticsearch
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESIndexUpdater:
    """Elasticsearch索引更新器"""
    
    def __init__(self, hosts: list = None, index_name: str = "tech_documents"):
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_name = index_name
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
    
    def update_index_mapping(self) -> bool:
        """更新索引映射"""
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
            
        try:
            # 更新日期字段映射
            update_body = {
                "properties": {
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
            
            # 更新映射
            self.es_client.indices.put_mapping(
                index=self.index_name,
                body=update_body
            )
            
            logger.info("索引映射更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新索引映射失败: {e}")
            return False
    
    def update_documents_dates(self) -> bool:
        """更新文档日期格式"""
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
            
            result = self.es_client.search(index=self.index_name, body=search_body)
            
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
                
                # 更新文档
                self.es_client.index(
                    index=self.index_name,
                    id=doc_id,
                    body=doc
                )
            
            logger.info("文档日期格式更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新文档日期失败: {e}")
            return False

def main():
    """主函数"""
    updater = ESIndexUpdater()
    
    print("=" * 70)
    print("Elasticsearch索引更新工具")
    print("=" * 70)
    
    print("\n问题描述:")
    print("- 日期格式不兼容: '2026-04-11' 无法转换为 LocalDateTime")
    print("- 需要更新索引映射和文档日期格式")
    
    print("\n开始更新流程...")
    
    if updater.connect():
        # 更新索引映射
        if updater.update_index_mapping():
            # 更新文档日期
            updater.update_documents_dates()
            print("\n索引更新完成!")
        else:
            print("\n索引映射更新失败")
    else:
        print("\nElasticsearch连接失败")
    
    print("=" * 70)

if __name__ == "__main__":
    main()