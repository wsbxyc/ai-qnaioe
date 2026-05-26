package com.tech.assistant.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 聊天会话请求DTO
 * 用于创建或更新聊天会话
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatSessionRequest {
    
    /**
     * 会话标题
     */
    private String title;
    
    /**
     * 会话消息（JSON格式）
     */
    private String messages;
}

