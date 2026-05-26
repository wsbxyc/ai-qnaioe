#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档整合优化工具 - 实现去重、分类、质量评估和语言优化
"""

import json
import hashlib
import re
import os
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import jieba
import logging
from googletrans import Translator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentIntegrationOptimizer:
    """文档整合优化工具"""
    
    def __init__(self):
        # 初始化中文分词
        jieba.initialize()
        
        # 初始化翻译器
        self.translator = Translator()
        
        # 技术主题分类
        self.tech_themes = {
            'spring-boot': {
                '基础概念': ['spring', 'boot', '概念', '介绍', '入门'],
                '配置管理': ['配置', 'properties', 'yml', 'yaml', '环境变量', '参数'],
                'API接口': ['api', '接口', 'controller', 'service', 'rest', 'endpoint'],
                '安全认证': ['安全', '认证', '授权', 'oauth', 'jwt', 'security'],
                '性能优化': ['性能', '优化', '缓存', '并发', '调优'],
                '高级特性': ['高级', '进阶', '源码', '原理', '设计模式']
            },
            'docker': {
                '基础概念': ['docker', '容器', '镜像', '概念', '介绍'],
                '配置管理': ['配置', 'dockerfile', 'compose', '环境变量', '参数'],
                'API接口': ['api', '接口', 'cli', '命令', 'reference'],
                '网络存储': ['网络', '存储', 'volume', 'network', '数据持久化'],
                '安全部署': ['安全', '部署', '生产', '监控', '日志'],
                '高级特性': ['高级', 'swarm', 'kubernetes', '编排', '集群']
            },
            'python': {
                '基础语法': ['python', '语法', '基础', '入门', '数据类型'],
                '配置管理': ['配置', '环境', '包管理', 'pip', 'requirements'],
                'API接口': ['api', '接口', '模块', '库', 'import'],
                '高级特性': ['高级', '进阶', '装饰器', '生成器', '元类'],
                '性能优化': ['性能', '优化', '并发', '异步', '多线程'],
                '应用开发': ['web', '数据分析', '机器学习', '自动化']
            },
            'vue': {
                '基础概念': ['vue', '概念', '介绍', '入门', '组件'],
                '配置管理': ['配置', 'vue.config', '环境变量', '参数'],
                'API接口': ['api', '接口', '组件', '指令', '插件'],
                '状态管理': ['状态', 'vuex', 'pinia', '数据流'],
                '路由导航': ['路由', 'router', '导航', '页面'],
                '高级特性': ['高级', '进阶', '源码', '性能', '优化']
            }
        }
        
        # 质量评估权重
        self.quality_weights = {
            'content_length': 0.2,
            'technical_keywords': 0.3,
            'code_examples': 0.25,
            'structure_quality': 0.15,
            'language_quality': 0.1
        }
        
        # 相关性评估权重
        self.relevance_weights = {
            'theme_match': 0.4,
            'keyword_density': 0.3,
            'content_freshness': 0.2,
            'source_authority': 0.1
        }
    
    def load_documents(self, tech_stack: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """加载原始文档和高级文档"""
        original_file = f"chinese_tech_docs/{tech_stack}_chinese_docs.json"
        advanced_file = f"advanced_{tech_stack}_docs.json"
        
        original_docs = []
        advanced_docs = []
        
        # 加载原始文档
        if os.path.exists(original_file):
            with open(original_file, 'r', encoding='utf-8') as f:
                original_docs = json.load(f)
        
        # 加载高级文档
        if os.path.exists(advanced_file):
            with open(advanced_file, 'r', encoding='utf-8') as f:
                advanced_docs = json.load(f)
        
        logger.info(f"加载 {tech_stack}: 原始文档 {len(original_docs)} 个, 高级文档 {len(advanced_docs)} 个")
        return original_docs, advanced_docs
    
    def calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值用于去重"""
        # 预处理内容：去除空格、标点，转换为小写
        cleaned_content = re.sub(r'[\s\W_]', '', content).lower()
        return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
    
    def remove_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除完全重复的内容"""
        logger.info("开始去重处理...")
        
        seen_hashes: Set[str] = set()
        unique_documents = []
        duplicate_count = 0
        
        for doc in documents:
            content_hash = self.calculate_content_hash(doc['content'])
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_documents.append(doc)
            else:
                duplicate_count += 1
                logger.debug(f"发现重复文档: {doc.get('title', '无标题')}")
        
        logger.info(f"去重完成: {len(documents)} -> {len(unique_documents)} 个文档, 去除 {duplicate_count} 个重复")
        return unique_documents
    
    def classify_by_theme(self, document: Dict[str, Any], tech_stack: str) -> str:
        """按技术主题分类文档"""
        content = document.get('content', '').lower()
        title = document.get('title', '').lower()
        
        full_text = title + ' ' + content
        
        # 获取技术栈的主题分类
        themes = self.tech_themes.get(tech_stack, {})
        
        theme_scores = {}
        
        for theme, keywords in themes.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in full_text:
                    score += 1
            theme_scores[theme] = score
        
        # 选择得分最高的主题
        if theme_scores:
            best_theme = max(theme_scores.items(), key=lambda x: x[1])
            if best_theme[1] > 0:
                return best_theme[0]
        
        # 默认分类
        return '其他'
    
    def assess_document_quality(self, document: Dict[str, Any]) -> float:
        """评估文档质量"""
        content = document.get('content', '')
        
        # 计算各项得分
        scores = {
            'content_length': self.calculate_content_length_score(content),
            'technical_keywords': self.calculate_technical_keywords_score(content),
            'code_examples': self.calculate_code_examples_score(content),
            'structure_quality': self.calculate_structure_quality_score(content),
            'language_quality': self.calculate_language_quality_score(content)
        }
        
        # 计算综合质量得分
        total_score = sum(scores[category] * weight 
                         for category, weight in self.quality_weights.items())
        
        return round(total_score, 3)
    
    def calculate_content_length_score(self, content: str) -> float:
        """计算内容长度得分"""
        length = len(content.strip())
        
        if length < 100:
            return 0.1
        elif length < 500:
            return 0.5
        elif length < 2000:
            return 0.9
        else:
            return 1.0
    
    def calculate_technical_keywords_score(self, content: str) -> float:
        """计算技术关键词得分"""
        # 技术关键词模式
        tech_patterns = [
            r'\b(config|配置|参数|setting|环境变量)\b',
            r'\b(api|接口|endpoint|controller|service)\b',
            r'\b(性能|优化|缓存|并发|security|安全)\b',
            r'\b(代码|示例|example|demo|实例)\b'
        ]
        
        keyword_count = 0
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keyword_count += len(matches)
        
        # 关键词密度评分
        words = jieba.lcut(content)
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        keyword_density = keyword_count / total_words
        
        if keyword_density < 0.01:
            return 0.2
        elif keyword_density < 0.03:
            return 0.5
        elif keyword_density < 0.05:
            return 0.8
        else:
            return 1.0
    
    def calculate_code_examples_score(self, content: str) -> float:
        """计算代码示例得分"""
        code_patterns = [
            r'```[\s\S]*?```',
            r'<code>[\s\S]*?</code>',
            r'<pre>[\s\S]*?</pre>',
            r'\b(public|private|def|class|import|from|function|var|let|const)\b'
        ]
        
        code_count = 0
        for pattern in code_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            code_count += len(matches)
        
        if code_count == 0:
            return 0.1
        elif code_count == 1:
            return 0.5
        elif code_count <= 3:
            return 0.8
        else:
            return 1.0
    
    def calculate_structure_quality_score(self, content: str) -> float:
        """计算结构质量得分"""
        structure_indicators = [
            r'^#+\s',
            r'\d+\.\s',
            r'-\s',
            r'\n\n',
            r'表格',
            r'图\s*\d+'
        ]
        
        structure_count = 0
        for pattern in structure_indicators:
            matches = re.findall(pattern, content, re.MULTILINE)
            structure_count += len(matches)
        
        if structure_count < 3:
            return 0.3
        elif structure_count < 6:
            return 0.6
        elif structure_count < 10:
            return 0.8
        else:
            return 1.0
    
    def calculate_language_quality_score(self, content: str) -> float:
        """计算语言质量得分"""
        quality_issues = [
            r'[a-zA-Z]{20,}',
            r'[\x00-\x1f\x7f-\x9f]',
            r'[\u4e00-\u9fff]{1}[\x00-\x7f]{1}[\u4e00-\u9fff]{1}',
            r'重复{3,}',
        ]
        
        issue_count = 0
        for pattern in quality_issues:
            matches = re.findall(pattern, content)
            issue_count += len(matches)
        
        if issue_count == 0:
            return 1.0
        elif issue_count <= 2:
            return 0.8
        elif issue_count <= 5:
            return 0.5
        else:
            return 0.2
    
    def calculate_relevance_score(self, document: Dict[str, Any], tech_stack: str) -> float:
        """计算文档相关性得分"""
        content = document.get('content', '').lower()
        
        # 主题匹配得分
        theme = self.classify_by_theme(document, tech_stack)
        theme_match_score = 1.0 if theme != '其他' else 0.3
        
        # 关键词密度得分
        keywords = self.tech_themes.get(tech_stack, {})
        all_keywords = []
        for theme_keywords in keywords.values():
            all_keywords.extend(theme_keywords)
        
        keyword_count = sum(1 for keyword in all_keywords if keyword.lower() in content)
        words = jieba.lcut(content)
        total_words = len(words)
        
        keyword_density_score = min(keyword_count / max(total_words, 1) * 10, 1.0)
        
        # 内容新鲜度得分（基于URL）
        url = document.get('url', '')
        freshness_score = 0.7  # 默认得分
        if '202' in url or 'latest' in url:
            freshness_score = 1.0
        
        # 来源权威性得分
        source = document.get('source', '').lower()
        authority_score = 0.5
        if '官方' in source or 'official' in source:
            authority_score = 1.0
        elif '教程' in source or 'tutorial' in source:
            authority_score = 0.8
        
        # 计算综合相关性得分
        relevance_score = (
            theme_match_score * self.relevance_weights['theme_match'] +
            keyword_density_score * self.relevance_weights['keyword_density'] +
            freshness_score * self.relevance_weights['content_freshness'] +
            authority_score * self.relevance_weights['source_authority']
        )
        
        return round(relevance_score, 3)
    
    def translate_important_english_content(self, content: str) -> str:
        """对重要英文内容进行中文翻译"""
        # 检测是否为英文内容
        english_ratio = len(re.findall(r'[a-zA-Z]', content)) / max(len(content), 1)
        
        if english_ratio < 0.3:
            return content  # 主要是中文内容，不需要翻译
        
        # 提取重要段落进行翻译
        important_sections = []
        
        # 检测代码块和配置内容
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        config_blocks = re.findall(r'\b(config|配置|setting)[\s\S]{1,200}', content, re.IGNORECASE)
        
        # 检测技术说明段落
        paragraphs = re.split(r'\n\n+', content)
        
        for para in paragraphs:
            # 判断段落是否重要（包含技术关键词）
            tech_keywords = ['config', 'api', 'parameter', 'setting', 'configuration']
            if any(keyword in para.lower() for keyword in tech_keywords):
                important_sections.append(para)
        
        # 限制翻译内容长度
        translation_content = ' '.join(important_sections[:3])
        if len(translation_content) > 1000:
            translation_content = translation_content[:1000]
        
        if translation_content:
            try:
                translated = self.translator.translate(translation_content, dest='zh-cn')
                # 在原文后添加翻译
                content += f"\n\n[中文翻译]\n{translated.text}"
                logger.info("已添加重要英文内容的中文翻译")
            except Exception as e:
                logger.warning(f"翻译失败: {e}")
        
        return content
    
    def optimize_document(self, document: Dict[str, Any], tech_stack: str) -> Dict[str, Any]:
        """优化单个文档"""
        # 计算质量和相关性得分
        quality_score = self.assess_document_quality(document)
        relevance_score = self.calculate_relevance_score(document, tech_stack)
        
        # 分类主题
        theme = self.classify_by_theme(document, tech_stack)
        
        # 语言优化
        optimized_content = self.translate_important_english_content(document['content'])
        
        # 更新文档信息
        optimized_doc = document.copy()
        optimized_doc.update({
            'quality_score': quality_score,
            'relevance_score': relevance_score,
            'theme': theme,
            'content': optimized_content,
            'optimized': True
        })
        
        return optimized_doc
    
    def integrate_and_optimize(self, tech_stack: str) -> Dict[str, Any]:
        """整合和优化特定技术栈的文档"""
        logger.info(f"开始整合优化 {tech_stack} 文档...")
        
        # 加载文档
        original_docs, advanced_docs = self.load_documents(tech_stack)
        
        # 合并文档
        all_docs = original_docs + advanced_docs
        logger.info(f"合并后文档总数: {len(all_docs)}")
        
        # 去重处理
        unique_docs = self.remove_duplicates(all_docs)
        
        # 优化每个文档
        optimized_docs = []
        for doc in unique_docs:
            optimized_doc = self.optimize_document(doc, tech_stack)
            optimized_docs.append(optimized_doc)
        
        # 按质量和相关性排序
        optimized_docs.sort(key=lambda x: (x['relevance_score'], x['quality_score']), reverse=True)
        
        # 按主题分类组织
        themed_docs = defaultdict(list)
        for doc in optimized_docs:
            themed_docs[doc['theme']].append(doc)
        
        # 生成优化报告
        report = self.generate_optimization_report(optimized_docs, tech_stack)
        
        # 保存优化后的文档
        output_file = f"chinese_tech_docs/{tech_stack}_chinese_docs_optimized.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_docs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"{tech_stack} 文档优化完成，保存到 {output_file}")
        
        return {
            'tech_stack': tech_stack,
            'original_count': len(original_docs),
            'advanced_count': len(advanced_docs),
            'optimized_count': len(optimized_docs),
            'themes_count': len(themed_docs),
            'report': report
        }
    
    def generate_optimization_report(self, documents: List[Dict[str, Any]], tech_stack: str) -> Dict[str, Any]:
        """生成优化报告"""
        total_docs = len(documents)
        
        if total_docs == 0:
            return {"error": "没有文档可分析"}
        
        # 统计质量分布
        quality_distribution = defaultdict(int)
        relevance_distribution = defaultdict(int)
        theme_distribution = defaultdict(int)
        
        total_quality_score = 0.0
        total_relevance_score = 0.0
        
        for doc in documents:
            quality_score = doc.get('quality_score', 0)
            relevance_score = doc.get('relevance_score', 0)
            theme = doc.get('theme', '其他')
            
            # 质量等级
            if quality_score >= 0.8:
                quality_level = '优秀'
            elif quality_score >= 0.6:
                quality_level = '良好'
            elif quality_score >= 0.4:
                quality_level = '一般'
            else:
                quality_level = '较差'
            
            # 相关性等级
            if relevance_score >= 0.8:
                relevance_level = '高'
            elif relevance_score >= 0.6:
                relevance_level = '中'
            else:
                relevance_level = '低'
            
            quality_distribution[quality_level] += 1
            relevance_distribution[relevance_level] += 1
            theme_distribution[theme] += 1
            
            total_quality_score += quality_score
            total_relevance_score += relevance_score
        
        avg_quality = total_quality_score / total_docs
        avg_relevance = total_relevance_score / total_docs
        
        return {
            'total_documents': total_docs,
            'average_quality_score': round(avg_quality, 3),
            'average_relevance_score': round(avg_relevance, 3),
            'quality_distribution': dict(quality_distribution),
            'relevance_distribution': dict(relevance_distribution),
            'theme_distribution': dict(theme_distribution),
            'improvement_suggestions': self.generate_improvement_suggestions(quality_distribution, theme_distribution)
        }
    
    def generate_improvement_suggestions(self, quality_dist: Dict[str, int], theme_dist: Dict[str, int]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 质量改进建议
        poor_count = quality_dist.get('较差', 0)
        if poor_count > len(quality_dist) * 0.2:
            suggestions.append("建议过滤或重新爬取低质量文档")
        
        excellent_count = quality_dist.get('优秀', 0)
        if excellent_count < len(quality_dist) * 0.3:
            suggestions.append("建议补充更多高质量技术文档")
        
        # 主题覆盖建议
        if '其他' in theme_dist and theme_dist['其他'] > len(theme_dist) * 0.3:
            suggestions.append("建议优化主题分类算法，减少'其他'分类")
        
        if not suggestions:
            suggestions.append("文档质量良好，继续保持")
        
        return suggestions
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """运行完整的文档优化流程"""
        logger.info("开始完整的文档整合优化流程...")
        
        tech_stacks = ['spring-boot', 'docker', 'python', 'vue']
        optimization_results = {}
        
        for tech_stack in tech_stacks:
            try:
                result = self.integrate_and_optimize(tech_stack)
                optimization_results[tech_stack] = result
                logger.info(f"{tech_stack} 优化完成")
            except Exception as e:
                logger.error(f"{tech_stack} 优化失败: {e}")
                optimization_results[tech_stack] = {
                    'error': str(e),
                    'success': False
                }
        
        # 生成总体报告
        overall_report = self.generate_overall_report(optimization_results)
        
        # 保存总体报告
        with open("document_optimization_report.json", 'w', encoding='utf-8') as f:
            json.dump({
                'optimization_results': optimization_results,
                'overall_report': overall_report
            }, f, ensure_ascii=False, indent=2)
        
        logger.info("完整的文档整合优化流程完成")
        return optimization_results
    
    def generate_overall_report(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成总体报告"""
        total_original = 0
        total_advanced = 0
        total_optimized = 0
        total_themes = 0
        
        successful_optimizations = 0
        
        for tech_stack, result in optimization_results.items():
            if result.get('success', True):
                total_original += result.get('original_count', 0)
                total_advanced += result.get('advanced_count', 0)
                total_optimized += result.get('optimized_count', 0)
                total_themes += result.get('themes_count', 0)
                successful_optimizations += 1
        
        return {
            'total_tech_stacks': len(optimization_results),
            'successful_optimizations': successful_optimizations,
            'total_original_documents': total_original,
            'total_advanced_documents': total_advanced,
            'total_optimized_documents': total_optimized,
            'average_documents_per_theme': round(total_optimized / max(total_themes, 1), 2),
            'improvement_rate': round((total_optimized - total_original) / max(total_original, 1) * 100, 2)
        }

