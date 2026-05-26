package com.tech.assistant.service;

import com.tech.assistant.config.SystemConfig;
import com.tech.assistant.model.IntentResult;
import com.tech.assistant.model.QueryIntent;
import dev.langchain4j.model.embedding.EmbeddingModel;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Pattern;

/**
 * 意图路由服务
 * 通过规则匹配和向量相似度识别用户查询意图（配置查询、API推荐、故障排查、通用知识）
 */
@Slf4j
@Service
public class IntentRouter {

    /**
     * 系统配置
     */
    @Autowired
    private SystemConfig systemConfig;

    /**
     * 嵌入模型
     */
    @Autowired
    private EmbeddingModel embeddingModel;

    /**
     * 规则模式映射（意图名称 -> 正则模式）
     */
    private final Map<String, Pattern> rulePatterns = new HashMap<>();

    /**
     * 意图关键词映射（意图名称 -> 关键词列表）
     */
    private final Map<String, List<String>> intentKeywords = new HashMap<>();

    /**
     * 意图向量质心映射（意图 -> 归一化向量）
     */
    private final Map<QueryIntent, List<Float>> intentCentroids = new EnumMap<>(QueryIntent.class);

    /**
     * 构造函数，初始化规则模式和关键词
     */
    public IntentRouter() {
        initializeRulePatterns();
        initializeIntentKeywords();
    }

    /**
     * 预热意图向量质心（Bean初始化后执行）
     */
    @PostConstruct
    public void warmIntentCentroids() {
        Map<QueryIntent, List<String>> seeds = new EnumMap<>(QueryIntent.class);
        seeds.put(QueryIntent.CONFIG_QUERY, Arrays.asList(
                "Spring Boot application.yml 多数据源与 JVM 参数如何配置",
                "Docker Compose 网络、卷、环境变量与资源限制配置",
                "Redis 与 MySQL 连接池、超时与线程池参数调优",
                "Kubernetes Deployment 资源配置与 ConfigMap 挂载",
                "Nginx 或 Spring Cloud Gateway 路由与超时配置"
        ));
        seeds.put(QueryIntent.API_RECOMMENDATION, Arrays.asList(
                "Java Stream map filter collect 示例与常用中间操作",
                "Python requests 或 httpx 调用 REST API 示例",
                "Vue 3 Composition API ref reactive 与组合式函数",
                "React hooks 中 useEffect 请求数据与清理",
                "Spring WebClient 或 RestTemplate POST JSON 示例",
                "Node.js Express 或 Fastify 路由与中间件示例"
        ));
        seeds.put(QueryIntent.TROUBLESHOOTING, Arrays.asList(
                "Spring Boot 启动失败 端口占用 依赖冲突 如何排查",
                "Docker 容器退出码 网络不通 卷权限 故障排查",
                "MySQL 慢查询 锁等待 连接数耗尽 错误日志分析",
                "Redis 内存淘汰 主从延迟 超时异常 处理思路",
                "前端 CORS 与 404 接口报错 调试步骤"
        ));
        seeds.put(QueryIntent.GENERAL_KNOWLEDGE, Arrays.asList(
                "微服务与单体架构的取舍与适用场景",
                "缓存穿透击穿雪崩与常见缓解策略",
                "REST 与 gRPC 选型与最佳实践概述",
                "技术文档阅读与问题定位的通用方法"
        ));

        for (Map.Entry<QueryIntent, List<String>> e : seeds.entrySet()) {
            try {
                List<List<Float>> vectors = new ArrayList<>();
                for (String phrase : e.getValue()) {
                    vectors.add(embeddingModel.embed(phrase).content().vectorAsList());
                }
                intentCentroids.put(e.getKey(), averageAndNormalize(vectors));
            } catch (Exception ex) {
                log.warn("意图 {} 向量原型预热失败（可检查 DASHSCOPE_API_KEY）: {}", e.getKey(), ex.getMessage());
            }
        }
    }

