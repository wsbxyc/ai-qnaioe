package com.tech.assistant.service;

import com.tech.assistant.model.TechDocument;
import dev.langchain4j.model.embedding.EmbeddingModel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

/**
 * 技术知识库初始化服务
 * 应用启动时自动创建示例技术文档并保存到Elasticsearch
 */
@Slf4j
@Service
public class TechKnowledgeInitializer implements CommandLineRunner {

    /**
     * Elasticsearch操作对象
     */
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;

    /**
     * 嵌入模型
     */
    @Autowired
    private EmbeddingModel embeddingModel;
    
    /**
     * 应用启动时执行
     * @param args 命令行参数
     * @throws Exception 异常
     */
    @Override
    public void run(String... args) throws Exception {
        log.info("开始初始化技术知识库...");
        
        // 创建示例技术文档
        List<TechDocument> techDocuments = createSampleTechDocuments();
        
        // 保存到Elasticsearch（如果已配置）
        try {
            for (TechDocument doc : techDocuments) {
                enrichEmbedding(doc);
                elasticsearchOperations.save(doc);
            }
            log.info("技术知识库初始化完成！共添加 {} 篇技术文档（含向量字段）", techDocuments.size());
        } catch (Exception e) {
            log.warn("Elasticsearch未配置或连接失败，跳过知识库初始化: {}", e.getMessage());
        }
    }

    /**
     * 为文档生成向量
     * @param doc 技术文档
     */
    private void enrichEmbedding(TechDocument doc) {
        try {
            String title = doc.getTitle() != null ? doc.getTitle() : "";
            String content = doc.getContent() != null ? doc.getContent() : "";
            String slice = content.length() > 2000 ? content.substring(0, 2000) : content;
            String text = title + "\n" + slice;
            List<Float> vec = embeddingModel.embed(text).content().vectorAsList();
            float[] arr = new float[vec.size()];
            for (int i = 0; i < vec.size(); i++) {
                arr[i] = vec.get(i);
            }
            doc.setEmbedding(arr);
        } catch (Exception e) {
            log.warn("文档 {} 向量生成失败（将仅参与 BM25）: {}", doc.getId(), e.getMessage());
        }
    }
    
    /**
     * 创建示例技术文档
     * @return 技术文档列表
     */
    private List<TechDocument> createSampleTechDocuments() {
        return Arrays.asList(
            // Spring Boot配置文档
            TechDocument.builder()
                .id("spring-boot-config-1")
                .title("Spring Boot多数据源配置")
                .content("Spring Boot配置多数据源需要在application.yml中定义多个数据源配置，并使用@Primary注解指定主数据源。示例配置：spring.datasource.primary.url=jdbc:mysql://localhost:3306/db1, spring.datasource.secondary.url=jdbc:mysql://localhost:3306/db2")
                .summary("Spring Boot多数据源配置方法和示例")
                .techStack("Spring Boot")
                .category("CONFIG")
                .tags(Arrays.asList("多数据源", "配置", "数据库"))
                .source("Spring Boot官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(85)
                .qualityScore(0.9)
                .build(),
            
            // Docker配置文档
            TechDocument.builder()
                .id("docker-config-1")
                .title("Docker Compose网络配置")
                .content("Docker Compose支持多种网络模式配置。在docker-compose.yml中可以使用networks字段定义自定义网络，services字段中指定网络连接。示例：networks: app-network: driver: bridge")
                .summary("Docker Compose网络配置详解")
                .techStack("Docker")
                .category("CONFIG")
                .tags(Arrays.asList("网络", "Compose", "容器"))
                .source("Docker官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(78)
                .qualityScore(0.85)
                .build(),
            
            // Java API文档
            TechDocument.builder()
                .id("java-api-1")
                .title("Java Stream API使用指南")
                .content("Java Stream API提供函数式编程能力。常用操作包括filter过滤、map转换、reduce归约、collect收集等。示例：List<String> result = list.stream().filter(s -> s.length() > 3).collect(Collectors.toList());")
                .summary("Java Stream API完整使用教程")
                .techStack("Java")
                .category("API")
                .tags(Arrays.asList("Stream", "函数式", "Java 8"))
                .source("Java官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(92)
                .qualityScore(0.95)
                .build(),
            
            // Vue配置文档
            TechDocument.builder()
                .id("vue-config-1")
                .title("Vue 3 Composition API配置")
                .content("Vue 3 Composition API使用setup函数替代了Options API。可以在setup中使用ref、reactive等响应式API，并通过return暴露给模板使用。")
                .summary("Vue 3 Composition API配置和使用")
                .techStack("Vue")
                .category("CONFIG")
                .tags(Arrays.asList("Vue 3", "Composition API", "前端"))
                .source("Vue官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(80)
                .qualityScore(0.88)
                .build(),
            
            // MySQL配置文档
            TechDocument.builder()
                .id("mysql-config-1")
                .title("MySQL性能优化配置")
                .content("MySQL性能优化包括配置合适的缓冲区大小、优化查询语句、创建合适的索引等。关键配置参数：innodb_buffer_pool_size、query_cache_size、max_connections等。")
                .summary("MySQL数据库性能优化配置指南")
                .techStack("MySQL")
                .category("CONFIG")
                .tags(Arrays.asList("性能优化", "配置", "数据库"))
                .source("MySQL官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(75)
                .qualityScore(0.82)
                .build(),
            
            // Redis API文档
            TechDocument.builder()
                .id("redis-api-1")
                .title("Redis Java客户端API使用")
                .content("使用Jedis或Lettuce客户端连接Redis。常用操作：set/get字符串、hset/hget哈希、lpush/lpop列表、sadd/smembers集合等。")
                .summary("Redis Java客户端API完整指南")
                .techStack("Redis")
                .category("API")
                .tags(Arrays.asList("Redis", "Java客户端", "缓存"))
                .source("Redis官方文档")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(70)
                .qualityScore(0.8)
                .build(),
            
            // 故障排除文档
            TechDocument.builder()
                .id("troubleshooting-1")
                .title("Spring Boot应用启动失败排查")
                .content("Spring Boot应用启动失败常见原因：依赖冲突、配置错误、端口占用、数据库连接失败等。排查步骤：检查启动日志、验证配置文件、测试数据库连接、检查依赖版本兼容性。")
                .summary("Spring Boot应用启动问题排查指南")
                .techStack("Spring Boot")
                .category("TROUBLESHOOTING")
                .tags(Arrays.asList("启动失败", "排查", "问题解决"))
                .source("社区经验")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(88)
                .qualityScore(0.9)
                .build(),
            
            // 最佳实践文档
            TechDocument.builder()
                .id("best-practice-1")
                .title("微服务架构设计最佳实践")
                .content("微服务架构设计最佳实践包括：单一职责原则、服务自治、API网关模式、服务发现、配置中心、熔断器模式、分布式追踪等。")
                .summary("微服务架构设计完整最佳实践指南")
                .techStack("Spring Boot")
                .category("BEST_PRACTICE")
                .tags(Arrays.asList("微服务", "架构", "最佳实践"))
                .source("行业标准")
                .language("中文")
                .createdAt(LocalDate.now())
                .updatedAt(LocalDate.now())
                .popularity(95)
                .qualityScore(0.95)
                .build()
        );
    }
}