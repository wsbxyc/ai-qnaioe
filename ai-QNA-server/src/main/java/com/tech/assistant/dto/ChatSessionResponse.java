package com.tech.assistant.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 聊天会话响应DTO
 * 用于返回聊天会话信息
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatSessionResponse {
    
    /**
     * 会话ID
     */
    private Long id;
    
    /**
     * 会话标题
     */
    private String title;
    
    /**
     * 会话消息（JSON格式）
     */
    private String messages;
    
    /**
     * 创建时间
     */
    private String createdAt;
    
    /**
     * 更新时间
     */
    private String updatedAt;
}
