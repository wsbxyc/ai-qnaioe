package com.tech.assistant.service;

import com.tech.assistant.config.SystemConfig;
import com.tech.assistant.model.QueryIntent;
import com.tech.assistant.model.RetrievalResult;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.data.message.UserMessage;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.output.Response;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * RAG答案生成服务
 * 基于检索到的文档和用户意图，调用大模型生成答案
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RagAnswerService {

    /**
     * 聊天语言模型
     */
    private final ChatLanguageModel chatLanguageModel;

    /**
     * 系统配置
     */
    private final SystemConfig systemConfig;

    /**
     * 合成答案
     * @param userQuery 用户查询
     * @param intent 查询意图
     * @param docs 检索到的文档
     * @return 生成的答案
     */
    public String synthesize(String userQuery, QueryIntent intent, List<RetrievalResult> docs) {
        if (docs == null || docs.isEmpty()) {
            return "抱歉，暂未找到相关的技术文档。建议您：\n1. 尝试更具体的关键词\n2. 检查技术栈筛选是否正确\n3. 确认知识库已写入向量并完成索引";
        }

        int maxDocs = systemConfig.getRetrieval().getRagContextDocLimit();
        int charBudget = systemConfig.getRetrieval().getRagCharBudgetPerDoc();

        StringBuilder ctx = new StringBuilder();
        for (int i = 0; i < Math.min(docs.size(), maxDocs); i++) {
            RetrievalResult d = docs.get(i);
            String body = d.getContent() != null ? d.getContent() : "";
            if (body.length() > charBudget) {
                body = body.substring(0, charBudget) + "...";
            }
            ctx.append("[片段").append(i + 1).append("] ")
                    .append(d.getTitle() != null ? d.getTitle() : "无标题")
                    .append(" | 技术栈:").append(d.getTechStack() != null ? d.getTechStack() : "—")
                    .append(" | 类别:").append(d.getCategory() != null ? d.getCategory() : "—")
                    .append("\n")
                    .append(body)
                    .append("\n\n");
        }

        String intentHint = switch (intent != null ? intent : QueryIntent.GENERAL_KNOWLEDGE) {
            case CONFIG_QUERY -> "侧重配置项、配置文件路径、YAML/Properties 示例与注意事项。";
            case API_RECOMMENDATION -> "侧重可调用 API、方法签名、代码示例与典型用法。";
            case TROUBLESHOOTING -> "侧重错误原因、排查步骤与修复方案。";
            case GENERAL_KNOWLEDGE -> "在配置与 API 之间平衡说明，并给出实践建议。";
        };

        String prompt = """
                你是企业级智能技术助手（配置 + API 双引擎）。请仅依据「检索上下文」作答，不要编造不存在的类名、配置项或版本。
                若上下文不足以回答，请明确说明缺什么信息。
                回答要求：使用简体中文，结构清晰（可分段或小标题），涉及配置时写出键名或文件位置；涉及 API 时给出简短示例代码块（仅当上下文中有依据时）。

                意图侧重：%s

                ### 检索上下文
                %s

                ### 用户问题
                %s
                """.formatted(intentHint, ctx, userQuery);

        try {
            Response<AiMessage> response = chatLanguageModel.generate(UserMessage.from(prompt));
            String text = response.content().text();
            if (text == null || text.isBlank()) {
                return fallbackConcat(userQuery, docs);
            }
            return text.trim();
        } catch (Exception e) {
            log.warn("大模型生成失败，使用检索片段拼接降级: {}", e.getMessage());
            return fallbackConcat(userQuery, docs);
        }
    }

    /**
     * 降级方案：拼接检索片段
     * @param userQuery 用户查询
     * @param docs 检索到的文档
     * @return 拼接的答案
     */
    private String fallbackConcat(String userQuery, List<RetrievalResult> docs) {
        StringBuilder answer = new StringBuilder();
        answer.append("（离线降级）根据检索到的技术文档，为您提供以下信息：\n\n");
        for (int i = 0; i < Math.min(docs.size(), 3); i++) {
            RetrievalResult doc = docs.get(i);
            answer.append("【").append(i + 1).append("】").append(doc.getTitle()).append("\n");
            String content = doc.getContent();
            if (content != null && content.length() > 400) {
                content = content.substring(0, 400) + "...";
            }
            answer.append(content != null ? content : "").append("\n\n");
        }
        answer.append("---\n问题：").append(userQuery);
        return answer.toString();
    }
}
