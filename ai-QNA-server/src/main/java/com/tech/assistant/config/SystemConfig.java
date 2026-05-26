package com.tech.assistant.config;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 系统配置类
 * 从application.yml中读取tech.assistant前缀的配置项
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "tech.assistant")
public class SystemConfig {
    
    /**
     * 系统名称
     */
    private String name;
    
    /**
     * 系统版本
     */
    private String version;
    
    /**
     * 知识库配置
     */
    private KnowledgeBaseConfig knowledgeBase = new KnowledgeBaseConfig();
    
    /**
     * 检索配置
     */
    private RetrievalConfig retrieval = new RetrievalConfig();
    
    /**
     * 路由配置
     */
    private RoutingConfig routing = new RoutingConfig();
    
    /**
     * LLM配置
     */
    private LlmConfig llm = new LlmConfig();
    
    /**
     * 知识库配置类
     */
    @Data
    public static class KnowledgeBaseConfig {
        
        /**
         * 知识库最大文档数
         */
        private int maxDocuments = 50000;
        
        /**
         * 支持的技术栈列表
         */
        private String[] supportedTechStacks = {
            "Spring Boot", "Docker", "Java", "Python", "Vue", "React", "MySQL", "Redis",
            "TypeScript", "Node.js", "Kubernetes", "PostgreSQL", "MongoDB"
        };
        
        /**
         * 知识类型列表
         */
        private String[] knowledgeTypes = {"CONFIG", "API", "TROUBLESHOOTING", "BEST_PRACTICE", "TUTORIAL"};
    }
    
    /**
     * 检索配置类
     */
    @Data
    public static class RetrievalConfig {
        
        /**
         * 是否启用混合检索
         */
        private boolean enableHybridSearch = true;
        
        /**
         * RRF中BM25权重
         */
        private double bm25Weight = 0.4;
        
        /**
         * RRF中向量权重
         */
        private double vectorWeight = 0.4;
        
        /**
         * RRF中RRF权重
         */
        private double rrfWeight = 0.2;
        
        /**
         * 返回的文档数量
         */
        private int topK = 10;
        
        /**
         * 相似度阈值
         */
        private double similarityThreshold = 0.7;
        
        /**
         * RRF常数k（典型值60）
         */
        private int rrfK = 60;
        
        /**
         * BM25/向量各路召回条数
         */
        private int candidatePoolSize = 80;
        
        /**
         * RAG上下文中的文档数量限制
         */
        private int ragContextDocLimit = 5;
        
        /**
         * 每个文档在RAG上下文中的字符数限制
         */
        private int ragCharBudgetPerDoc = 1200;
        
        /**
         * 是否启用缓存
         */
        private boolean cacheEnabled = true;
        
        /**
         * 缓存过期时间（秒）
         */
        private int cacheTtlSeconds = 3600;
        
        /**
         * 是否启用Redis缓存
         */
        private boolean redisCacheEnabled = true;
    }
    
    /**
     * 路由配置类
     */
    @Data
    public static class RoutingConfig {
        
        /**
         * 是否启用智能路由
         */
        private boolean enableSmartRouting = true;
        
        /**
         * 规则匹配阈值
         */
        private double ruleThreshold = 0.6;
        
        /**
         * 向量匹配阈值
         */
        private double vectorThreshold = 0.8;
        
        /**
         * 意图类型列表
         */
        private String[] intentTypes = {"CONFIG_QUERY", "API_RECOMMENDATION", "TROUBLESHOOTING", "GENERAL_KNOWLEDGE"};
    }
    
    /**
     * LLM配置类
     */
    @Data
    public static class LlmConfig {
        
        /**
         * 当前使用的模型名称
         */
        private String activeModel = "qwen-max";
        
        /**
         * 模型配置列表
         */
        private ModelConfig[] models = {
            new ModelConfig("qwen-max", "通义千问 Max", true),
            new ModelConfig("qwen-plus", "通义千问 Plus", false)
        };
    }
    
    /**
     * 模型配置类
     */
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class ModelConfig {
        
        /**
         * 模型名称
         */
        private String name;
        
        /**
         * 模型描述
         */
        private String description;
        
        /**
         * 是否启用
         */
        private boolean enabled;
    }
}