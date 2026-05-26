package com.tech.assistant.model;

import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IntentResult {
    
    /**
     * 识别出的意图
     */
    private QueryIntent intent;
    
    /**
     * 置信度 (0-1)
     */
    private double confidence;
    
    /**
     * 识别方法
     */
    private String method; // RULE_BASED, VECTOR_BASED, HYBRID_CONSISTENT
    
    /**
     * 是否需要混合检索
     */
    private boolean needHybridRetrieval;
    
    /**
     * 路由到的知识库类型
     */
    private String targetKnowledgeBase;
}