#!/usr/bin/env python3
"""
企业级智能技术助手 - 中文文档爬取器
专门爬取中文技术文档，自动翻译英文内容为中文
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
from googletrans import Translator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChineseDocsCrawler:
    """中文文档爬取器"""
    
    def __init__(self, output_dir: str = "chinese_tech_docs"):
        self.output_dir = output_dir
        self.session = None
        self.translator = Translator()
        self.visited_urls: Set[str] = set()
        self.max_depth = 3  # 最大爬取深度
        self.max_pages_per_tech = 200  # 每个技术栈最大页面数
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 中文技术文档配置
        self.tech_configs = {
            "spring-boot": {
                "name": "Spring Boot",
                "start_urls": [
                    "https://springdoc.cn/spring-boot/",
                    "https://springdoc.cn/spring-boot/reference/",
                    "https://springdoc.cn/spring-boot/docs/current/reference/html/"
                ],
                "base_url": "https://springdoc.cn",
                "language": "中文"
            },
            "java": {
                "name": "Java",
                "start_urls": [
                    "https://docs.oracle.com/javase/8/docs/api/",
                    "https://www.runoob.com/java/java-tutorial.html"
                ],
                "base_url": "https://docs.oracle.com",
                "language": "中文"
            },
            "docker": {
                "name": "Docker",
                "start_urls": [
                    "https://docs.docker.com/get-started/",
                    "https://docker.easydoc.net/doc/",
                    "https://www.runoob.com/docker/docker-tutorial.html"
                ],
                "base_url": "https://docs.docker.com",
                "language": "中文"
            },
            "python": {
                "name": "Python",
                "start_urls": [
                    "https://docs.python.org/zh-cn/3/",
                    "https://www.runoob.com/python/python-tutorial.html",
                    "https://www.liaoxuefeng.com/wiki/1016959663602400"
                ],
                "base_url": "https://docs.python.org",
                "language": "中文"
            },
            "vue": {
                "name": "Vue.js",
                "start_urls": [
                    "https://cn.vuejs.org/guide/introduction.html",
                    "https://v3.cn.vuejs.org/guide/introduction.html",
                    "https://www.runoob.com/vue3/vue3-tutorial.html"
                ],
                "base_url": "https://cn.vuejs.org",
                "language": "中文"
            },
            "react": {
                "name": "React",
                "start_urls": [
                    "https://zh-hans.reactjs.org/docs/getting-started.html",
                    "https://react.docschina.org/docs/getting-started.html",
                    "https://www.runoob.com/react/react-tutorial.html"
                ],
                "base_url": "https://zh-hans.reactjs.org",
                "language": "中文"
            },
            "redis": {
                "name": "Redis",
                "start_urls": [
                    "https://redis.io/docs/",
                    "https://www.redis.com.cn/documentation.html",
                    "https://www.runoob.com/redis/redis-tutorial.html"
                ],
                "base_url": "https://redis.io",
                "language": "中文"
            },
            "mysql": {
                "name": "MySQL",
                "start_urls": [
                    "https://dev.mysql.com/doc/",
                    "https://www.runoob.com/mysql/mysql-tutorial.html",
                    "https://www.mysqlzh.com/doc/"
                ],
                "base_url": "https://dev.mysql.com",
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
        
        # 检查中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return False
        
        # 如果中文字符比例超过30%，认为是中文
        return chinese_chars / total_chars > 0.3

    async def translate_to_chinese(self, text: str) -> str:
        """将英文文本翻译为中文"""
        if not text or self.is_chinese_text(text):
            return text
        
        try:
            # 限制翻译文本长度
            if len(text) > 4000:
                text = text[:4000]
            
            translated = self.translator.translate(text, dest='zh-cn')
            return translated.text
        except Exception as e:
            logger.warning(f"翻译失败: {e}")
            return text  # 返回原文

    def extract_content(self, html: str, tech_name: str) -> Dict[str, Any]:
        """提取文档内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(['script', 'style']):
            script.decompose()
        
        # 提取标题
        title = ""
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text().strip()
        
        # 提取主要内容
        content_parts = []
        
        # 尝试不同的内容提取策略
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
        
        # 提取文本内容
        text_content = content_elem.get_text(separator='\n', strip=True)
        
        # 清理文本
        lines = []
        for line in text_content.split('\n'):
            line = line.strip()
            if line and len(line) > 10:  # 过滤过短的行
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
            
            # 过滤链接
            if self.should_follow_link(full_url, tech_name):
                links.append(full_url)
        
        return list(set(links))  # 去重

    def should_follow_link(self, url: str, tech_name: str) -> bool:
        """判断是否应该跟踪链接"""
        # 排除外部链接
        if not url.startswith(self.tech_configs[tech_name]['base_url']):
            return False
        
        # 排除常见的不相关路径
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
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前chunk加上新段落不超过最大大小
            if len(current_chunk) + len(paragraph) <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                # 保存当前chunk并开始新的chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        # 添加最后一个chunk
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

    async def crawl_tech_docs_chinese(self, tech_name: str) -> List[Dict[str, Any]]:
        """爬取特定技术栈的中文文档"""
        logger.info(f"开始爬取 {tech_name} 中文文档...")
        
        config = self.tech_configs.get(tech_name)
        if not config:
            logger.error(f"未找到 {tech_name} 的配置")
            return []
        
        start_urls = config['start_urls']
        base_url = config['base_url']
        
        documents = []
        queue = deque([(url, 0) for url in start_urls])  # (url, depth)
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
                
                # 提取内容
                doc_data = self.extract_content(html, tech_name)
                
                if doc_data['content']:
                    # 检查是否为中文，如果不是则翻译
                    if not self.is_chinese_text(doc_data['content']):
                        logger.info(f"检测到英文内容，开始翻译...")
                        doc_data['content'] = await self.translate_to_chinese(doc_data['content'])
                    
                    # 切分成chunk
                    chunks = self.split_into_chunks(doc_data['content'])
                    
                    for i, chunk in enumerate(chunks):
                        doc_id = hashlib.md5(f"{url}-{i}".encode()).hexdigest()
                        
                        document = {
                            'id': doc_id,
                            'url': url,
                            'title': doc_data['title'] or f"{tech_name} 文档 - 第{i+1}部分",
                            'content': chunk,
                            'tech_stack': tech_name,
                            'category': self.get_category(tech_name, doc_data['title']),
                            'source': f"{tech_name}官方文档",
                            'language': '中文',
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'depth': depth
                        }
                        
                        documents.append(document)
                        
                    logger.info(f"提取文档片段 {i+1}/{len(chunks)}: {len(chunk)} 字符")
                
                # 提取新链接
                new_links = self.extract_all_links(html, base_url, tech_name)
                for link in new_links:
                    if link not in self.visited_urls:
                        # 检查是否已在队列中
                        in_queue = any(link == q_url for q_url, _ in queue)
                        if not in_queue:
                            queue.append((link, depth + 1))
                
                processed += 1
                
                # 避免请求过快
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

    async def crawl_all_tech_docs_chinese(self):
        """爬取所有技术栈的中文文档"""
        logger.info("开始爬取所有技术栈的中文文档...")
        
        await self.init_session()
        
        try:
            all_documents = []
            
            for tech_name in self.tech_configs.keys():
                documents = await self.crawl_tech_docs_chinese(tech_name)
                self.save_documents(documents, tech_name)
                all_documents.extend(documents)
                
                # 重置已访问URL，为下一个技术栈准备
                self.visited_urls.clear()
            
            # 保存所有文档
            if all_documents:
                all_filename = os.path.join(self.output_dir, "all_tech_chinese_docs.json")
                with open(all_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_documents, f, ensure_ascii=False, indent=2)
                logger.info(f"保存所有 {len(all_documents)} 个文档片段到: {all_filename}")
            
            return all_documents
            
        finally:
            await self.close_session()

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='中文文档爬取器')
    parser.add_argument('--tech', type=str, help='指定技术栈（如spring-boot,java,docker等）')
    parser.add_argument('--output-dir', type=str, default='chinese_tech_docs', help='输出目录')
    
    args = parser.parse_args()
    
    crawler = ChineseDocsCrawler(output_dir=args.output_dir)
    
    if args.tech:
        # 爬取指定技术栈
        tech_names = [tech.strip() for tech in args.tech.split(',')]
        
        await crawler.init_session()
        try:
            for tech_name in tech_names:
                if tech_name in crawler.tech_configs:
                    documents = await crawler.crawl_tech_docs_chinese(tech_name)
                    crawler.save_documents(documents, tech_name)
                else:
                    logger.warning(f"未知技术栈: {tech_name}")
        finally:
            await crawler.close_session()
    
    else:
        # 爬取所有技术栈
        await crawler.crawl_all_tech_docs_chinese()

if __name__ == "__main__":
    asyncio.run(main())