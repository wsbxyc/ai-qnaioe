#!/usr/bin/env python3
"""
Elasticsearch 索引优化脚本
用于优化索引配置，提升检索速度
"""

import logging
from elasticsearch import Elasticsearch
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndexOptimizer:
    def __init__(self, host='localhost', port=9200, index_name='tech_documents'):
        self.host = host
        self.port = port
        self.index_name = index_name
        self.temp_index = f"{index_name}_optimized"
        self.es_client = None
        self.connect()
    
    def connect(self):
        try:
            self.es_client = Elasticsearch(
                [f"http://{self.host}:{self.port}"],
                verify_certs=False
            )
            if self.es_client.ping():
                logger.info(f"成功连接到Elasticsearch: {self.host}:{self.port}")
            else:
                logger.error("无法连接到Elasticsearch")
        except Exception as e:
            logger.error(f"连接Elasticsearch失败: {e}")
    
    def get_optimized_mappings(self):
        return {
            "properties": {
                "id": {"type": "keyword"},
                "url": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart"
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart"
                },
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
                    "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
                },
                "updatedAt": {
                    "type": "date",
                    "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
                },
                "tags": {"type": "keyword"},
                "summary": {
                    "type": "text",
                    "analyzer": "ik_smart"
                }
            }
        }
    
    def get_optimized_settings(self):
        return {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "60s",
            "index.translog.sync_interval": "5s",
            "index.translog.durability": "async",
            "index.mapping.total_fields.limit": 100,
            "analysis": {
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word"
                    },
                    "ik_smart": {
                        "type": "custom",
                        "tokenizer": "ik_smart"
                    }
                }
            }
        }
    
    def create_optimized_index(self):
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
        
        try:
            if self.es_client.indices.exists(index=self.temp_index):
                self.es_client.indices.delete(index=self.temp_index)
                logger.info(f"已删除旧的优化索引: {self.temp_index}")
            
            index_body = {
                "settings": self.get_optimized_settings(),
                "mappings": self.get_optimized_mappings()
            }
            
            self.es_client.indices.create(index=self.temp_index, body=index_body)
            logger.info(f"优化索引创建成功: {self.temp_index}")
            return True
            
        except Exception as e:
            logger.error(f"创建优化索引失败: {e}")
            return False
    
    def reindex_data(self):
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
        
        try:
            if not self.es_client.indices.exists(index=self.index_name):
                logger.warning(f"原索引不存在: {self.index_name}")
                return False
            
            logger.info("开始重新索引数据...")
            
            reindex_body = {
                "source": {"index": self.index_name},
                "dest": {"index": self.temp_index}
            }
            
            response = self.es_client.reindex(body=reindex_body, wait_for_completion=True, refresh=True)
            logger.info(f"重新索引完成，文档数: {response.get('total', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"重新索引失败: {e}")
            return False
    
    def swap_aliases(self):
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
        
        try:
            alias_actions = []
            
            try:
                aliases_map = self.es_client.indices.get_alias(name=self.index_name)
                is_alias = True
                if aliases_map:
                    for actual_index in aliases_map.keys():
                        alias_actions.append({"remove": {"index": actual_index, "alias": self.index_name}})
                        alias_actions.append({"add": {"index": actual_index, "alias": f"{self.index_name}_old"}})
            except:
                is_alias = False
                if self.es_client.indices.exists(index=self.index_name):
                    alias_actions.append({"remove": {"index": self.index_name, "alias": self.index_name}})
                    alias_actions.append({"add": {"index": self.index_name, "alias": f"{self.index_name}_old"}})
            
            alias_actions.append({"add": {"index": self.temp_index, "alias": self.index_name}})
            
            self.es_client.indices.update_aliases(body={"actions": alias_actions})
            logger.info(f"索引别名切换成功")
            
            return True
            
        except Exception as e:
            logger.error(f"切换别名失败: {e}")
            return False
    
    def optimize(self):
        logger.info("开始索引优化流程")
        
        if not self.create_optimized_index():
            return False
        
        if not self.reindex_data():
            return False
        
        if not self.swap_aliases():
            return False
        
        logger.info("索引优化完成！")
        return True
    
    def analyze_query_performance(self, sample_query="Spring Boot 配置"):
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return
        
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": sample_query,
                        "fields": ["title^2", "content"],
                        "type": "best_fields"
                    }
                },
                "size": 10
            }
            
            response = self.es_client.search(index=self.index_name, body=query, profile=True)
            
            took = response.get('took', 0)
            hits = len(response.get('hits', {}).get('hits', []))
            
            logger.info(f"查询性能分析 - 查询: '{sample_query}'")
            logger.info(f"  耗时: {took}ms")
            logger.info(f"  命中: {hits} 条")
            
            if 'profile' in response:
                shards = response['profile'].get('shards', [])
                if shards:
                    search_time = shards[0].get('search', [])
                    if search_time:
                        logger.info(f"  搜索阶段: {search_time[0].get('time', 'N/A')}")
            
        except Exception as e:
            logger.error(f"查询性能分析失败: {e}")
    
    def force_merge(self, max_num_segments=1):
        if not self.es_client:
            logger.error("未连接到Elasticsearch")
            return False
        
        try:
            logger.info(f"开始强制段合并，最大段数: {max_num_segments}")
            self.es_client.indices.forcemerge(index=self.index_name, max_num_segments=max_num_segments)
            logger.info("强制段合并完成")
            return True
        except Exception as e:
            logger.error(f"强制段合并失败: {e}")
            return False

def main():
    optimizer = IndexOptimizer()
    
    print("\n" + "="*60)
    print("Elasticsearch 索引优化工具")
    print("="*60)
    print("\n请选择操作:")
    print("1. 完整优化流程（推荐）")
    print("2. 仅分析查询性能")
    print("3. 强制段合并")
    print("4. 退出")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        if optimizer.optimize():
            print("\n优化完成！正在进行查询性能测试...")
            optimizer.analyze_query_performance()
            optimizer.force_merge()
    elif choice == "2":
        query = input("请输入测试查询语句 (默认: Spring Boot 配置): ").strip()
        if not query:
            query = "Spring Boot 配置"
        optimizer.analyze_query_performance(query)
    elif choice == "3":
        optimizer.force_merge()
    else:
        print("退出")

if __name__ == "__main__":
    main()
