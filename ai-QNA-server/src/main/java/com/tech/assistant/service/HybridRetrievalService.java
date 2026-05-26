package com.tech.assistant.service;

import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch._types.query_dsl.TextQueryType;
import co.elastic.clients.json.JsonData;
import com.tech.assistant.config.SystemConfig;
import com.tech.assistant.model.QueryIntent;
import com.tech.assistant.model.RetrievalResult;
import com.tech.assistant.model.TechDocument;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.model.embedding.EmbeddingModel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.elasticsearch.client.elc.NativeQuery;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.data.elasticsearch.core.SearchHit;
import org.springframework.data.elasticsearch.core.SearchHits;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 混合检索服务：BM25（全文） + 向量（dense_vector 余弦） + RRF（倒数排名融合）。
 * <p>
 * 流程概览：
 * <ol>
 *   <li>BM25 路：multi_match 查询 title/content 等，并按技术栈、类别、意图做 filter/should 加权。</li>
 *   <li>向量路：将用户问题 embed 后，用 script_score + cosineSimilarity 与文档 embedding 比对。</li>
 *   <li>RRF：两路各取前 N 条，按排名倒数加权融合（权重来自配置 bm25Weight、vectorWeight、rrfWeight）。</li>
 * </ol>
 */
@Slf4j
@Service
public class HybridRetrievalService {

    @Autowired
    private SystemConfig systemConfig;

    @Autowired
    private ElasticsearchOperations elasticsearchOperations;

    @Autowired
    private EmbeddingModel embeddingModel;

    /** 检索结果短期内存缓存，减轻 ES 与 embed 压力（与答案缓存 Redis 不同，仅缓存「文档列表」） */
    private final Map<String, CacheEntry> cache = new ConcurrentHashMap<>();

    /** 检索缓存 TTL：5 分钟 */
    private static final long CACHE_TTL_MS = 5 * 60 * 1000;

    private static class CacheEntry {
        final List<RetrievalResult> results;
        final long timestamp;

        CacheEntry(List<RetrievalResult> results) {
            this.results = results;
            this.timestamp = System.currentTimeMillis();
        }

        boolean isExpired() {
            return System.currentTimeMillis() - timestamp > CACHE_TTL_MS;
        }
    }

    /**
     * 对外主入口：根据查询文本、可选技术栈/类别、以及意图做混合检索。
     *
     * @param query     用户问题（向量化与 BM25 均依赖）
     * @param techStack 非空时在 ES 中 term 过滤字段 techStack
     * @param category  非空时在 ES 中 term 过滤字段 category（优先级高于意图 boost）
     * @param intent    意图路由：在 BM25 的 bool 上增加 should 提升对应 category 得分
     */
    public List<RetrievalResult> hybridSearch(String query, String techStack, String category, QueryIntent intent) {
        long startTime = System.currentTimeMillis();
        log.info("混合检索 query={} techStack={} category={} intent={}", query, techStack, category, intent);

        String cacheKey = buildCacheKey(query, techStack, category, intent);
        CacheEntry cached = cache.get(cacheKey);
        if (cached != null && !cached.isExpired()) {
            log.info("检索缓存命中，耗时 {}ms", System.currentTimeMillis() - startTime);
            return cached.results;
        }

        List<RetrievalResult> finalResults;
        if (!systemConfig.getRetrieval().isEnableHybridSearch()) {
            finalResults = bm25OnlySearch(query, techStack, category, intent);
        } else {
            finalResults = bm25VectorRrfSearch(query, techStack, category, intent);
        }

        cache.put(cacheKey, new CacheEntry(finalResults));
        log.info("混合检索完成，条数={} 耗时={}ms", finalResults.size(), System.currentTimeMillis() - startTime);
        return finalResults;
    }

    /** 缓存键：四元组字符串，意图变化会导致不同缓存条目 */
    private String buildCacheKey(String query, String techStack, String category, QueryIntent intent) {
        return String.format("%s|%s|%s|%s",
                query != null ? query : "",
                techStack != null ? techStack : "",
                category != null ? category : "",
                intent != null ? intent.name() : "");
    }

