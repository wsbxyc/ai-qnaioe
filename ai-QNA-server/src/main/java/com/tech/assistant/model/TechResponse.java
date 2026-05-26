package com.tech.assistant.model;

import lombok.*;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TechResponse {
    
    /**
     * 请求是否成功
     */
    private boolean success;
    
    /**
     * 原始查询问题
     */
    private String query;
    
    /**
     * AI生成的回答
     */
    private String answer;
    
    /**
     * 识别出的意图
     */
    private QueryIntent intent;
    
    /**
     * 意图识别置信度
     */
    private double confidence;
    
    /**
     * 相关技术文档
     */
    private List<RetrievalResult> relevantDocuments;
    
    /**
     * 会话ID
     */
    private String sessionId;
    
    /**
     * 时间戳
     */
    private Long timestamp;
}