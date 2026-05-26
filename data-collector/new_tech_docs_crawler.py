#!/usr/bin/env python3
"""
企业级智能技术助手 - 新增技术文档爬取器
专门爬取 TypeScript、Node.js、Kubernetes、PostgreSQL、MongoDB 的中文文档，自动翻译英文内容为中文
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Any, Optional, Set
import hashlib
from collections import deque
import requests
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewTechDocsCrawler:
    """新增技术文档爬取器"""
    
    def __init__(self, output_dir: str = "chinese_tech_docs", es_host: str = "localhost", es_port: int = 9200):
        self.output_dir = output_dir
        self.session = None
        self.visited_urls: Set[str] = set()
        self.max_depth = 3
        self.max_pages_per_tech = 200
        self.es_host = es_host
        self.es_port = es_port
        self.es_client = None
        self.index_name = "tech_documents"
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.tech_configs = {
            "typescript": {
                "name": "TypeScript",
                "start_urls": [
                    "https://www.typescriptlang.org/zh/docs/",
                    "https://www.runoob.com/typescript/ts-tutorial.html"
                ],
                "base_url": "https://www.typescriptlang.org",
                "language": "中文"
            },
            "nodejs": {
                "name": "Node.js",
                "start_urls": [
                    "https://nodejs.org/zh-cn/docs/",
                    "https://www.runoob.com/nodejs/nodejs-tutorial.html"
                ],
                "base_url": "https://nodejs.org",
                "language": "中文"
            },
            "kubernetes": {
                "name": "Kubernetes",
                "start_urls": [
                    "https://kubernetes.io/zh-cn/docs/",
                    "https://www.runoob.com/kubernetes/kubernetes-tutorial.html"
                ],
                "base_url": "https://kubernetes.io",
                "language": "中文"
            },
            "postgresql": {
                "name": "PostgreSQL",
                "start_urls": [
                    "https://www.runoob.com/postgresql/postgresql-tutorial.html"
                ],
                "base_url": "https://www.runoob.com",
                "language": "中文"
            },
            "mongodb": {
                "name": "MongoDB",
                "start_urls": [
                    "https://www.runoob.com/mongodb/mongodb-tutorial.html"
                ],
                "base_url": "https://www.runoob.com",
                "language": "中文"
            }
        }

    async def init_session(self):
        """初始化会话"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()

    async def fetch_url(self, url: str) -> Optional[str]:
        """获取URL内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"请求失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取URL失败 {url}: {e}")
            return None

    def is_chinese_text(self, text: str) -> bool:
        """判断文本是否为中文"""
        if not text:
            return False
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return False
        
        return chinese_chars / total_chars > 0.3

    def extract_content(self, html: str, tech_name: str) -> Dict[str, Any]:
        """提取文档内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup(['script', 'style']):
            script.decompose()
        
        title = ""
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text().strip()
        
        content_selectors = [
            'main',
            '.content',
            '#content',
            '.documentation',
            '.doc-content',
            'article',
            '.main-content',
            'body'
        ]
        
        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break
        
        if not content_elem:
            content_elem = soup
        
        text_content = content_elem.get_text(separator='\n', strip=True)
        
        lines = []
        for line in text_content.split('\n'):
            line = line.strip()
            if line and len(line) > 10:
                lines.append(line)
        
        content = '\n'.join(lines)
        
        return {
            'title': title,
            'content': content
        }

    def extract_all_links(self, html: str, base_url: str, tech_name: str) -> List[str]:
        """提取所有相关链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            if self.should_follow_link(full_url, tech_name):
                links.append(full_url)
        
        return list(set(links))

    def should_follow_link(self, url: str, tech_name: str) -> bool:
        """判断是否应该跟踪链接"""
        config = self.tech_configs[tech_name]
        base_url = config['base_url']
        
        if not url.startswith(base_url):
            return False
        
        exclude_patterns = [
            r'.*\.(pdf|zip|tar\.gz|exe|dmg)$',
            r'.*download.*',
            r'.*blog.*',
            r'.*community.*',
            r'.*forum.*',
            r'.*signin.*',
            r'.*login.*',
            r'.*logout.*',
            r'.*api/.*',
            r'.*search.*'
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return False
        
        return True

    def split_into_chunks(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """将内容切分成chunk"""
        if not content:
            return []
        
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def get_category(self, tech_name: str, title: str) -> str:
        """获取文档类别"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['api', 'reference', '接口', '参考']):
            return 'API_REFERENCE'
        elif any(word in title_lower for word in ['config', 'configuration', '配置']):
            return 'CONFIGURATION'
        elif any(word in title_lower for word in ['tutorial', 'guide', '教程', '指南']):
            return 'TUTORIAL'
        elif any(word in title_lower for word in ['troubleshoot', 'error', '问题', '故障']):
            return 'TROUBLESHOOTING'
        else:
            return 'GENERAL'

    async def crawl_tech_docs(self, tech_name: str) -> List[Dict[str, Any]]:
        """爬取特定技术栈的文档"""
        logger.info(f"开始爬取 {tech_name} 文档...")
        
        config = self.tech_configs.get(tech_name)
        if not config:
            logger.error(f"未找到 {tech_name} 的配置")
            return []
        
        start_urls = config['start_urls']
        base_url = config['base_url']
        
        documents = []
        queue = deque([(url, 0) for url in start_urls])
        processed = 0
        
        while queue and processed < self.max_pages_per_tech:
            url, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
            
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            logger.info(f"处理页面 {processed + 1}/{self.max_pages_per_tech} (深度 {depth}): {url}")
            
            try:
                html = await self.fetch_url(url)
                if not html:
                    continue
                
                doc_data = self.extract_content(html, tech_name)
                
                if doc_data['content']:
                    chunks = self.split_into_chunks(doc_data['content'])
                    
                    for i, chunk in enumerate(chunks):
                        doc_id = hashlib.md5(f"{url}-{i}".encode()).hexdigest()
                        
                        document = {
                            'id': doc_id,
                            'url': url,
                            'title': doc_data['title'] or f"{tech_name} 文档 - 第{i+1}部分",
                            'content': chunk,
                            'techStack': tech_name,
                            'category': self.get_category(tech_name, doc_data['title']),
                            'source': f"{tech_name}官方文档",
                            'language': '中文',
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'depth': depth
                        }
                        
                        documents.append(document)
                    
                    logger.info(f"提取文档片段 {i+1}/{len(chunks)}: {len(chunk)} 字符")
                
                new_links = self.extract_all_links(html, base_url, tech_name)
                for link in new_links:
                    if link not in self.visited_urls:
                        in_queue = any(link == q_url for q_url, _ in queue)
                        if not in_queue:
                            queue.append((link, depth + 1))
                
                processed += 1
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"处理页面 {url} 时出错: {e}")
                continue
        
        logger.info(f"完成爬取 {tech_name}，共处理 {processed} 个页面，生成 {len(documents)} 个文档片段")
        return documents

    def save_documents(self, documents: List[Dict[str, Any]], tech_name: str):
        """保存文档到文件"""
        if not documents:
            logger.warning(f"没有文档需要保存: {tech_name}")
            return
        
        filename = os.path.join(self.output_dir, f"{tech_name}_chinese_docs.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存 {len(documents)} 个文档片段到: {filename}")

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

    def index_documents_to_es(self, documents: List[Dict[str, Any]]) -> bool:
        """将文档索引到Elasticsearch"""
        if not self.es_client:
            logger.error("Elasticsearch客户端未连接")
            return False
        
        actions = []
        
        for doc in documents:
            enhanced_doc = self.enhance_document(doc)
            
            action = {
                "_index": self.index_name,
                "_id": enhanced_doc['id'],
                "_source": enhanced_doc
            }
            actions.append(action)
        
        try:
            success, failed = bulk(self.es_client, actions, stats_only=True)
            
            logger.info(f"成功索引 {success} 个文档")
            if failed:
                logger.warning(f"索引失败 {failed} 个文档")
            
            self.es_client.indices.refresh(index=self.index_name)
            
            stats = self.es_client.count(index=self.index_name)
            logger.info(f"索引当前包含 {stats['count']} 个文档")
            
            return True
            
        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return False

    async def crawl_and_index_all(self):
        """爬取所有技术栈文档并索引到Elasticsearch"""
        logger.info("开始爬取新增技术栈的文档...")
        
        await self.init_session()
        
        try:
            all_documents = []
            
            for tech_name in self.tech_configs.keys():
                documents = await self.crawl_tech_docs(tech_name)
                self.save_documents(documents, tech_name)
                all_documents.extend(documents)
                self.visited_urls.clear()
            
            if all_documents:
                all_filename = os.path.join(self.output_dir, "new_tech_chinese_docs.json")
                with open(all_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_documents, f, ensure_ascii=False, indent=2)
                logger.info(f"保存所有 {len(all_documents)} 个文档片段到: {all_filename}")
                
                if self.connect_to_es():
                    self.index_documents_to_es(all_documents)
            
            return all_documents
            
        finally:
            await self.close_session()

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='新增技术文档爬取器')
    parser.add_argument('--tech', type=str, help='指定技术栈（如typescript,nodejs,kubernetes等）')
    parser.add_argument('--output-dir', type=str, default='chinese_tech_docs', help='输出目录')
    parser.add_argument('--es-host', type=str, default='localhost', help='Elasticsearch主机')
    parser.add_argument('--es-port', type=int, default=9200, help='Elasticsearch端口')
    
    args = parser.parse_args()
    
    crawler = NewTechDocsCrawler(
        output_dir=args.output_dir,
        es_host=args.es_host,
        es_port=args.es_port
    )
    
    if args.tech:
        tech_names = [tech.strip() for tech in args.tech.split(',')]
        
        await crawler.init_session()
        try:
            all_documents = []
            for tech_name in tech_names:
                if tech_name in crawler.tech_configs:
                    documents = await crawler.crawl_tech_docs(tech_name)
                    crawler.save_documents(documents, tech_name)
                    all_documents.extend(documents)
                else:
                    logger.warning(f"未知技术栈: {tech_name}")
            
            if all_documents and crawler.connect_to_es():
                crawler.index_documents_to_es(all_documents)
                
        finally:
            await crawler.close_session()
    else:
        await crawler.crawl_and_index_all()

if __name__ == "__main__":
    asyncio.run(main())
