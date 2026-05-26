#!/usr/bin/env python3
"""
企业级智能技术助手 - 技术文档爬取工具
支持爬取Spring Boot、Java、Docker、Python、Vue、React、Redis、MySQL等官方文档
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Any, Optional
import hashlib
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechDocsCrawler:
    """技术文档爬取器"""
    
    def __init__(self, output_dir: str = "tech_docs"):
        self.output_dir = output_dir
        self.session = None
        self.visited_urls = set()
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 技术栈文档配置
        self.tech_configs = {
            "spring-boot": {
                "base_url": "https://docs.spring.io/spring-boot/docs/current/reference/html/",
                "start_urls": [
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/getting-started.html",
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/features.html",
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/configuration.html"
                ],
                "selectors": {
                    "content": "#content",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "java": {
                "base_url": "https://docs.oracle.com/javase/8/docs/api/",
                "start_urls": [
                    "https://docs.oracle.com/javase/8/docs/api/overview-summary.html",
                    "https://docs.oracle.com/javase/8/docs/api/java/util/package-summary.html"
                ],
                "selectors": {
                    "content": ".contentContainer",
                    "title": ".header h1",
                    "sections": "h2, h3"
                }
            },
            "docker": {
                "base_url": "https://docs.docker.com/",
                "start_urls": [
                    "https://docs.docker.com/get-started/",
                    "https://docs.docker.com/engine/",
                    "https://docs.docker.com/compose/"
                ],
                "selectors": {
                    "content": "article",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "python": {
                "base_url": "https://docs.python.org/3/",
                "start_urls": [
                    "https://docs.python.org/3/tutorial/",
                    "https://docs.python.org/3/library/",
                    "https://docs.python.org/3/howto/"
                ],
                "selectors": {
                    "content": ".body",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "vue": {
                "base_url": "https://vuejs.org/guide/",
                "start_urls": [
                    "https://vuejs.org/guide/introduction.html",
                    "https://vuejs.org/guide/essentials/",
                    "https://vuejs.org/guide/components/"
                ],
                "selectors": {
                    "content": ".content",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "react": {
                "base_url": "https://react.dev/",
                "start_urls": [
                    "https://react.dev/learn",
                    "https://react.dev/reference"
                ],
                "selectors": {
                    "content": "main",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "redis": {
                "base_url": "https://redis.io/docs/",
                "start_urls": [
                    "https://redis.io/docs/latest/",
                    "https://redis.io/docs/latest/develop/",
                    "https://redis.io/docs/latest/operate/"
                ],
                "selectors": {
                    "content": ".td-content",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            },
            "mysql": {
                "base_url": "https://dev.mysql.com/doc/",
                "start_urls": [
                    "https://dev.mysql.com/doc/refman/8.0/en/",
                    "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html"
                ],
                "selectors": {
                    "content": ".chapter",
                    "title": "h1",
                    "sections": "h2, h3"
                }
            }
        }
    
    async def init_session(self):
        """初始化异步会话"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
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
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """获取URL内容"""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"请求失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"请求错误: {url}, 错误: {e}")
            return None
    
    def extract_links(self, html: str, base_url: str, tech_name: str) -> List[str]:
        """提取相关链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 提取所有链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # 跳过外部链接和锚点
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
                continue
            
            # 转换为绝对URL
            full_url = urljoin(base_url, href)
            
            # 检查是否属于同一域名和技术栈
            if self.is_valid_link(full_url, tech_name):
                links.append(full_url)
        
        return list(set(links))  # 去重
    
    def is_valid_link(self, url: str, tech_name: str) -> bool:
        """检查链接是否有效"""
        config = self.tech_configs.get(tech_name)
        if not config:
            return False
        
        # 检查是否属于基础URL
        return url.startswith(config['base_url'])
    
    def extract_content(self, html: str, tech_name: str) -> Dict[str, Any]:
        """提取页面内容"""
        soup = BeautifulSoup(html, 'html.parser')
        config = self.tech_configs.get(tech_name, {})
        selectors = config.get('selectors', {})
        
        # 提取标题
        title = ""
        if selectors.get('title'):
            title_elem = soup.select_one(selectors['title'])
            if title_elem:
                title = self.clean_text(title_elem.get_text())
        
        # 提取主要内容
        content = ""
        if selectors.get('content'):
            content_elem = soup.select_one(selectors['content'])
            if content_elem:
                content = self.clean_text(content_elem.get_text())
        
        # 如果选择器无效，尝试通用提取
        if not content:
            # 移除导航、侧边栏等
            for unwanted in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                unwanted.decompose()
            content = self.clean_text(soup.get_text())
        
        # 提取章节标题
        sections = []
        if selectors.get('sections'):
            section_elems = soup.select(selectors['sections'])
            for elem in section_elems:
                section_text = self.clean_text(elem.get_text())
                if section_text:
                    sections.append(section_text)
        
        return {
            'title': title,
            'content': content,
            'sections': sections,
            'tech_stack': tech_name
        }
    
    async def crawl_tech_docs(self, tech_name: str, max_pages: int = 50) -> List[Dict[str, Any]]:
        """爬取特定技术栈的文档"""
        logger.info(f"开始爬取 {tech_name} 文档...")
        
        config = self.tech_configs.get(tech_name)
        if not config:
            logger.error(f"未找到 {tech_name} 的配置")
            return []
        
        start_urls = config['start_urls']
        base_url = config['base_url']
        
        documents = []
        queue = start_urls.copy()
        processed = 0
        
        while queue and processed < max_pages:
            url = queue.pop(0)
            
            logger.info(f"处理页面 {processed + 1}/{max_pages}: {url}")
            
            html = await self.fetch_url(url)
            if not html:
                continue
            
            # 提取内容
            doc_data = self.extract_content(html, tech_name)
            
            if doc_data['content']:
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
                        'total_chunks': len(chunks)
                    }
                    
                    documents.append(document)
                    logger.info(f"提取文档片段 {i+1}/{len(chunks)}: {len(chunk)} 字符")
                
                # 提取新链接
                new_links = self.extract_links(html, base_url, tech_name)
                for link in new_links:
                    if link not in self.visited_urls and link not in queue:
                        queue.append(link)
            
            processed += 1
            
            # 避免请求过快
            await asyncio.sleep(1)
        
        logger.info(f"完成爬取 {tech_name}，共处理 {processed} 个页面，生成 {len(documents)} 个文档片段")
        return documents
    
    def get_category(self, tech_name: str, title: str) -> str:
        """根据技术栈和标题确定文档类别"""
        title_lower = title.lower() if title else ""
        
        # 根据关键词判断类别
        if any(keyword in title_lower for keyword in ['api', 'reference', '接口', '方法']):
            return 'API'
        elif any(keyword in title_lower for keyword in ['config', 'configuration', '配置', '设置']):
            return 'CONFIG'
        elif any(keyword in title_lower for keyword in ['troubleshoot', 'error', 'debug', '问题', '错误']):
            return 'TROUBLESHOOTING'
        elif any(keyword in title_lower for keyword in ['best practice', 'guide', '指南', '最佳实践']):
            return 'BEST_PRACTICE'
        else:
            return 'TUTORIAL'
    
    def save_documents(self, documents: List[Dict[str, Any]], tech_name: str):
        """保存文档到文件"""
        filename = os.path.join(self.output_dir, f"{tech_name}_docs.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存 {len(documents)} 个 {tech_name} 文档片段到 {filename}")
    
    async def crawl_all_tech_docs(self, max_pages_per_tech: int = 30):
        """爬取所有技术栈的文档"""
        await self.init_session()
        
        all_documents = []
        
        try:
            for tech_name in self.tech_configs.keys():
                try:
                    documents = await self.crawl_tech_docs(tech_name, max_pages_per_tech)
                    all_documents.extend(documents)
                    
                    # 保存每个技术栈的文档
                    self.save_documents(documents, tech_name)
                    
                except Exception as e:
                    logger.error(f"爬取 {tech_name} 文档时出错: {e}")
                    continue
            
            # 保存所有文档
            all_filename = os.path.join(self.output_dir, "all_tech_docs.json")
            with open(all_filename, 'w', encoding='utf-8') as f:
                json.dump(all_documents, f, ensure_ascii=False, indent=2)
            
            logger.info(f"完成所有技术文档爬取，共生成 {len(all_documents)} 个文档片段")
            
            return all_documents
            
        finally:
            await self.close_session()

# 同步版本（用于简单调用）
def crawl_tech_docs_sync(max_pages_per_tech: int = 20):
    """同步版本的文档爬取"""
    crawler = TechDocsCrawler()
    
    # 创建事件循环并运行异步任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(crawler.crawl_all_tech_docs(max_pages_per_tech))
        return result
    finally:
        loop.close()

if __name__ == "__main__":
    # 命令行使用示例
    import argparse
    
    parser = argparse.ArgumentParser(description='技术文档爬取工具')
    parser.add_argument('--tech', type=str, help='指定技术栈（如spring-boot,java,docker等）')
    parser.add_argument('--max-pages', type=int, default=20, help='每个技术栈最大爬取页面数')
    parser.add_argument('--output-dir', type=str, default='tech_docs', help='输出目录')
    
    args = parser.parse_args()
    
    crawler = TechDocsCrawler(output_dir=args.output_dir)
    
    if args.tech:
        # 爬取指定技术栈
        tech_names = [tech.strip() for tech in args.tech.split(',')]
        
        async def crawl_selected():
            await crawler.init_session()
            try:
                for tech_name in tech_names:
                    if tech_name in crawler.tech_configs:
                        documents = await crawler.crawl_tech_docs(tech_name, args.max_pages)
                        crawler.save_documents(documents, tech_name)
                    else:
                        logger.warning(f"未知技术栈: {tech_name}")
            finally:
                await crawler.close_session()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(crawl_selected())
        loop.close()
    
    else:
        # 爬取所有技术栈
        crawl_tech_docs_sync(args.max_pages)