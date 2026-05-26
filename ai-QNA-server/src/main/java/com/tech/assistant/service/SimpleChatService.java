package com.tech.assistant.service;

import org.springframework.stereotype.Service;

/**
 * 简单聊天服务
 */
@Service
public class SimpleChatService {
    
    public String generateResponse(String userMessage) {
        return "当前AI服务暂时不可用，请稍后重试。您的问题已记录：" + userMessage;
    }
}