    /**
     * 路由查询意图
     * @param query 用户查询
     * @return 意图识别结果
     */
    public IntentResult routeIntent(String query) {
        log.info("开始意图识别，查询：{}", query);
        if (!systemConfig.getRouting().isEnableSmartRouting()) {
            IntentResult ruleOnly = ruleBasedClassification(query);
            log.info("智能路由已关闭，仅规则：{}", ruleOnly);
            return ruleOnly;
        }

        IntentResult ruleResult = ruleBasedClassification(query);
        IntentResult vectorResult = vectorBasedClassification(query);
        IntentResult finalResult = hybridDecision(ruleResult, vectorResult);
        log.info("意图识别完成：{}", finalResult);
        return finalResult;
    }

    /**
     * 基于规则的意图分类
     * @param query 用户查询
     * @return 意图识别结果
     */
    private IntentResult ruleBasedClassification(String query) {
        double maxScore = 0.0;
        QueryIntent bestIntent = QueryIntent.GENERAL_KNOWLEDGE;
        String q = query.toLowerCase(Locale.ROOT);

        for (Map.Entry<String, Pattern> entry : rulePatterns.entrySet()) {
            String intentName = entry.getKey();
            Pattern pattern = entry.getValue();
            if (pattern.matcher(q).find()) {
                double score = calculateRuleScore(query, intentName);
                if (score > maxScore) {
                    maxScore = score;
                    bestIntent = QueryIntent.valueOf(intentName);
                }
            }
        }

        return IntentResult.builder()
                .intent(bestIntent)
                .confidence(maxScore)
                .method("RULE_BASED")
                .build();
    }

    /**
     * 基于向量的意图分类
     * @param query 用户查询
     * @return 意图识别结果
     */
    private IntentResult vectorBasedClassification(String query) {
        try {
            if (intentCentroids.isEmpty()) {
                return IntentResult.builder()
                        .intent(QueryIntent.GENERAL_KNOWLEDGE)
                        .confidence(0.35)
                        .method("VECTOR_SKIPPED")
                        .build();
            }

            List<Float> queryVec = embeddingModel.embed(query).content().vectorAsList();
            Map<QueryIntent, Double> similarityScores = new EnumMap<>(QueryIntent.class);

            for (QueryIntent intent : QueryIntent.values()) {
                List<Float> centroid = intentCentroids.get(intent);
                if (centroid == null || centroid.isEmpty()) {
                    continue;
                }
                double sim = cosineSimilarity(queryVec, centroid);
                similarityScores.put(intent, sim);
            }

            if (similarityScores.isEmpty()) {
                return IntentResult.builder()
                        .intent(QueryIntent.GENERAL_KNOWLEDGE)
                        .confidence(0.35)
                        .method("VECTOR_BASED")
                        .build();
            }

            QueryIntent bestIntent = similarityScores.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse(QueryIntent.GENERAL_KNOWLEDGE);

            double confidence = similarityScores.get(bestIntent);

            return IntentResult.builder()
                    .intent(bestIntent)
                    .confidence(confidence)
                    .method("VECTOR_BASED")
                    .build();

        } catch (Exception e) {
            log.error("向量分类失败：{}", e.getMessage());
            return IntentResult.builder()
                    .intent(QueryIntent.GENERAL_KNOWLEDGE)
                    .confidence(0.4)
                    .method("VECTOR_BASED")
                    .build();
        }
    }

    /**
     * 混合决策，融合规则和向量结果
     * @param ruleResult 规则识别结果
     * @param vectorResult 向量识别结果
     * @return 最终意图识别结果
     */
    private IntentResult hybridDecision(IntentResult ruleResult, IntentResult vectorResult) {
        double ruleBar = systemConfig.getRouting().getRuleThreshold();
        double vectorBar = systemConfig.getRouting().getVectorThreshold();

        double ruleConfidence = ruleResult.getConfidence();
        double vectorConfidence = vectorResult.getConfidence();

        if (ruleConfidence >= ruleBar) {
            return ruleResult;
        }
        if (vectorConfidence >= vectorBar) {
            return vectorResult;
        }

        if (ruleResult.getIntent() == vectorResult.getIntent()) {
            double hybridConfidence = (ruleConfidence + vectorConfidence) / 2;
            return IntentResult.builder()
                    .intent(ruleResult.getIntent())
                    .confidence(hybridConfidence)
                    .method("HYBRID_CONSISTENT")
                    .build();
        }

        if (ruleConfidence >= 0.35 && vectorConfidence >= 0.35) {
            IntentResult pick = ruleConfidence >= vectorConfidence ? ruleResult : vectorResult;
            return IntentResult.builder()
                    .intent(pick.getIntent())
                    .confidence((ruleConfidence + vectorConfidence) / 2)
                    .method("HYBRID_DISAGREE_PICK")
                    .build();
        }

        return ruleConfidence >= vectorConfidence ? ruleResult : vectorResult;
    }

