package com.tech.assistant.service;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.tech.assistant.model.QueryIntent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

/**
 * 缓存服务
 * 提供本地缓存（Caffeine）和分布式缓存（Redis）的双层缓存支持
 */
@Slf4j
@Service
public class CacheService {

    /**
     * Redis模板
     */
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    /**
     * 是否启用缓存（默认启用）
     */
    @Value("${tech.assistant.retrieval.cache-enabled:true}")
    private boolean cacheEnabled;

    /**
     * 是否启用Redis缓存（默认启用）
     */
    @Value("${tech.assistant.retrieval.redis-cache-enabled:true}")
    private boolean redisCacheEnabled;

    /**
     * 缓存过期时间（秒，默认3600秒）
     */
    @Value("${tech.assistant.retrieval.cache-ttl-seconds:3600}")
    private int cacheTtlSeconds;

    /**
     * 本地Caffeine缓存（最多5000条，10分钟过期）
     */
    private final Cache<String, String> localCache = Caffeine.newBuilder()
            .maximumSize(5000)
            .expireAfterWrite(10, TimeUnit.MINUTES)
            .build();

    /**
     * 构建答案缓存键
     * @param query 查询问题
     * @param techStack 技术栈
     * @param category 分类
     * @param intent 查询意图
     * @return 组合缓存键
     */
    public static String buildAnswerCacheKey(String query, String techStack, String category, QueryIntent intent) {
        return String.join("|",
                query != null ? query : "",
                techStack != null ? techStack : "",
                category != null ? category : "",
                intent != null ? intent.name() : "");
    }

    /**
     * 获取缓存的答案
     * @param compoundKey 组合缓存键
     * @return 缓存的答案（未找到返回null）
     */
    public String getCachedAnswer(String compoundKey) {
        if (!cacheEnabled) {
            return null;
        }
        String redisKey = "tech-qa:" + hashKey(compoundKey);

        String local = localCache.getIfPresent(compoundKey);
        if (local != null) {
            log.debug("命中本地答案缓存");
            return local;
        }

        if (redisCacheEnabled) {
            try {
                Object redis = redisTemplate.opsForValue().get(redisKey);
                if (redis != null) {
                    log.debug("命中 Redis 答案缓存");
                    String answer = redis.toString();
                    localCache.put(compoundKey, answer);
                    return answer;
                }
            } catch (Exception e) {
                log.warn("Redis 答案缓存读取失败（已降级为仅本地）: {}", e.getMessage());
            }
        }

        return null;
    }

    /**
     * 缓存答案
     * @param compoundKey 组合缓存键
     * @param answer 答案内容
     */
    public void cacheAnswer(String compoundKey, String answer) {
        if (!cacheEnabled) {
            return;
        }
        String redisKey = "tech-qa:" + hashKey(compoundKey);
        localCache.put(compoundKey, answer);

        if (redisCacheEnabled) {
            try {
                redisTemplate.opsForValue().set(redisKey, answer, cacheTtlSeconds, TimeUnit.SECONDS);
            } catch (Exception e) {
                log.warn("Redis 答案缓存写入失败: {}", e.getMessage());
            }
        }
    }

    /**
     * 清空本地缓存
     */
    public void clearCache() {
        localCache.invalidateAll();
        log.info("本地答案缓存已清空");
    }

    /**
     * 获取缓存统计信息
     * @return 缓存统计信息
     */
    public CacheStats getCacheStats() {
        return CacheStats.builder()
                .localCacheSize(localCache.estimatedSize())
                .cacheEnabled(cacheEnabled)
                .cacheTtl(cacheTtlSeconds)
                .build();
    }

    /**
     * 计算键的哈希值
     * @param key 原始键
     * @return 哈希值
     */
    private static int hashKey(String key) {
        return key.hashCode();
    }

    /**
     * 缓存统计信息
     */
    @lombok.Data
    @lombok.Builder
    public static class CacheStats {
        /**
         * 本地缓存大小
         */
        private long localCacheSize;
        /**
         * 缓存是否启用
         */
        private boolean cacheEnabled;
        /**
         * 缓存过期时间（秒）
         */
        private int cacheTtl;
    }
}
