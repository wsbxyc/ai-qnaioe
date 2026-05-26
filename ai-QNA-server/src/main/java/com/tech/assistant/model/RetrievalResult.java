package com.tech.assistant.model;

import lombok.*;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RetrievalResult {
    
    /**
     * 文档ID
     */
    private String documentId;
    
    /**
     * 文档标题
     */
    private String title;
    
    /**
     * 文档内容
     */
    private String content;
    
    /**
     * 文档摘要
     */
    private String summary;
    
    /**
     * 技术栈
     */
    private String techStack;
    
    /**
     * 类别
     */
    private String category;
    
    /**
     * 标签
     */
    private List<String> tags;
    
    /**
     * 来源
     */
    private String source;
    
    /**
     * 最终得分
     */
    private double score;
    
    /**
     * BM25得分
     */
    private Double bm25Score;
    
    /**
     * 向量得分
     */
    private Double vectorScore;
    
    /**
     * RRF得分
     */
    private Double rrfScore;
    
    /**
     * 检索方法
     */
    private String retrievalMethod;
}