    /** 关闭混合时仅走 BM25，取 topK 条 */
    private List<RetrievalResult> bm25OnlySearch(String query, String techStack, String category, QueryIntent intent) {
        int topK = systemConfig.getRetrieval().getTopK();
        NativeQuery nq = NativeQuery.builder()
                .withQuery(buildBm25Query(query, techStack, category, intent))
                .withPageable(PageRequest.of(0, topK))
                .build();
        SearchHits<TechDocument> hits = elasticsearchOperations.search(nq, TechDocument.class);
        // Spring Data Elasticsearch 的 SearchHit#getScore() 返回 float 基本类型，传给 convertHit 时会自动加宽为 double
        return hits.stream()
                .map(h -> convertHit(h, h.getScore(), "BM25"))
                .collect(Collectors.toList());
    }

    /**
     * 完整混合：分别拉取 BM25 与向量两路候选池，再 RRF 融合后取 topK。
     */
    private List<RetrievalResult> bm25VectorRrfSearch(String query, String techStack, String category, QueryIntent intent) {
        int pool = Math.max(systemConfig.getRetrieval().getCandidatePoolSize(), systemConfig.getRetrieval().getTopK());
        int topK = systemConfig.getRetrieval().getTopK();
        double rrfK = systemConfig.getRetrieval().getRrfK();
        double wB = systemConfig.getRetrieval().getBm25Weight();
        double wV = systemConfig.getRetrieval().getVectorWeight();
        // rrfWeight 作为对 RRF 总得分的整体缩放（配置为 0 时用 1.0）
        double rrfScalar = systemConfig.getRetrieval().getRrfWeight() > 0
                ? systemConfig.getRetrieval().getRrfWeight()
                : 1.0;

        List<RetrievalResult> bm25Ranked = runBm25Search(query, techStack, category, intent, pool);
        List<RetrievalResult> vecRanked = runVectorSearch(query, techStack, category, intent, pool);

        if (vecRanked.isEmpty()) {
            return bm25Ranked.stream().limit(topK).collect(Collectors.toList());
        }
        if (bm25Ranked.isEmpty()) {
            return vecRanked.stream().limit(topK).collect(Collectors.toList());
        }

        // 文档 id -> RRF 累加器；同一文档在两路都出现则分数叠加
        Map<String, RrfAccumulator> acc = new LinkedHashMap<>();

        for (int i = 0; i < bm25Ranked.size(); i++) {
            RetrievalResult r = bm25Ranked.get(i);
            String id = r.getDocumentId();
            // 标准 RRF 项：weight / (k + rank)，rank 从 1 开始故用 i+1
            double contrib = wB * rrfScalar / (rrfK + i + 1);
            acc.computeIfAbsent(id, k -> new RrfAccumulator(deepCopy(r)))
                    .addRrf(contrib)
                    .setBm25(r.getScore());
        }

        for (int i = 0; i < vecRanked.size(); i++) {
            RetrievalResult r = vecRanked.get(i);
            String id = r.getDocumentId();
            double contrib = wV * rrfScalar / (rrfK + i + 1);
            acc.computeIfAbsent(id, k -> new RrfAccumulator(deepCopy(r)))
                    .addRrf(contrib)
                    .setVector(r.getScore());
        }

        return acc.values().stream()
                .sorted(Comparator.comparingDouble((RrfAccumulator a) -> a.rrfScore).reversed())
                .limit(topK)
                .map(RrfAccumulator::toResult)
                .collect(Collectors.toList());
    }

    /** 深拷贝检索结果，避免 RRF 合并时修改共享对象 */
    private RetrievalResult deepCopy(RetrievalResult r) {
        return RetrievalResult.builder()
                .documentId(r.getDocumentId())
                .title(r.getTitle())
                .content(r.getContent())
                .summary(r.getSummary())
                .techStack(r.getTechStack())
                .category(r.getCategory())
                .tags(r.getTags() != null ? new ArrayList<>(r.getTags()) : null)
                .source(r.getSource())
                .score(r.getScore())
                .bm25Score(r.getBm25Score())
                .vectorScore(r.getVectorScore())
                .rrfScore(r.getRrfScore())
                .retrievalMethod(r.getRetrievalMethod())
                .build();
    }