def main():
    """主函数"""
    optimizer = DocumentIntegrationOptimizer()
    
    print("=" * 70)
    print("文档整合优化工具")
    print("=" * 70)
    
    print("\n优化步骤:")
    print("- 去重处理: 识别并去除完全重复的内容")
    print("- 分类整合: 按技术主题重新组织文档结构")
    print("- 质量评估: 基于相关性评分和质量评分排序")
    print("- 语言优化: 对重要英文内容进行中文翻译")
    
    print("\n开始优化流程...")
    
    try:
        results = optimizer.run_full_optimization()
        
        print("\n" + "=" * 70)
        print("优化完成!")
        print("=" * 70)
        
        # 显示优化结果
        for tech_stack, result in results.items():
            if result.get('success', True):
                print(f"[OK] {tech_stack}: {result['original_count']} + {result['advanced_count']} -> {result['optimized_count']} 个文档")
                report = result.get('report', {})
                print(f"     质量分: {report.get('average_quality_score', 0)}, 相关分: {report.get('average_relevance_score', 0)}")
            else:
                print(f"[ERROR] {tech_stack}: 优化失败 - {result.get('error', '未知错误')}")
        
        print("\n详细报告已保存到: document_optimization_report.json")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 优化流程失败: {e}")
        print("=" * 70)

if __name__ == "__main__":
    main()