    /**
     * 计算规则匹配分数
     * @param query 用户查询
     * @param intentName 意图名称
     * @return 匹配分数（0-1）
     */
    private double calculateRuleScore(String query, String intentName) {
        List<String> keywords = intentKeywords.get(intentName);
        if (keywords == null) {
            return 0.0;
        }
        String lowerQuery = query.toLowerCase(Locale.ROOT);
        int matchCount = 0;
        for (String keyword : keywords) {
            if (lowerQuery.contains(keyword.toLowerCase(Locale.ROOT))) {
                matchCount++;
            }
        }
        return (double) matchCount / keywords.size();
    }

    /**
     * 计算余弦相似度
     * @param a 向量a
     * @param b 向量b
     * @return 余弦相似度（0-1）
     */
    private static double cosineSimilarity(List<Float> a, List<Float> b) {
        if (a == null || b == null || a.size() != b.size() || a.isEmpty()) {
            return 0.0;
        }
        double dot = 0.0;
        double n1 = 0.0;
        double n2 = 0.0;
        for (int i = 0; i < a.size(); i++) {
            float x = a.get(i);
            float y = b.get(i);
            dot += x * y;
            n1 += x * x;
            n2 += y * y;
        }
        if (n1 <= 0 || n2 <= 0) {
            return 0.0;
        }
        return dot / (Math.sqrt(n1) * Math.sqrt(n2));
    }

    /**
     * 计算向量平均值并归一化
     * @param vectors 向量列表
     * @return 归一化的平均向量
     */
    private static List<Float> averageAndNormalize(List<List<Float>> vectors) {
        int dim = vectors.get(0).size();
        double[] acc = new double[dim];
        for (List<Float> v : vectors) {
            for (int i = 0; i < dim; i++) {
                acc[i] += v.get(i);
            }
        }
        int n = vectors.size();
        List<Float> out = new ArrayList<>(dim);
        double norm = 0.0;
        for (int i = 0; i < dim; i++) {
            float val = (float) (acc[i] / n);
            out.add(val);
            norm += val * val;
        }
        norm = Math.sqrt(norm);
        if (norm > 1e-8) {
            for (int i = 0; i < dim; i++) {
                out.set(i, out.get(i) / (float) norm);
            }
        }
        return out;
    }

    /**
     * 初始化规则模式
     */
    private void initializeRulePatterns() {
        rulePatterns.put("CONFIG_QUERY",
                Pattern.compile("(配置|设置|properties|yml|yaml|application|spring|boot|环境变量|参数|compose|k8s|kubernetes|deployment|configmap)"));
        rulePatterns.put("API_RECOMMENDATION",
                Pattern.compile("(api|接口|调用|方法|函数|如何使用|怎么用|recommend|suggest|示例|demo|sample|hook|stream|webclient|resttemplate)"));
        rulePatterns.put("TROUBLESHOOTING",
                Pattern.compile("(错误|异常|问题|bug|故障|解决|修复|trouble|error|exception|fix|崩溃|超时|无法连接|failed|timeout)"));
    }

    /**
     * 初始化意图关键词
     */
    private void initializeIntentKeywords() {
        intentKeywords.put("CONFIG_QUERY", Arrays.asList(
                "配置", "设置", "properties", "yml", "yaml", "application",
                "spring", "boot", "环境变量", "参数", "compose", "kubernetes", "连接池"
        ));
        intentKeywords.put("API_RECOMMENDATION", Arrays.asList(
                "api", "接口", "调用", "方法", "函数", "如何使用", "怎么用",
                "recommend", "suggest", "推荐", "建议", "示例", "装饰器", "hook", "stream"
        ));
        intentKeywords.put("TROUBLESHOOTING", Arrays.asList(
                "错误", "异常", "问题", "bug", "故障", "解决", "修复",
                "trouble", "error", "exception", "fix", "调试", "无法", "失败"
        ));
    }
}
