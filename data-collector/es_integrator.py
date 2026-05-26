#!/usr/bin/env python3
"""
企业级智能技术助手 - Elasticsearch集成器
将中文文档存储到Elasticsearch中
"""

import json
import os
import logging
from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESIntegrator:
    """Elasticsearch集成器"""
    
    def __init__(self, es_host: str = "localhost", es_port: int = 9200):
        self.es_host = es_host
        self.es_port = es_port
        self.es_client = None
        # 与 Java 实体 @Document(indexName = "tech_documents") 对齐
        self.index_name = "tech_documents"
        
    def connect_to_es(self) -> bool:
        """连接到Elasticsearch"""
        try:
            self.es_client = Elasticsearch(
                f"http://{self.es_host}:{self.es_port}"
            )
            
            if self.es_client.ping():
                logger.info(f"成功连接到Elasticsearch: {self.es_host}:{self.es_port}")
                return True
            else:
                logger.error("无法连接到Elasticsearch")
                return False
                
        except Exception as e:
            logger.error(f"连接Elasticsearch失败: {e}")
            return False
    
    def create_index(self) -> bool:
        """创建索引"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return False
        
        # 与 Spring Data Elasticsearch 实体 TechDocument 字段对齐（camelCase）
        mapping = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 0,
                "max_result_window": 50000,
                "analysis": {
                    "analyzer": {
                        "tech_text": {"type": "standard"}
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "tech_text", "search_analyzer": "tech_text"},
                    "content": {"type": "text", "analyzer": "tech_text", "search_analyzer": "tech_text"},
                    "bm25Content": {"type": "text", "analyzer": "tech_text", "search_analyzer": "tech_text"},
                    "summary": {"type": "keyword"},
                    "techStack": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "embedding": {"type": "dense_vector", "dims": 1024},
                    "source": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "createdAt": {"type": "date"},
                    "updatedAt": {"type": "date"},
                    "popularity": {"type": "integer"},
                    "qualityScore": {"type": "double"},
                    "retrievalWeight": {"type": "double"},
                    "url": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "total_chunks": {"type": "integer"},
                    "depth": {"type": "integer"},
                    "timestamp": {"type": "date"}
                }
            }
        }
        
        try:
            # 检查索引是否存在
            if self.es_client.indices.exists(index=self.index_name):
                logger.info(f"索引 {self.index_name} 已存在，跳过创建")
                return True
            
            # 创建索引
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"成功创建索引: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def enhance_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """转换为后端 Java 实体兼容结构（camelCase）"""
        import time

        title = doc.get("title") or ""
        content = doc.get("content") or ""
        tech = doc.get("techStack") or doc.get("tech_stack") or ""
        cat = doc.get("category") or ""
        doc_id = doc.get("id") or doc.get("_id") or doc.get("url")

        enhanced_doc: Dict[str, Any] = {
            "id": str(doc_id) if doc_id is not None else str(hash(title + content))[:16],
            "title": title,
            "content": content,
            "bm25Content": doc.get("bm25Content") or content,
            "summary": (doc.get("summary") or title[:200])[:512],
            "techStack": tech,
            "category": cat or "TUTORIAL",
            "tags": doc.get("tags") if isinstance(doc.get("tags"), list) else [],
            "source": doc.get("source") or "crawler",
            "language": doc.get("language") or "中文",
            "popularity": int(doc.get("popularity") or 50),
            "qualityScore": float(doc.get("qualityScore") or 0.8),
            "retrievalWeight": float(doc.get("retrievalWeight") or 1.0),
            "timestamp": int(time.time() * 1000),
        }
        if doc.get("embedding") is not None:
            enhanced_doc["embedding"] = doc["embedding"]
        if doc.get("createdAt"):
            enhanced_doc["createdAt"] = doc["createdAt"]
        if doc.get("updatedAt"):
            enhanced_doc["updatedAt"] = doc["updatedAt"]
        return enhanced_doc
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """将文档索引到Elasticsearch"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return False
        
        actions = []
        
        for doc in documents:
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
            # 批量索引文档
            success, failed = bulk(self.es_client, actions, stats_only=True)
            
            logger.info(f"成功索引 {success} 个文档")
            if failed:
                logger.warning(f"索引失败 {failed} 个文档")
            
            # 刷新索引
            self.es_client.indices.refresh(index=self.index_name)
            
            # 检查索引统计
            stats = self.es_client.count(index=self.index_name)
            logger.info(f"索引当前包含 {stats['count']} 个文档")
            
            return True
            
        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return False
    
    def load_documents_from_dir(self, docs_dir: str) -> List[Dict[str, Any]]:
        """从目录加载文档"""
        all_documents = []
        
        if not os.path.exists(docs_dir):
            logger.error(f"文档目录不存在: {docs_dir}")
            return all_documents
        
        # 加载单个技术栈文档
        tech_stacks = ["spring-boot", "java", "docker", "python", "vue", "react", "redis", "mysql"]
        
        for tech in tech_stacks:
            filename = os.path.join(docs_dir, f"{tech}_chinese_docs.json")
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        documents = json.load(f)
                    all_documents.extend(documents)
                    logger.info(f"加载 {tech} 文档: {len(documents)} 个片段")
                except Exception as e:
                    logger.error(f"加载文档失败 {filename}: {e}")
        
        # 加载合并文档
        all_filename = os.path.join(docs_dir, "all_tech_chinese_docs.json")
        if os.path.exists(all_filename):
            try:
                with open(all_filename, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                all_documents.extend(documents)
                logger.info(f"加载合并文档: {len(documents)} 个片段")
            except Exception as e:
                logger.error(f"加载合并文档失败 {all_filename}: {e}")
        
        # 去重
        seen_ids = set()
        unique_documents = []
        
        for doc in all_documents:
            if doc['id'] not in seen_ids:
                seen_ids.add(doc['id'])
                unique_documents.append(doc)
        
        logger.info(f"去重后总文档数: {len(unique_documents)}")
        return unique_documents
    
    def integrate_documents(self, docs_dir: str) -> bool:
        """集成文档到Elasticsearch"""
        # 连接Elasticsearch
        if not self.connect_to_es():
            return False
        
        # 创建索引
        if not self.create_index():
            return False
        
        # 加载文档
        documents = self.load_documents_from_dir(docs_dir)
        if not documents:
            logger.error("没有找到可索引的文档")
            return False
        
        # 索引文档
        if not self.index_documents(documents):
            return False
        
        logger.info("文档集成完成!")
        return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Elasticsearch集成器')
    parser.add_argument('--docs-dir', type=str, default='chinese_tech_docs', help='文档目录')
    parser.add_argument('--es-host', type=str, default='localhost', help='Elasticsearch主机')
    parser.add_argument('--es-port', type=int, default=9200, help='Elasticsearch端口')
    
    args = parser.parse_args()
    
    integrator = ESIntegrator(es_host=args.es_host, es_port=args.es_port)
    
    if integrator.integrate_documents(args.docs_dir):
        print("\n文档集成成功!")
        print(f"索引名称: {integrator.index_name}")
        print("下一步操作:")
        print("1. 启动后端服务: cd ../ai-QNA--server && mvn spring-boot:run")
        print("2. 访问前端界面: http://localhost:5175/")
        print("3. 开始使用中文知识库进行问答")
    else:
        print("\n文档集成失败!")
        print("请检查:")
        print("• Elasticsearch服务是否启动")
        print("• 文档目录是否存在有效文档")
        print("• 网络连接是否正常")

if __name__ == "__main__":
    main()