    /**
     * RRF 阶段临时结构：累加 RRF 分，并分别记录来自 BM25 / 向量的原始分（便于调试与前端展示）。
     */
    private static final class RrfAccumulator {
        final RetrievalResult base;
        double rrfScore;
        Double bm25Score;
        Double vectorScore;

        RrfAccumulator(RetrievalResult base) {
            this.base = base;
        }

        RrfAccumulator addRrf(double v) {
            this.rrfScore += v;
            return this;
        }

        void setBm25(double s) {
            this.bm25Score = s;
        }

        void setVector(double s) {
            this.vectorScore = s;
        }

        RetrievalResult toResult() {
            return RetrievalResult.builder()
                    .documentId(base.getDocumentId())
                    .title(base.getTitle())
                    .content(base.getContent())
                    .summary(base.getSummary())
                    .techStack(base.getTechStack())
                    .category(base.getCategory())
                    .tags(base.getTags())
                    .source(base.getSource())
                    .score(rrfScore)
                    .bm25Score(bm25Score)
                    .vectorScore(vectorScore)
                    .rrfScore(rrfScore)
                    .retrievalMethod("RRF_BM25_VECTOR")
                    .build();
        }
    }

    /** 执行 BM25 检索，返回最多 size 条（用于 RRF 候选池） */
    private List<RetrievalResult> runBm25Search(String query, String techStack, String category, QueryIntent intent, int size) {
        NativeQuery nq = NativeQuery.builder()
                .withQuery(buildBm25Query(query, techStack, category, intent))
                .withPageable(PageRequest.of(0, size))
                .build();
        SearchHits<TechDocument> hits = elasticsearchOperations.search(nq, TechDocument.class);
        return hits.stream()
                .map(h -> {
                    RetrievalResult r = convertHit(h, h.getScore(), "BM25");
                    // RetrievalResult#setBm25Score 接收 Double；getScore() 为 float，必须显式转为 double 再装箱
                    r.setBm25Score((double) h.getScore());
                    return r;
                })
                .collect(Collectors.toList());
    }

