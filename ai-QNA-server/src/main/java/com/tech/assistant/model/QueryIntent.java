package com.tech.assistant.model;

/**
 * 查询意图枚举
 */
public enum QueryIntent {
    /**
     * 配置查询 - 如Spring Boot配置、Docker配置等
     */
    CONFIG_QUERY,
    
    /**
     * API推荐 - 如推荐合适的API、方法调用等
     */
    API_RECOMMENDATION,
    
    /**
     * 故障排除 - 如错误解决、问题排查等
     */
    TROUBLESHOOTING,
    
    /**
     * 通用知识 - 如概念解释、最佳实践等
     */
    GENERAL_KNOWLEDGE
}