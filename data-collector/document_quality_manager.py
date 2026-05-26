#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档质量管理和去重工具
"""

import json
import hashlib
import re
from typing import List, Dict, Any, Set
from collections import defaultdict
import jieba
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentQualityManager:
    """文档质量管理和去重工具"""
    
    def __init__(self):
        # 初始化中文分词
        jieba.initialize()
        
        # 质量评估参数
        self.quality_weights = {
            'content_length': 0.2,      # 内容长度
            'technical_keywords': 0.3, # 技术关键词密度
            'code_examples': 0.25,      # 代码示例
            'structure_quality': 0.15, # 结构质量
            'language_quality': 0.1    # 语言质量
        }
        
        # 技术关键词库
        self.technical_keywords = {
            'spring-boot': ['Spring', 'Boot', 'Bean', 'Autowired', 'Controller', 'Service', 'Repository',
                           'Configuration', 'Properties', 'YAML', 'Annotation', 'Dependency', 'Maven', 'Gradle'],
            'docker': ['Docker', 'Container', 'Image', 'Compose', 'Swarm', 'Registry', 'Volume', 'Network',
                      'Dockerfile', 'Build', 'Run', 'Exec', 'Logs', 'Port'],
            'python': ['Python', 'Import', 'Def', 'Class', 'Module', 'Package', 'Function', 'Method',
                      'List', 'Dict', 'Tuple', 'Set', 'Lambda', 'Decorator'],
            'vue': ['Vue', 'Component', 'Props', 'Emit', 'Router', 'Store', 'State', 'Mutation',
                   'Action', 'Getter', 'Directive', 'Filter', 'Mixin', 'Plugin']
        }
    
    def calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值用于去重"""
        # 预处理内容：去除空格、标点，转换为小写
        cleaned_content = re.sub(r'[\s\p{P}]', '', content).lower()
        return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
    
    def remove_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复文档"""
        logger.info("开始文档去重处理...")
        
        seen_hashes: Set[str] = set()
        unique_documents = []
        
        for doc in documents:
            content_hash = self.calculate_content_hash(doc['content'])
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_documents.append(doc)
            else:
                logger.debug(f"发现重复文档: {doc.get('title', '无标题')}")
        
        logger.info(f"去重完成: {len(documents)} -> {len(unique_documents)} 个文档")
        return unique_documents
    
    def calculate_content_length_score(self, content: str) -> float:
        """计算内容长度得分"""
        length = len(content.strip())
        
        # 长度评分标准
        if length < 100:
            return 0.1  # 太短
        elif length < 500:
            return 0.5  # 适中
        elif length < 2000:
            return 0.9  # 良好
        else:
            return 1.0  # 优秀
    
    def calculate_technical_keywords_score(self, content: str, tech_stack: str) -> float:
        """计算技术关键词得分"""
        keywords = self.technical_keywords.get(tech_stack, [])
        
        if not keywords:
            return 0.5  # 默认得分
        
        # 使用jieba分词
        words = jieba.lcut(content)
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        # 统计关键词出现次数
        keyword_count = sum(1 for word in words if word in keywords)
        keyword_density = keyword_count / total_words
        
        # 密度评分
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
        # 检测代码块
        code_patterns = [
            r'```[\s\S]*?```',  # Markdown代码块
            r'<code>[\s\S]*?</code>',  # HTML代码标签
            r'<pre>[\s\S]*?</pre>',  # HTML预格式化
            r'\b(public|private|def|class|import|from|function|var|let|const)\b'  # 编程语言关键词
        ]
        
        code_count = 0
        for pattern in code_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            code_count += len(matches)
        
        # 代码示例评分
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
        # 检测结构化内容
        structure_indicators = [
            r'^#+\s',  # 标题
            r'\d+\.\s',  # 编号列表
            r'-\s',  # 项目符号
            r'\n\n',  # 段落分隔
            r'表格',  # 表格
            r'图\s*\d+'  # 图表引用
        ]
        
        structure_count = 0
        for pattern in structure_indicators:
            matches = re.findall(pattern, content, re.MULTILINE)
            structure_count += len(matches)
        
        # 结构质量评分
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
        # 检测语言质量问题
        quality_issues = [
            r'[a-zA-Z]{20,}',  # 长英文单词（可能是乱码）
            r'[\x00-\x1f\x7f-\x9f]',  # 控制字符
            r'[\u4e00-\u9fff]{1}[\x00-\x7f]{1}[\u4e00-\u9fff]{1}',  # 中英混合乱序
            r'重复{3,}',  # 重复字符
        ]
        
        issue_count = 0
        for pattern in quality_issues:
            matches = re.findall(pattern, content)
            issue_count += len(matches)
        
        # 语言质量评分（问题越少得分越高）
        if issue_count == 0:
            return 1.0
        elif issue_count <= 2:
            return 0.8
        elif issue_count <= 5:
            return 0.5
        else:
            return 0.2
    
    def assess_document_quality(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个文档质量"""
        content = document.get('content', '')
        tech_stack = document.get('tech_stack', '')
        
        # 计算各项得分
        scores = {
            'content_length': self.calculate_content_length_score(content),
            'technical_keywords': self.calculate_technical_keywords_score(content, tech_stack),
            'code_examples': self.calculate_code_examples_score(content),
            'structure_quality': self.calculate_structure_quality_score(content),
            'language_quality': self.calculate_language_quality_score(content)
        }
        
        # 计算综合得分
        total_score = sum(scores[category] * weight 
                         for category, weight in self.quality_weights.items())
        
        # 确定质量等级
        if total_score >= 0.8:
            quality_level = '优秀'
        elif total_score >= 0.6:
            quality_level = '良好'
        elif total_score >= 0.4:
            quality_level = '一般'
        else:
            quality_level = '较差'
        
        return {
            'total_score': round(total_score, 3),
            'quality_level': quality_level,
            'detailed_scores': scores,
            'assessment': self.generate_quality_assessment(scores, total_score)
        }
    
    def generate_quality_assessment(self, scores: Dict[str, float], total_score: float) -> str:
        """生成质量评估描述"""
        assessments = []
        
        if scores['content_length'] < 0.3:
            assessments.append("内容过短")
        elif scores['content_length'] > 0.8:
            assessments.append("内容丰富")
        
        if scores['technical_keywords'] < 0.3:
            assessments.append("技术内容较少")
        elif scores['technical_keywords'] > 0.8:
            assessments.append("技术内容充实")
        
        if scores['code_examples'] < 0.3:
            assessments.append("缺少代码示例")
        elif scores['code_examples'] > 0.8:
            assessments.append("代码示例丰富")
        
        if scores['structure_quality'] < 0.3:
            assessments.append("结构不够清晰")
        elif scores['structure_quality'] > 0.8:
            assessments.append("结构清晰")
        
        if scores['language_quality'] < 0.3:
            assessments.append("语言质量有待提高")
        elif scores['language_quality'] > 0.8:
            assessments.append("语言表达良好")
        
        if not assessments:
            return "文档质量均衡"
        
        return ", ".join(assessments)
    
    def filter_low_quality_documents(self, documents: List[Dict[str, Any]], 
                                   min_score: float = 0.4) -> List[Dict[str, Any]]:
        """过滤低质量文档"""
        logger.info(f"开始过滤低质量文档 (阈值: {min_score})...")
        
        filtered_documents = []
        quality_stats = defaultdict(int)
        
        for doc in documents:
            quality_info = self.assess_document_quality(doc)
            
            # 添加质量信息到文档
            doc['quality_score'] = quality_info['total_score']
            doc['quality_level'] = quality_info['quality_level']
            doc['quality_assessment'] = quality_info['assessment']
            
            # 统计质量分布
            quality_stats[quality_info['quality_level']] += 1
            
            # 过滤低质量文档
            if quality_info['total_score'] >= min_score:
                filtered_documents.append(doc)
            else:
                logger.debug(f"过滤低质量文档: {doc.get('title', '无标题')} - 得分: {quality_info['total_score']}")
        
        logger.info(f"质量过滤完成: {len(documents)} -> {len(filtered_documents)} 个文档")
        logger.info(f"质量分布: {dict(quality_stats)}")
        
        return filtered_documents
    
    def generate_quality_report(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成质量报告"""
        total_docs = len(documents)
        
        if total_docs == 0:
            return {"error": "没有文档可分析"}
        
        # 统计质量分布
        quality_distribution = defaultdict(int)
        tech_stack_distribution = defaultdict(int)
        category_distribution = defaultdict(int)
        
        total_score_sum = 0.0
        
        for doc in documents:
            quality_info = self.assess_document_quality(doc)
            
            quality_distribution[quality_info['quality_level']] += 1
            tech_stack_distribution[doc.get('tech_stack', '未知')] += 1
            category_distribution[doc.get('category', '未知')] += 1
            total_score_sum += quality_info['total_score']
        
        avg_score = total_score_sum / total_docs
        
        # 生成报告
        report = {
            "total_documents": total_docs,
            "average_quality_score": round(avg_score, 3),
            "quality_distribution": dict(quality_distribution),
            "tech_stack_distribution": dict(tech_stack_distribution),
            "category_distribution": dict(category_distribution),
            "recommendations": self.generate_recommendations(quality_distribution, avg_score)
        }
        
        return report
    
    def generate_recommendations(self, quality_distribution: Dict[str, int], 
                               avg_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if avg_score < 0.6:
            recommendations.append("建议补充更多技术内容和代码示例")
        
        poor_count = quality_distribution.get('较差', 0)
        if poor_count > 0:
            recommendations.append(f"发现 {poor_count} 个低质量文档，建议重新爬取或过滤")
        
        excellent_count = quality_distribution.get('优秀', 0)
        if excellent_count < quality_distribution.get('一般', 0):
            recommendations.append("高质量文档比例较低，建议优化爬取策略")
        
        if not recommendations:
            recommendations.append("文档质量良好，继续保持当前策略")
        
        return recommendations
    
    def process_document_collection(self, input_file: str, output_file: str, 
                                  min_quality_score: float = 0.4) -> Dict[str, Any]:
        """处理整个文档集合"""
        logger.info(f"开始处理文档集合: {input_file}")
        
        try:
            # 读取文档
            with open(input_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"原始文档数量: {len(documents)}")
            
            # 去重处理
            unique_documents = self.remove_duplicates(documents)
            
            # 质量过滤
            filtered_documents = self.filter_low_quality_documents(unique_documents, min_quality_score)
            
            # 生成质量报告
            quality_report = self.generate_quality_report(filtered_documents)
            
            # 保存处理后的文档
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_documents, f, ensure_ascii=False, indent=2)
            
            logger.info(f"处理完成: 保存 {len(filtered_documents)} 个文档到 {output_file}")
            
            return {
                "success": True,
                "original_count": len(documents),
                "final_count": len(filtered_documents),
                "quality_report": quality_report
            }
            
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return {"success": False, "error": str(e)}

def main():
    """主函数"""
    manager = DocumentQualityManager()
    
    print("=" * 60)
    print("文档质量管理和去重工具")
    print("=" * 60)
    
    # 处理所有技术栈的文档
    tech_stacks = ['spring-boot', 'docker', 'python', 'vue', 'react', 'redis', 'mysql', 'java']
    
    for tech_stack in tech_stacks:
        input_file = f"chinese_tech_docs/{tech_stack}_chinese_docs.json"
        output_file = f"chinese_tech_docs/{tech_stack}_chinese_docs_cleaned.json"
        
        print(f"\n处理 {tech_stack} 文档...")
        result = manager.process_document_collection(input_file, output_file)
        
        if result['success']:
            print(f"✅ {tech_stack}: {result['original_count']} -> {result['final_count']} 个文档")
            report = result['quality_report']
            print(f"   平均质量分: {report['average_quality_score']}")
            print(f"   质量分布: {report['quality_distribution']}")
        else:
            print(f"❌ {tech_stack}: 处理失败 - {result['error']}")
    
    print("\n" + "=" * 60)
    print("文档质量管理和去重完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()