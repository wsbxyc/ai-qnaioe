package com.tech.assistant.service;

import com.tech.assistant.model.IntentResult;
import com.tech.assistant.model.QueryIntent;
import com.tech.assistant.model.RetrievalResult;
import com.tech.assistant.model.TechResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

/**
 * 技术助手核心服务
 * 协调意图识别、混合检索、答案生成和缓存
 */
@Slf4j
@Service
public class TechAssistantService {

    /**
     * 混合检索服务
     */
    @Autowired
    private HybridRetrievalService hybridRetrievalService;

    /**
     * 缓存服务
     */
    @Autowired
    private CacheService cacheService;

    /**
     * RAG答案生成服务
     */
    @Autowired
    private RagAnswerService ragAnswerService;

    /**
     * 处理技术查询
     * @param query 用户查询
     * @param intentResult 意图识别结果
     * @param techStack 技术栈筛选
     * @param category 分类筛选
     * @return 技术助手响应
     */
    public TechResponse processQuery(String query, IntentResult intentResult, String techStack, String category) {
        long startTime = System.currentTimeMillis();
        log.info("处理技术查询，意图：{}，置信度：{}", intentResult.getIntent(), intentResult.getConfidence());

        String sessionId = UUID.randomUUID().toString();

        String cacheKey = CacheService.buildAnswerCacheKey(query, techStack, category, intentResult.getIntent());
        String cachedAnswer = cacheService.getCachedAnswer(cacheKey);
        if (cachedAnswer != null) {
            log.info("命中答案缓存，耗时：{}ms", System.currentTimeMillis() - startTime);
            return buildResponse(query, cachedAnswer, intentResult, null, sessionId);
        }

        List<RetrievalResult> relevantDocs = hybridRetrievalService.hybridSearch(
                query, techStack, category, intentResult.getIntent());

        String answer = ragAnswerService.synthesize(query, intentResult.getIntent(), relevantDocs);

        if (!relevantDocs.isEmpty()) {
            cacheService.cacheAnswer(cacheKey, answer);
        }

        log.info("查询处理完成，耗时：{}ms", System.currentTimeMillis() - startTime);
        return buildResponse(query, answer, intentResult, relevantDocs, sessionId);
    }

    /**
     * 混合检索（测试用）
     * @param query 用户查询
     * @param techStack 技术栈筛选
     * @param category 分类筛选
     * @param intent 查询意图
     * @return 检索结果列表
     */
    public List<RetrievalResult> hybridRetrieve(String query, String techStack, String category, QueryIntent intent) {
        return hybridRetrievalService.hybridSearch(query, techStack, category, intent);
    }

    /**
     * 构建响应对象
     * @param query 用户查询
     * @param answer 答案
     * @param intentResult 意图识别结果
     * @param docs 检索到的文档
     * @param sessionId 会话ID
     * @return 技术助手响应
     */
    private TechResponse buildResponse(String query, String answer, IntentResult intentResult,
                                       List<RetrievalResult> docs, String sessionId) {
        return TechResponse.builder()
                .success(true)
                .query(query)
                .answer(answer)
                .intent(intentResult.getIntent())
                .confidence(intentResult.getConfidence())
                .relevantDocuments(docs)
                .sessionId(sessionId)
                .timestamp(System.currentTimeMillis())
                .build();
    }
}
