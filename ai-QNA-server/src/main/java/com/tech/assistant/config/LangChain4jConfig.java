package com.tech.assistant.config;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.dashscope.QwenChatModel;
import dev.langchain4j.model.dashscope.QwenEmbeddingModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import java.util.HashMap;
import java.util.Map;

/**
 * LangChain4J配置类
 * 集成通义千问（DashScope）大模型
 */
@Slf4j
@Configuration
public class LangChain4jConfig {

    /**
     * 通义千问API Key
     */
    @Value("${langchain4j.dashscope.api-key:}")
    private String dashscopeApiKey;

    /**
     * 通义千问聊天模型名称
     */
    @Value("${langchain4j.dashscope.chat-model-name:qwen-max}")
    private String dashscopeChatModelName;

    /**
     * 通义千问嵌入模型名称
     */
    @Value("${langchain4j.dashscope.embedding-model-name:text-embedding-v4}")
    private String dashscopeEmbeddingModelName;

    /**
     * 注册通义千问聊天模型
     * @return 模型名称到ChatLanguageModel的映射
     */
    @Bean
    public Map<String, ChatLanguageModel> chatModels() {
        Map<String, ChatLanguageModel> models = new HashMap<>();

        // 添加通义千问模型
        if (dashscopeApiKey != null && !dashscopeApiKey.isBlank()) {
            try {
                QwenChatModel qwenModel = QwenChatModel.builder()
                        .apiKey(dashscopeApiKey.trim())
                        .modelName(dashscopeChatModelName)
                        .build();
                models.put("qwen-max", qwenModel);
                log.info("✅ 通义千问模型已注册: {}", dashscopeChatModelName);
            } catch (Exception e) {
                log.warn("⚠️ 通义千问模型注册失败: {}", e.getMessage());
            }
        }

        log.info("📋 已注册 {} 个大模型: {}", models.size(), models.keySet());
        return models;
    }

    /**
     * 获取当前使用的聊天模型
     * @param chatModels 所有可用的聊天模型
     * @return 当前使用的ChatLanguageModel
     */
    @Bean
    @Primary
    public ChatLanguageModel chatLanguageModel(Map<String, ChatLanguageModel> chatModels) {
        ChatLanguageModel model = chatModels.get("qwen-max");
        if (model != null) {
            log.info("🚀 当前使用的大模型: qwen-max");
            return model;
        }

        throw new IllegalStateException("没有可用的大模型，请检查配置");
    }

    /**
     * 获取嵌入模型
     * @return EmbeddingModel
     */
    @Bean
    public EmbeddingModel embeddingModel() {
        return QwenEmbeddingModel.builder()
                .apiKey(dashscopeApiKey != null ? dashscopeApiKey.trim() : "")
                .modelName(dashscopeEmbeddingModelName)
                .build();
    }
}
