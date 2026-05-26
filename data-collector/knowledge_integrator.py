#!/usr/bin/env python3
"""
企业级智能技术助手 - 知识库集成器
将爬取的技术文档集成到Elasticsearch知识库中
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeIntegrator:
    """知识库集成器"""
    
    def __init__(self, es_host: str = "localhost", es_port: int = 9200):
        self.es_host = es_host
        self.es_port = es_port
        self.es_client = None
        self.index_name = "tech_documents"
        
    def connect_elasticsearch(self) -> bool:
        """连接Elasticsearch"""
        try:
            self.es_client = Elasticsearch([{'host': self.es_host, 'port': self.es_port}])
            
            if self.es_client.ping():
                logger.info("成功连接到Elasticsearch")
                return True
            else:
                logger.error("无法连接到Elasticsearch")
                return False
                
        except Exception as e:
            logger.error(f"连接Elasticsearch失败: {e}")
            return False
    
    def create_index(self) -> bool:
        """创建Elasticsearch索引"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return False
        
        # 索引映射
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
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
                    "tech_stack": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "total_chunks": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "popularity": {"type": "integer"},
                    "quality_score": {"type": "float"},
                    "tags": {"type": "keyword"},
                    "summary": {"type": "text"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_max_word": {
                            "type": "ik_max_word"
                        },
                        "ik_smart": {
                            "type": "ik_smart"
                        }
                    }
                }
            }
        }
        
        try:
            # 检查索引是否存在
            if self.es_client.indices.exists(index=self.index_name):
                logger.info(f"索引 {self.index_name} 已存在")
                return True
            
            # 创建索引
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"成功创建索引 {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def load_documents(self, docs_dir: str = "tech_docs") -> List[Dict[str, Any]]:
        """加载爬取的文档"""
        all_documents = []
        
        if not os.path.exists(docs_dir):
            logger.error(f"文档目录不存在: {docs_dir}")
            return all_documents
        
        # 加载所有技术栈的文档
        for filename in os.listdir(docs_dir):
            if filename.endswith('_docs.json'):
                filepath = os.path.join(docs_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        documents = json.load(f)
                    
                    logger.info(f"从 {filename} 加载 {len(documents)} 个文档")
                    all_documents.extend(documents)
                    
                except Exception as e:
                    logger.error(f"加载文件 {filename} 失败: {e}")
                    continue
        
        # 加载合并的文档文件
        all_filepath = os.path.join(docs_dir, "all_tech_docs.json")
        if os.path.exists(all_filepath):
            try:
                with open(all_filepath, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                logger.info(f"从合并文件加载 {len(documents)} 个文档")
                all_documents.extend(documents)
                
            except Exception as e:
                logger.error(f"加载合并文件失败: {e}")
        
        # 去重
        seen_ids = set()
        unique_documents = []
        
        for doc in all_documents:
            if doc['id'] not in seen_ids:
                seen_ids.add(doc['id'])
                unique_documents.append(doc)
        
        logger.info(f"去重后共 {len(unique_documents)} 个唯一文档")
        return unique_documents
    
    def enhance_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """增强文档数据"""
        # 添加时间戳
        current_time = datetime.now().isoformat()
        doc['created_at'] = current_time
        doc['updated_at'] = current_time
        
        # 添加标签
        tech_stack = doc.get('tech_stack', '')
        category = doc.get('category', '')
        
        tags = [tech_stack, category]
        
        # 根据内容添加更多标签
        content = doc.get('content', '').lower()
        if 'api' in content or '接口' in content:
            tags.append('API')
        if 'config' in content or '配置' in content:
            tags.append('CONFIG')
        if 'error' in content or '问题' in content:
            tags.append('TROUBLESHOOTING')
        
        doc['tags'] = list(set(tags))
        
        # 生成摘要
        content = doc.get('content', '')
        if len(content) > 200:
            doc['summary'] = content[:200] + '...'
        else:
            doc['summary'] = content
        
        # 设置质量和流行度分数
        doc['quality_score'] = self.calculate_quality_score(doc)
        doc['popularity'] = self.calculate_popularity(doc)
        
        return doc
    
    def calculate_quality_score(self, doc: Dict[str, Any]) -> float:
        """计算文档质量分数"""
        score = 0.5  # 基础分数
        
        content = doc.get('content', '')
        title = doc.get('title', '')
        
        # 根据内容长度加分
        content_length = len(content)
        if content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.1
        
        # 根据标题质量加分
        if title and len(title) > 10:
            score += 0.1
        
        # 根据技术栈加分
        tech_stack = doc.get('tech_stack', '')
        if tech_stack in ['spring-boot', 'java', 'docker']:
            score += 0.1
        
        # 根据类别加分
        category = doc.get('category', '')
        if category in ['API', 'CONFIG']:
            score += 0.1
        
        return min(score, 1.0)  # 确保不超过1.0
    
    def calculate_popularity(self, doc: Dict[str, Any]) -> int:
        """计算文档流行度"""
        popularity = 50  # 基础流行度
        
        tech_stack = doc.get('tech_stack', '')
        category = doc.get('category', '')
        
        # 热门技术栈加分
        if tech_stack in ['spring-boot', 'java', 'docker']:
            popularity += 30
        elif tech_stack in ['vue', 'react', 'python']:
            popularity += 20
        
        # 热门类别加分
        if category in ['API', 'CONFIG']:
            popularity += 20
        elif category in ['TROUBLESHOOTING', 'BEST_PRACTICE']:
            popularity += 10
        
        return popularity
    
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
    
    def integrate_knowledge(self, docs_dir: str = "tech_docs") -> bool:
        """集成知识库"""
        logger.info("开始集成知识库...")
        
        # 连接Elasticsearch
        if not self.connect_elasticsearch():
            return False
        
        # 创建索引
        if not self.create_index():
            return False
        
        # 加载文档
        documents = self.load_documents(docs_dir)
        if not documents:
            logger.error("未找到任何文档")
            return False
        
        # 索引文档
        if not self.index_documents(documents):
            return False
        
        logger.info("知识库集成完成")
        return True
    
    def search_documents(self, query: str, tech_stack: str = None, category: str = None, 
                        size: int = 10) -> List[Dict[str, Any]]:
        """搜索文档"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return []
        
        # 构建查询
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content", "summary"],
                                "type": "best_fields"
                            }
                        }
                    ]
                }
            },
            "size": size
        }
        
        # 添加过滤器
        filters = []
        
        if tech_stack:
            filters.append({"term": {"tech_stack": tech_stack}})
        
        if category:
            filters.append({"term": {"category": category}})
        
        if filters:
            search_body["query"]["bool"]["filter"] = filters
        
        try:
            response = self.es_client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='知识库集成器')
    parser.add_argument('--docs-dir', type=str, default='tech_docs', help='文档目录')
    parser.add_argument('--es-host', type=str, default='localhost', help='Elasticsearch主机')
    parser.add_argument('--es-port', type=int, default=9200, help='Elasticsearch端口')
    parser.add_argument('--search', type=str, help='搜索查询')
    parser.add_argument('--tech-stack', type=str, help='技术栈过滤')
    parser.add_argument('--category', type=str, help='类别过滤')
    
    args = parser.parse_args()
    
    integrator = KnowledgeIntegrator(es_host=args.es_host, es_port=args.es_port)
    
    if args.search:
        # 搜索模式
        results = integrator.search_documents(
            query=args.search,
            tech_stack=args.tech_stack,
            category=args.category
        )
        
        print(f"找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['tech_stack']}] {result['title']}")
            print(f"   分数: {result['score']:.3f}")
            print(f"   摘要: {result.get('summary', '')[:100]}...")
    
    else:
        # 集成模式
        success = integrator.integrate_knowledge(args.docs_dir)
        if success:
            print("知识库集成成功")
        else:
            print("知识库集成失败")

if __name__ == "__main__":
    main()