#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档库优化执行脚本 - 整合深度爬取、去重和质量监控
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentOptimizationPipeline:
    """文档优化流水线"""
    
    def __init__(self):
        self.optimization_stats = {}
    
    async def run_advanced_crawling(self) -> Dict[str, Any]:
        """运行高级爬取"""
        logger.info("开始高级爬取阶段...")
        
        try:
            from advanced_crawler import AdvancedTechCrawler
            
            crawler = AdvancedTechCrawler()
            documents = await crawler.run_advanced_crawling()
            
            # 保存高级爬取结果
            advanced_docs_count = 0
            for tech_stack, docs in documents.items():
                filename = f"advanced_{tech_stack}_docs.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
                
                advanced_docs_count += len(docs)
                logger.info(f"保存 {tech_stack} 高级文档: {len(docs)} 个")
            
            return {
                "success": True,
                "documents_count": advanced_docs_count,
                "tech_stacks": list(documents.keys())
            }
            
        except Exception as e:
            logger.error(f"高级爬取失败: {e}")
            return {"success": False, "error": str(e)}
    
    def merge_documents(self, original_file: str, advanced_file: str, output_file: str) -> Dict[str, Any]:
        """合并原始文档和高级文档"""
        logger.info(f"合并文档: {original_file} + {advanced_file}")
        
        try:
            # 读取原始文档
            original_docs = []
            if os.path.exists(original_file):
                with open(original_file, 'r', encoding='utf-8') as f:
                    original_docs = json.load(f)
            
            # 读取高级文档
            advanced_docs = []
            if os.path.exists(advanced_file):
                with open(advanced_file, 'r', encoding='utf-8') as f:
                    advanced_docs = json.load(f)
            
            # 合并文档
            merged_docs = original_docs + advanced_docs
            
            # 保存合并结果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_docs, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "original_count": len(original_docs),
                "advanced_count": len(advanced_docs),
                "merged_count": len(merged_docs)
            }
            
        except Exception as e:
            logger.error(f"文档合并失败: {e}")
            return {"success": False, "error": str(e)}
    
    def run_quality_management(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """运行质量管理和去重"""
        logger.info(f"运行质量管理和去重: {input_file}")
        
        try:
            from document_quality_manager import DocumentQualityManager
            
            manager = DocumentQualityManager()
            result = manager.process_document_collection(input_file, output_file)
            
            return result
            
        except Exception as e:
            logger.error(f"质量管理失败: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "optimization_stats": self.optimization_stats,
            "summary": self.generate_summary()
        }
        
        # 保存报告
        with open("optimization_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成优化摘要"""
        total_original = 0
        total_final = 0
        total_advanced = 0
        
        for tech_stack, stats in self.optimization_stats.items():
            total_original += stats.get('original_count', 0)
            total_final += stats.get('final_count', 0)
            total_advanced += stats.get('advanced_count', 0)
        
        improvement_rate = ((total_final - total_original) / total_original * 100) if total_original > 0 else 0
        
        return {
            "total_original_documents": total_original,
            "total_final_documents": total_final,
            "total_advanced_documents": total_advanced,
            "improvement_rate": round(improvement_rate, 2),
            "optimized_tech_stacks": list(self.optimization_stats.keys())
        }
    
    async def optimize_tech_stack(self, tech_stack: str) -> Dict[str, Any]:
        """优化单个技术栈的文档库"""
        logger.info(f"开始优化 {tech_stack} 文档库...")
        
        optimization_result = {}
        
        try:
            # 文件路径
            original_file = f"chinese_tech_docs/{tech_stack}_chinese_docs.json"
            advanced_file = f"advanced_{tech_stack}_docs.json"
            merged_file = f"chinese_tech_docs/{tech_stack}_chinese_docs_merged.json"
            final_file = f"chinese_tech_docs/{tech_stack}_chinese_docs_optimized.json"
            
            # 步骤1: 高级爬取
            advanced_result = await self.run_advanced_crawling()
            optimization_result["advanced_crawling"] = advanced_result
            
            # 步骤2: 文档合并
            if os.path.exists(original_file):
                merge_result = self.merge_documents(original_file, advanced_file, merged_file)
                optimization_result["document_merging"] = merge_result
            else:
                # 如果没有原始文件，直接使用高级文档
                if os.path.exists(advanced_file):
                    os.rename(advanced_file, merged_file)
                optimization_result["document_merging"] = {"success": True, "note": "直接使用高级文档"}
            
            # 步骤3: 质量管理和去重
            if os.path.exists(merged_file):
                quality_result = self.run_quality_management(merged_file, final_file)
                optimization_result["quality_management"] = quality_result
            
            # 收集统计信息
            self.optimization_stats[tech_stack] = {
                "original_count": optimization_result.get("document_merging", {}).get("original_count", 0),
                "advanced_count": optimization_result.get("document_merging", {}).get("advanced_count", 0),
                "final_count": optimization_result.get("quality_management", {}).get("final_count", 0)
            }
            
            optimization_result["success"] = True
            
        except Exception as e:
            logger.error(f"优化 {tech_stack} 失败: {e}")
            optimization_result["success"] = False
            optimization_result["error"] = str(e)
        
        return optimization_result
    
    async def run_full_optimization(self) -> Dict[str, Any]:
        """运行完整的优化流程"""
        logger.info("开始完整的文档库优化流程...")
        
        start_time = time.time()
        optimization_results = {}
        
        # 技术栈列表
        tech_stacks = ['spring-boot', 'docker', 'python', 'vue']
        
        # 并行优化所有技术栈
        tasks = [self.optimize_tech_stack(tech_stack) for tech_stack in tech_stacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, tech_stack in enumerate(tech_stacks):
            if isinstance(results[i], dict):
                optimization_results[tech_stack] = results[i]
            else:
                optimization_results[tech_stack] = {
                    "success": False,
                    "error": str(results[i])
                }
        
        # 生成最终报告
        final_report = self.generate_optimization_report()
        
        end_time = time.time()
        duration = end_time - start_time
        
        optimization_results["summary"] = {
            "total_duration": round(duration, 2),
            "successful_optimizations": sum(1 for result in optimization_results.values() 
                                           if result.get("success", False)),
            "total_tech_stacks": len(tech_stacks)
        }
        
        return optimization_results

async def main():
    """主函数"""
    pipeline = DocumentOptimizationPipeline()
    
    print("=" * 70)
    print("企业级智能技术助手 - 文档库优化工具")
    print("=" * 70)
    
    print("\n优化目标:")
    print("- 深度爬取配置问题和API接口")
    print("- 补充高级主题内容")
    print("- 去除重复文档")
    print("- 建立质量监控机制")
    
    print("\n开始优化流程...")
    
    try:
        # 运行完整优化
        results = await pipeline.run_full_optimization()
        
        # 显示优化结果
        print("\n" + "=" * 70)
        print("优化完成!")
        print("=" * 70)
        
        successful_count = 0
        for tech_stack, result in results.items():
            if result.get("success", False):
                print(f"[OK] {tech_stack}: 优化成功")
                successful_count += 1
            else:
                print(f"[ERROR] {tech_stack}: 优化失败 - {result.get('error', '未知错误')}")
        
        # 显示统计信息
        summary = results.get("summary", {})
        print(f"\n优化统计:")
        print(f"- 成功优化: {successful_count}/{summary.get('total_tech_stacks', 0)} 个技术栈")
        print(f"- 总耗时: {summary.get('total_duration', 0)} 秒")
        
        # 显示文档库改进情况
        if hasattr(pipeline, 'optimization_stats'):
            print(f"\n文档库改进:")
            for tech_stack, stats in pipeline.optimization_stats.items():
                original = stats.get('original_count', 0)
                final = stats.get('final_count', 0)
                improvement = ((final - original) / original * 100) if original > 0 else 0
                print(f"- {tech_stack}: {original} -> {final} 个文档 (+{improvement:.1f}%)")
        
        print("\n下一步操作:")
        print("1. 查看详细报告: optimization_report.json")
        print("2. 启动后端服务测试优化效果")
        print("3. 在前端界面验证知识库质量")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 优化流程失败: {e}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())