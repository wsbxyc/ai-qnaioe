#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级爬虫工具 - 专门针对配置问题和API接口进行深度爬取
"""

import asyncio
import json
import re
import hashlib
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Set
import aiohttp
from bs4 import BeautifulSoup
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedTechCrawler:
    """高级技术文档爬虫"""
    
    def __init__(self):
        self.session = None
        self.visited_urls: Set[str] = set()
        self.binary_extensions = {'.zip', '.gz', '.tar', '.bz2', '.7z', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', '.exe', '.dmg', '.iso'}
        
        self.config_keywords = [
            '配置', '配置项', '配置文件', 'application.properties', 'application.yml',
            '环境变量', '参数', '设置', 'properties', 'yml', 'yaml',
            'configuration', 'config', 'settings', 'env', 'environment'
        ]
        
        self.api_keywords = [
            'API', '接口', '端点', 'endpoint', 'REST', 'RESTful',
            '控制器', 'controller', '服务', 'service', '方法', 'method',
            '请求', 'response', '参数', 'parameter', '注解', 'annotation'
        ]
        
        self.advanced_topics = [
            '高级', '进阶', '性能优化', '安全', '并发', '分布式',
            '微服务', '容器化', '部署', '监控', '日志', '调试',
            '最佳实践', '设计模式', '架构', '源码分析'
        ]
        
        # 技术栈特定的深度爬取URL
        self.tech_stack_deep_urls = {
            'spring-boot': [
                'https://springdoc.cn/configuration/',
                'https://springdoc.cn/api/',
                'https://springdoc.cn/advanced/',
                'https://springdoc.cn/security/',
                'https://springdoc.cn/performance/'
            ],
            'docker': [
                'https://docs.docker.com/config/',
                'https://docs.docker.com/engine/api/',
                'https://docs.docker.com/compose/compose-file/',
                'https://docs.docker.com/security/',
                'https://docs.docker.com/engine/swarm/'
            ],
            'python': [
                'https://docs.python.org/zh-cn/3/library/',
                'https://docs.python.org/zh-cn/3/howto/',
                'https://docs.python.org/zh-cn/3/extending/',
                'https://docs.python.org/zh-cn/3/c-api/',
                'https://docs.python.org/zh-cn/3/faq/'
            ],
            'vue': [
                'https://cn.vuejs.org/api/',
                'https://cn.vuejs.org/guide/extras/',
                'https://cn.vuejs.org/guide/best-practices/',
                'https://cn.vuejs.org/guide/advanced/',
                'https://cn.vuejs.org/guide/security/'
            ],
            'java': [
                'https://docs.oracle.com/en/java/javase/17/docs/api/',
                'https://docs.oracle.com/javase/tutorial/',
                'https://www.baeldung.com/java-tutorial',
                'https://jenkov.com/java/index.html',
                'https://www.tutorialspoint.com/java/index.htm',
                'https://howtodoinjava.com/java-17/'
            ],
            'redis': [
                'https://redis.io/docs/latest/commands/',
                'https://redis.io/docs/latest/develop/',
                'https://redis.io/docs/latest/operate/',
                'https://redis.io/docs/latest/integrate/',
                'https://www.runoob.com/redis/redis-tutorial.html',
                'https://redis.com.cn/commands.html'
            ],
            'mysql': [
                'https://dev.mysql.com/doc/refman/8.0/en/',
                'https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html',
                'https://dev.mysql.com/doc/refman/8.0/en/optimization.html',
                'https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html',
                'https://www.runoob.com/mysql/mysql-tutorial.html',
                'https://www.mysqltutorial.org/'
            ],
            'react': [
                'https://react.dev/learn',
                'https://react.dev/reference/react',
                'https://react.dev/learn/thinking-in-react',
                'https://reactrouter.com/en/main/start/overview',
                'https://zh-hans.react.dev/learn',
                'https://www.runoob.com/react/react-tutorial.html'
            ]
        }
        
        # 技术栈特定关键词
        self.tech_keywords = {
            'spring-boot': ['spring', 'boot', 'bean', 'autowired', 'controller', 'restcontroller', 'service', 'repository', 'jpa', 'hibernate', '微服务', 'spring cloud'],
            'docker': ['docker', 'container', 'image', 'compose', 'swarm', 'kubernetes', 'k8s', 'pod', 'deployment', 'dockerfile'],
            'python': ['python', 'import', 'def', 'class', 'module', 'django', 'flask', 'fastapi', 'numpy', 'pandas', 'asyncio'],
            'vue': ['vue', 'component', 'props', 'emit', 'router', 'vuex', 'pinia', 'composition api', 'options api', 'vite'],
            'java': ['java', 'jvm', 'jdk', 'jre', 'maven', 'gradle', 'spring', 'hibernate', 'jpa', 'servlet', 'tomcat', 'jetty', 'java8', 'java11', 'java17'],
            'redis': ['redis', 'redis缓存', 'redis命令', 'redis数据结构', 'redis持久化', 'redis集群', 'redis哨兵', 'redis事务', 'redis锁'],
            'mysql': ['mysql', 'sql', '数据库', '索引', '事务', '存储过程', '触发器', '视图', '主从复制', '分库分表', 'mybatis', 'jdbc'],
            'react': ['react', 'react组件', 'hooks', 'usestate', 'useeffect', 'usecontext', 'props', 'state', 'jsx', 'virtual dom', 'next.js', 'redux', 'react router']
        }
    
    async def init_session(self):
        """初始化会话"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
    
    def is_binary_url(self, url: str, content_type: str = '') -> bool:
        """判断是否为二进制文件URL"""
        # 检查文件扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        for ext in self.binary_extensions:
            if path.endswith(ext):
                return True
        
        # 检查Content-Type
        if content_type:
            binary_content_types = [
                'application/zip', 'application/gzip', 'application/x-tar',
                'application/x-bzip2', 'application/pdf', 'application/msword',
                'application/vnd.openxmlformats', 'image/', 'video/', 'audio/',
                'application/octet-stream'
            ]
            for ct in binary_content_types:
                if content_type.startswith(ct):
                    return True
        
        return False
    
    async def fetch_html(self, url: str) -> str:
        """安全地获取HTML内容"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ''
                
                content_type = response.headers.get('Content-Type', '').lower()
                
                # 检查是否为二进制文件
                if self.is_binary_url(url, content_type):
                    logger.warning(f"跳过二进制文件: {url} (Content-Type: {content_type})")
                    return ''
                
                # 尝试获取文本内容
                try:
                    # 优先使用响应头中的编码
                    html = await response.text()
                    return html
                except UnicodeDecodeError as e:
                    # 如果解码失败，尝试其他编码
                    logger.warning(f"UTF-8解码失败 {url}: {e}, 尝试其他编码")
                    
                    # 获取原始字节
                    raw_content = await response.read()
                    
                    # 尝试常见编码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            html = raw_content.decode(encoding)
                            logger.info(f"使用 {encoding} 编码成功解码: {url}")
                            return html
                        except UnicodeDecodeError:
                            continue
                    
                    # 所有编码都失败
                    logger.error(f"无法解码内容: {url}, 内容可能是二进制文件")
                    return ''
                    
        except Exception as e:
            logger.warning(f"获取URL失败 {url}: {e}")
            return ''
    
    def is_relevant_content(self, text: str, tech_stack: str) -> bool:
        """判断内容是否相关"""
        if not text or len(text.strip()) < 50:  # 内容太短则跳过
            return False
            
        text_lower = text.lower()
        
        # 检查是否包含配置相关关键词
        config_match = any(keyword in text_lower for keyword in self.config_keywords)
        
        # 检查是否包含API相关关键词
        api_match = any(keyword in text_lower for keyword in self.api_keywords)
        
        # 检查是否包含高级主题关键词
        advanced_match = any(keyword in text_lower for keyword in self.advanced_topics)
        
        # 检查是否包含技术栈特定关键词
        tech_match = any(keyword in text_lower for keyword in self.tech_keywords.get(tech_stack, []))
        
        return config_match or api_match or advanced_match or tech_match
    
    def extract_technical_content(self, soup: BeautifulSoup) -> str:
        """提取技术相关内容"""
        # 优先提取代码块
        code_blocks = soup.find_all(['pre', 'code'])
        code_content = '\n'.join([block.get_text().strip() for block in code_blocks if block.get_text().strip()])
        
        # 提取配置相关内容
        config_patterns = [
            r'application\.(properties|yml|yaml)',
            r'配置.*?[：:]',
            r'参数.*?[：:]',
            r'设置.*?[：:]',
            r'[\w\.\-]+\s*=\s*.+',  # properties格式
            r'[\w\-]+\s*:\s*.+'      # yaml格式
        ]
        
        config_content = []
        for pattern in config_patterns:
            matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
            config_content.extend(matches)
        
        # 提取API相关内容
        api_patterns = [
            r'@\w+Mapping',  # Spring注解
            r'\w+\.\w+\s*\(',  # 方法调用
            r'(GET|POST|PUT|DELETE|PATCH)\s+/\w+',  # HTTP方法
            r'/api/\w+'  # API路径
        ]
        
        api_content = []
        for pattern in api_patterns:
            matches = re.findall(pattern, soup.get_text())
            api_content.extend(matches)
        
        # 提取Java特定内容
        java_patterns = [
            r'(public|private|protected)\s+(static\s+)?(void|[\w<>]+)\s+\w+\s*\([^)]*\)\s*\{',  # 方法声明
            r'@\w+',  # 注解
            r'new\s+\w+\s*\([^)]*\)',  # 对象实例化
            r'(extends|implements)\s+\w+',  # 继承和实现
            r'import\s+[\w\.]+;'  # 导入语句
        ]
        
        java_content = []
        for pattern in java_patterns:
            matches = re.findall(pattern, soup.get_text())
            java_content.extend(matches)
        
        # 提取SQL内容
        sql_patterns = [
            r'SELECT\s+.*?\s+FROM\s+\w+',
            r'INSERT\s+INTO\s+\w+',
            r'UPDATE\s+\w+\s+SET',
            r'DELETE\s+FROM\s+\w+',
            r'CREATE\s+TABLE\s+\w+',
            r'ALTER\s+TABLE\s+\w+',
            r'CREATE\s+INDEX',
            r'JOIN\s+\w+\s+ON'
        ]
        
        sql_content = []
        for pattern in sql_patterns:
            matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
            sql_content.extend(matches)
        
        # 获取主体内容
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        if main_content:
            # 移除脚本和样式
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            body_text = main_content.get_text().strip()
        else:
            body_text = soup.get_text().strip()
        
        # 合并所有内容
        all_parts = [
            body_text, 
            code_content, 
            '\n'.join(config_content), 
            '\n'.join(api_content),
            '\n'.join(java_content),
            '\n'.join(sql_content)
        ]
        combined_content = '\n'.join(filter(None, all_parts))
        
        # 清理多余空白
        combined_content = re.sub(r'\n\s*\n', '\n\n', combined_content)
        
        return combined_content[:10000]  # 限制长度
    
    async def crawl_url(self, url: str, tech_stack: str, max_depth: int = 3, current_depth: int = 0) -> List[Dict[str, Any]]:
        """爬取单个URL"""
        if current_depth > max_depth or url in self.visited_urls:
            return []
        
        # 跳过二进制文件
        if self.is_binary_url(url):
            logger.debug(f"跳过二进制URL: {url}")
            return []
        
        self.visited_urls.add(url)
        documents = []
        
        try:
            html = await self.fetch_html(url)
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else '无标题'
            
            # 限制标题长度
            if len(title_text) > 200:
                title_text = title_text[:200] + "..."
            
            # 提取内容
            content = self.extract_technical_content(soup)
            
            # 如果内容相关，保存文档
            if content and self.is_relevant_content(content, tech_stack):
                doc_id = hashlib.md5(f"{url}_{tech_stack}".encode()).hexdigest()
                
                document = {
                    'id': doc_id,
                    'url': url,
                    'title': title_text,
                    'content': content,
                    'tech_stack': tech_stack,
                    'category': self.determine_category(content),
                    'source': '深度爬取',
                    'language': '中文' if any('\u4e00' <= char <= '\u9fff' for char in content[:1000]) else '英文',
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'depth': current_depth,
                    'relevance_score': self.calculate_relevance_score(content, tech_stack)
                }
                
                documents.append(document)
                logger.info(f"深度 {current_depth}: 爬取到相关文档 - {title_text}")
            
            # 如果是深度爬取，继续爬取链接
            if current_depth < max_depth and len(documents) > 0:  # 只爬取相关页面的链接
                links = soup.find_all('a', href=True)
                link_tasks = []
                
                for link in links[:15]:  # 增加链接数量
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    # 只爬取同域名链接，且不重复
                    if (urlparse(full_url).netloc == urlparse(url).netloc and 
                        full_url not in self.visited_urls and
                        not self.is_binary_url(full_url)):
                        task = self.crawl_url(full_url, tech_stack, max_depth, current_depth + 1)
                        link_tasks.append(task)
                
                # 并行爬取链接，但限制并发数
                if link_tasks:
                    # 分批处理，避免过多并发
                    batch_size = 5
                    for i in range(0, len(link_tasks), batch_size):
                        batch = link_tasks[i:i+batch_size]
                        results = await asyncio.gather(*batch, return_exceptions=True)
                        for result in results:
                            if isinstance(result, list):
                                documents.extend(result)
                
        except Exception as e:
            logger.warning(f"爬取失败 {url}: {e}")
        
        return documents
    
    def determine_category(self, content: str) -> str:
        """确定文档类别"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in self.config_keywords):
            return 'CONFIGURATION'
        elif any(keyword in content_lower for keyword in self.api_keywords):
            return 'API_REFERENCE'
        elif any(keyword in content_lower for keyword in self.advanced_topics):
            return 'ADVANCED'
        else:
            return 'GENERAL'
    
    def calculate_relevance_score(self, content: str, tech_stack: str) -> float:
        """计算内容相关性得分"""
        score = 0.0
        content_lower = content.lower()
        
        # 配置相关得分
        config_count = sum(1 for keyword in self.config_keywords if keyword in content_lower)
        score += min(config_count * 0.3, 1.0)
        
        # API相关得分
        api_count = sum(1 for keyword in self.api_keywords if keyword in content_lower)
        score += min(api_count * 0.3, 1.0)
        
        # 高级主题得分
        advanced_count = sum(1 for keyword in self.advanced_topics if keyword in content_lower)
        score += min(advanced_count * 0.2, 0.5)
        
        # 技术栈特定得分
        tech_count = sum(1 for keyword in self.tech_keywords.get(tech_stack, []) if keyword in content_lower)
        score += min(tech_count * 0.2, 0.5)
        
        return min(score, 1.0)
    
    async def deep_crawl_tech_stack(self, tech_stack: str) -> List[Dict[str, Any]]:
        """深度爬取特定技术栈"""
        logger.info(f"开始深度爬取 {tech_stack}")
        
        documents = []
        urls = self.tech_stack_deep_urls.get(tech_stack, [])
        
        # 添加基础URL
        base_urls = {
            'spring-boot': 'https://springdoc.cn/',
            'docker': 'https://docs.docker.com/',
            'python': 'https://docs.python.org/zh-cn/3/',
            'vue': 'https://cn.vuejs.org/',
            'java': 'https://docs.oracle.com/en/java/javase/17/',
            'redis': 'https://redis.io/docs/',
            'mysql': 'https://dev.mysql.com/doc/refman/8.0/en/',
            'react': 'https://react.dev/'
        }
        
        if tech_stack in base_urls:
            urls.insert(0, base_urls[tech_stack])
        
        # 并行爬取所有URL，但限制并发数
        results = []
        batch_size = 2
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            tasks = [self.crawl_url(url, tech_stack, max_depth=2) for url in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            await asyncio.sleep(1)  # 避免请求过快
        
        for result in results:
            if isinstance(result, list):
                documents.extend(result)
        
        # 去重（基于URL）
        unique_docs = {}
        for doc in documents:
            if doc['url'] not in unique_docs:
                unique_docs[doc['url']] = doc
        
        documents = list(unique_docs.values())
        
        logger.info(f"{tech_stack} 深度爬取完成，获取 {len(documents)} 个文档")
        return documents
    
    async def run_advanced_crawling(self, tech_stacks: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """运行高级爬取
        
        Args:
            tech_stacks: 要爬取的技术栈列表，默认为所有支持的技术栈
        """
        await self.init_session()
        
        if tech_stacks is None:
            tech_stacks = ['spring-boot', 'docker', 'python', 'vue', 'java', 'redis', 'mysql', 'react']
        
        all_documents = {}
        
        try:
            # 串行爬取技术栈，避免过大压力
            for tech_stack in tech_stacks:
                logger.info(f"开始爬取技术栈: {tech_stack}")
                docs = await self.deep_crawl_tech_stack(tech_stack)
                all_documents[tech_stack] = docs
                await asyncio.sleep(2)  # 技术栈之间间隔
        
        finally:
            await self.close_session()
        
        return all_documents

async def main():
    """主函数"""
    crawler = AdvancedTechCrawler()
    
    print("=" * 70)
    print("高级技术文档深度爬取工具 - 支持多技术栈")
    print("=" * 70)
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 可以选择要爬取的技术栈
        tech_stacks = ['java', 'redis', 'mysql', 'react', 'spring-boot', 'python', 'docker', 'vue']
        
        print(f"\n准备爬取的技术栈: {', '.join(tech_stacks)}")
        print("=" * 70)
        
        # 运行深度爬取
        documents = await crawler.run_advanced_crawling(tech_stacks)
        
        # 保存结果
        for tech_stack, docs in documents.items():
            if docs:  # 只保存非空结果
                filename = f"advanced_{tech_stack}_docs.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
                
                # 统计信息
                avg_score = sum(doc['relevance_score'] for doc in docs) / len(docs)
                categories = {}
                for doc in docs:
                    cat = doc['category']
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"\n✅ {tech_stack.upper()}:")
                print(f"   - 文档数: {len(docs)}")
                print(f"   - 平均相关性: {avg_score:.2f}")
                print(f"   - 分类: {categories}")
                print(f"   - 保存到: {filename}")
            else:
                print(f"\n⚠️ {tech_stack.upper()}: 未获取到文档")
        
        # 总体统计信息
        total_docs = sum(len(docs) for docs in documents.values())
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("深度爬取完成!")
        print(f"总文档数: {total_docs}")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"平均速度: {total_docs/duration:.2f} 文档/秒" if total_docs > 0 else "")
        print("\n爬取特性:")
        print("• 支持 Java、Redis、MySQL、React 等技术栈")
        print("• 专门针对配置问题和API接口")
        print("• 深度爬取高级技术主题")
        print("• 智能内容相关性评分")
        print("• 自动分类和去重")
        print("• 二进制文件过滤")
        print("• 多编码支持")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())