    /**
     * 向量检索：embed 查询 -> script_score 余弦相似度；脚本为 cosineSimilarity + 1.0，故 ES 得分 = 余弦 + 1。
     * 配置中的 similarityThreshold 表示「最低余弦」，对应脚本得分阈值为 threshold + 1.0。
     * <p>
     * 注意：SearchHit#getScore() 为 float 基本类型，不能与 null 比较；无得分时一般为 0.0f。
     */
    private List<RetrievalResult> runVectorSearch(String query, String techStack, String category, QueryIntent intent, int size) {
        try {
            String embedText = query != null && !query.isBlank() ? query : "技术文档检索";
            Embedding emb = embeddingModel.embed(embedText).content();
            List<Float> qv = emb.vectorAsList();
            if (qv == null || qv.isEmpty()) {
                return Collections.emptyList();
            }

            Map<String, JsonData> params = new HashMap<>();
            params.put("query_vector", JsonData.of(qv));

            // 仅对存在 embedding 字段的文档打分，避免 painless 对缺失字段报错
            Query filterBool = Query.of(q -> q.bool(b -> {
                b.filter(f -> f.exists(e -> e.field("embedding")));
                applyTechStackFilter(b, techStack);
                applyCategoryFilter(b, category, intent);
                return b;
            }));
            // ES 的 script_score 查询对象（与下方命中得分 hitScore 区分，避免同方法内变量重名）
            Query vectorScriptQuery = Query.of(q -> q.scriptScore(ss -> ss
                    .query(filterBool)
                    .script(s -> s.inline(in -> in
                            .lang("painless")
                            .source("cosineSimilarity(params.query_vector, 'embedding') + 1.0")
                            .params(params)
                    ))
            ));

            NativeQuery nq = NativeQuery.builder()
                    .withQuery(vectorScriptQuery)
                    .withPageable(PageRequest.of(0, size))
                    .build();

            SearchHits<TechDocument> hits = elasticsearchOperations.search(nq, TechDocument.class);
            double minCos = systemConfig.getRetrieval().getSimilarityThreshold();
            double minScriptScore = minCos + 1.0;

            List<RetrievalResult> out = new ArrayList<>();
            for (SearchHit<TechDocument> h : hits) {
                float hitScore = h.getScore();
                if (hitScore < minScriptScore) {
                    continue;
                }
                // 还原余弦：脚本里加了 1.0
                double cos = hitScore - 1.0;
                RetrievalResult r = convertHit(h, cos, "VECTOR");
                r.setVectorScore(cos);
                out.add(r);
            }
            return out;
        } catch (Exception e) {
            log.warn("向量检索失败，降级为仅 BM25: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 构造 BM25 bool 查询：must 为 multi_match 或 match_all；filter 技术栈/类别；should 按意图加权 category。
     */
    private Query buildBm25Query(String query, String techStack, String category, QueryIntent intent) {
        return Query.of(q -> q.bool(b -> {
            boolean hasQ = query != null && !query.trim().isEmpty();
            if (hasQ) {
                b.must(m -> m.multiMatch(mm -> mm
                        .query(query.trim())
                        .fields("title^2.5", "content^1.5", "bm25Content^1.0", "summary^1.2")
                        .type(TextQueryType.BestFields)
                        .fuzziness("AUTO")
                ));
            } else {
                b.must(m -> m.matchAll(ma -> ma));
            }
            applyTechStackFilter(b, techStack);
            applyCategoryFilter(b, category, intent);
            applyIntentBoosts(b, category, intent);
            return b;
        }));
    }

    /** 技术栈作为 Should Boost 而不是 Filter，这样不匹配也能搜到，只是匹配的排前面 */
    private void applyTechStackFilter(BoolQuery.Builder b, String techStack) {
        if (techStack != null && !techStack.isBlank()) {
            b.should(s -> s.term(t -> t.field("techStack").value(techStack).boost(3.0f)));
            b.minimumShouldMatch("0");
        }
    }

    /** 用户显式指定类别时，用 filter 限定 category */
    private void applyCategoryFilter(BoolQuery.Builder b, String category, QueryIntent intent) {
        if (category != null && !category.isBlank()) {
            b.filter(f -> f.term(t -> t.field("category").value(category)));
        }
    }

    /**
     * 未指定 category 时，根据意图对相应 category 做 should + boost（minimum_should_match=0，不强制匹配）。
     */
    private void applyIntentBoosts(BoolQuery.Builder b, String explicitCategory, QueryIntent intent) {
        if (explicitCategory != null && !explicitCategory.isBlank()) {
            b.minimumShouldMatch("0");
            return;
        }
        if (intent == null) {
            b.minimumShouldMatch("0");
            return;
        }
        switch (intent) {
            case CONFIG_QUERY -> {
                b.should(s -> s.term(t -> t.field("category").value("CONFIG").boost(2.2f)));
                b.minimumShouldMatch("0");
            }
            case API_RECOMMENDATION -> {
                b.should(s -> s.term(t -> t.field("category").value("API").boost(2.2f)));
                b.minimumShouldMatch("0");
            }
            case TROUBLESHOOTING -> {
                b.should(s -> s.term(t -> t.field("category").value("TROUBLESHOOTING").boost(2.2f)));
                b.minimumShouldMatch("0");
            }
            case GENERAL_KNOWLEDGE -> {
                b.should(s -> s.term(t -> t.field("category").value("BEST_PRACTICE").boost(1.4f)));
                b.should(s -> s.term(t -> t.field("category").value("TUTORIAL").boost(1.4f)));
                b.minimumShouldMatch("0");
            }
        }
    }

    /** 将 ES SearchHit 转为领域对象 RetrievalResult */
    private RetrievalResult convertHit(SearchHit<TechDocument> hit, double score, String method) {
        TechDocument document = hit.getContent();
        return RetrievalResult.builder()
                .documentId(document.getId())
                .title(document.getTitle())
                .content(document.getContent())
                .summary(document.getSummary())
                .techStack(document.getTechStack())
                .category(document.getCategory())
                .tags(document.getTags())
                .source(document.getSource())
                .score(score)
                .retrievalMethod(method)
                .build();
    }

    /** 清空内存检索缓存（例如索引全量重建后调用） */
    public void clearCache() {
        cache.clear();
        log.info("检索缓存已清除");
    }
}
