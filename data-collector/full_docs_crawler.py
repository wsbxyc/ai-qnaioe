#!/usr/bin/env python3
"""
企业级智能技术助手 - 完整文档爬取器
支持爬取官方文档的所有页面，包括深度链接和完整目录结构
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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullDocsCrawler:
    """完整文档爬取器"""
    
    def __init__(self, output_dir: str = "full_tech_docs"):
        self.output_dir = output_dir
        self.session = None
        self.visited_urls: Set[str] = set()
        self.max_depth = 10  # 最大爬取深度
        self.max_pages_per_tech = 500  # 每个技术栈最大页面数
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 完整的技术栈文档配置
        self.tech_configs = {
            "spring-boot": {
                "base_url": "https://docs.spring.io/spring-boot/docs/current/reference/html/",
                "start_urls": [
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/",
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/getting-started.html",
                    "https://docs.spring.io/spring-boot/docs/current/reference/html/features.html"
                ],
                "selectors": {
                    "content": "#content",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".navigation-links",
                    "toc": ".toc"
                },
                "link_patterns": [
                    r'\.html$',  # HTML页面
                    r'/reference/html/',  # 参考文档
                ],
                "exclude_patterns": [
                    r'index\.html$',  # 索引页面
                    r'#',  # 锚点
                ]
            },
            "java": {
                "base_url": "https://docs.oracle.com/javase/8/docs/api/",
                "start_urls": [
                    "https://docs.oracle.com/javase/8/docs/api/overview-summary.html",
                    "https://docs.oracle.com/javase/8/docs/api/index.html"
                ],
                "selectors": {
                    "content": ".contentContainer",
                    "title": ".header h1",
                    "sections": "h2, h3",
                    "navigation": ".topNav",
                    "toc": ".leftContainer"
                },
                "link_patterns": [
                    r'\.html$',
                    r'/api/',
                ],
                "exclude_patterns": [
                    r'allclasses-frame\.html',
                    r'package-frame\.html',
                ]
            },
            "docker": {
                "base_url": "https://docs.docker.com/",
                "start_urls": [
                    "https://docs.docker.com/",
                    "https://docs.docker.com/get-started/",
                    "https://docs.docker.com/engine/"
                ],
                "selectors": {
                    "content": "article",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".sidebar",
                    "toc": ".toc"
                },
                "link_patterns": [
                    r'/docs/',
                    r'/get-started/',
                    r'/engine/',
                    r'/compose/',
                ],
                "exclude_patterns": [
                    r'/blog/',
                    r'/community/',
                    r'/docker-hub/',
                ]
            },
            "python": {
                "base_url": "https://docs.python.org/3/",
                "start_urls": [
                    "https://docs.python.org/3/",
                    "https://docs.python.org/3/tutorial/",
                    "https://docs.python.org/3/library/"
                ],
                "selectors": {
                    "content": ".body",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".related",
                    "toc": ".toctree-wrapper"
                },
                "link_patterns": [
                    r'/3/',
                    r'/tutorial/',
                    r'/library/',
                    r'/howto/',
                ],
                "exclude_patterns": [
                    r'/download/',
                    r'/bugs/',
                    r'/license/',
                ]
            },
            "vue": {
                "base_url": "https://vuejs.org/",
                "start_urls": [
                    "https://vuejs.org/guide/",
                    "https://vuejs.org/api/",
                    "https://vuejs.org/examples/"
                ],
                "selectors": {
                    "content": ".content",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".sidebar",
                    "toc": ".table-of-contents"
                },
                "link_patterns": [
                    r'/guide/',
                    r'/api/',
                    r'/examples/',
                ],
                "exclude_patterns": [
                    r'/blog/',
                    r'/press/',
                    r'/support/',
                ]
            },
            "react": {
                "base_url": "https://react.dev/",
                "start_urls": [
                    "https://react.dev/learn",
                    "https://react.dev/reference",
                    "https://react.dev/apis"
                ],
                "selectors": {
                    "content": "main",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": "nav",
                    "toc": ".toc"
                },
                "link_patterns": [
                    r'/learn/',
                    r'/reference/',
                    r'/apis/',
                ],
                "exclude_patterns": [
                    r'/blog/',
                    r'/community/',
                ]
            },
            "redis": {
                "base_url": "https://redis.io/",
                "start_urls": [
                    "https://redis.io/docs/",
                    "https://redis.io/docs/latest/",
                    "https://redis.io/commands/"
                ],
                "selectors": {
                    "content": ".td-content",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".td-sidebar",
                    "toc": ".td-toc"
                },
                "link_patterns": [
                    r'/docs/',
                    r'/commands/',
                    r'/topics/',
                ],
                "exclude_patterns": [
                    r'/download/',
                    r'/community/',
                    r'/blog/',
                ]
            },
            "mysql": {
                "base_url": "https://dev.mysql.com/",
                "start_urls": [
                    "https://dev.mysql.com/doc/refman/8.0/en/",
                    "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html"
                ],
                "selectors": {
                    "content": ".chapter",
                    "title": "h1",
                    "sections": "h2, h3",
                    "navigation": ".nav",
                    "toc": ".toc"
                },
                "link_patterns": [
                    r'/doc/refman/8\.0/en/',
                    r'/tutorial',
                    r'/reference',
                ],
                "exclude_patterns": [
                    r'/downloads/',
                    r'/news/',
                    r'/support/',
                ]
            }
        }
    
    async def init_session(self):
        """初始化异步会话"""
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)  # 限制并发连接
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    
    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
    
    def should_follow_link(self, url: str, tech_name: str) -> bool:
        """判断是否应该跟踪此链接"""
        config = self.tech_configs.get(tech_name)
        if not config:
            return False
        
        # 检查是否属于基础URL
        if not url.startswith(config['base_url']):
            return False
        
        # 检查排除模式
        exclude_patterns = config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return False
        
        # 检查包含模式
        link_patterns = config.get('link_patterns', [])
        if link_patterns:
            for pattern in link_patterns:
                if re.search(pattern, url):
                    return True
            return False
        
        return True
    
    def extract_all_links(self, html: str, base_url: str, tech_name: str) -> List[str]:
        """提取所有相关链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 提取导航链接（目录结构）
        config = self.tech_configs.get(tech_name, {})
        selectors = config.get('selectors', {})
        
        # 优先提取导航和目录链接
        nav_selectors = [
            selectors.get('navigation'),
            selectors.get('toc'),
            'nav', '.nav', '.navigation', '.sidebar', '.toc'
        ]
        
        for selector in nav_selectors:
            if selector:
                nav_elements = soup.select(selector)
                for nav in nav_elements:
                    for link in nav.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)
                        if self.should_follow_link(full_url, tech_name):
                            links.append(full_url)
        
        # 提取内容中的链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # 跳过外部链接和锚点
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
                continue
            
            full_url = urljoin(base_url, href)
            
            if self.should_follow_link(full_url, tech_name):
                links.append(full_url)
        
        # 去重并返回
        return list(set(links))
    
    async def crawl_tech_docs_complete(self, tech_name: str) -> List[Dict[str, Any]]:
        """完整爬取特定技术栈的文档"""
        logger.info(f"开始完整爬取 {tech_name} 文档...")
        
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
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"处理页面 {url} 时出错: {e}")
                continue
        
        logger.info(f"完成完整爬取 {tech_name}，共处理 {processed} 个页面，生成 {len(documents)} 个文档片段")
        return documents
    
    # 以下方法与之前的爬取器相同，为了完整性保留
    async def fetch_url(self, url: str) -> Optional[str]:
        """获取URL内容"""
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
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        text = re.sub(r'<[^>]+>', '', text)
        return text
    
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
    
    def get_category(self, tech_name: str, title: str) -> str:
        """根据技术栈和标题确定文档类别"""
        title_lower = title.lower() if title else ""
        
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
        filename = os.path.join(self.output_dir, f"{tech_name}_full_docs.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"保存 {len(documents)} 个 {tech_name} 完整文档片段到 {filename}")
    
    async def crawl_all_tech_docs_complete(self):
        """完整爬取所有技术栈的文档"""
        await self.init_session()
        
        all_documents = []
        
        try:
            for tech_name in self.tech_configs.keys():
                try:
                    # 重置已访问URL
                    self.visited_urls.clear()
                    
                    documents = await self.crawl_tech_docs_complete(tech_name)
                    all_documents.extend(documents)
                    
                    # 保存每个技术栈的文档
                    self.save_documents(documents, tech_name)
                    
                    # 休息一下，避免请求过快
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"完整爬取 {tech_name} 文档时出错: {e}")
                    continue
            
            # 保存所有文档
            all_filename = os.path.join(self.output_dir, "all_tech_full_docs.json")
            with open(all_filename, 'w', encoding='utf-8') as f:
                json.dump(all_documents, f, ensure_ascii=False, indent=2)
            
            logger.info(f"完成所有技术文档完整爬取，共生成 {len(all_documents)} 个文档片段")
            
            return all_documents
            
        finally:
            await self.close_session()

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='完整文档爬取器')
    parser.add_argument('--tech', type=str, help='指定技术栈（如spring-boot,java,docker等）')
    parser.add_argument('--output-dir', type=str, default='full_tech_docs', help='输出目录')
    
    args = parser.parse_args()
    
    crawler = FullDocsCrawler(output_dir=args.output_dir)
    
    if args.tech:
        # 爬取指定技术栈
        tech_names = [tech.strip() for tech in args.tech.split(',')]
        
        await crawler.init_session()
        try:
            for tech_name in tech_names:
                if tech_name in crawler.tech_configs:
                    documents = await crawler.crawl_tech_docs_complete(tech_name)
                    crawler.save_documents(documents, tech_name)
                else:
                    logger.warning(f"未知技术栈: {tech_name}")
        finally:
            await crawler.close_session()
    
    else:
        # 爬取所有技术栈
        await crawler.crawl_all_tech_docs_complete()

if __name__ == "__main__":
    asyncio.run(main())