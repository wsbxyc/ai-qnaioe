package com.tech.assistant.model;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.*;

import java.time.LocalDate;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(indexName = "tech_documents")
@Setting(settingPath = "/elasticsearch/tech-settings.json")
public class TechDocument {
    
    @Id
    private String id;
    
    // 文档基本信息（tech_text 在 tech-settings.json 中定义，默认 standard，便于无 IK 插件环境）
    @Field(type = FieldType.Text, analyzer = "tech_text", searchAnalyzer = "tech_text")
    private String title;
    
    @Field(type = FieldType.Text, analyzer = "tech_text", searchAnalyzer = "tech_text")
    private String content;
    
    @Field(type = FieldType.Keyword)
    private String summary;
    
    // 技术栈分类
    @Field(type = FieldType.Keyword)
    private String techStack; // Spring Boot, Docker, Java等
    
    @Field(type = FieldType.Keyword)
    private String category; // CONFIG, API, TROUBLESHOOTING等
    
    @Field(type = FieldType.Keyword)
    private List<String> tags;
    
    // 向量嵌入（与 text-embedding-v4 默认 1024 维对齐，可通过数据采集脚本批量写入）
    @Field(type = FieldType.Dense_Vector, dims = 1024)
    private float[] embedding;
    
    // 元数据
    @Field(type = FieldType.Keyword)
    private String source; // 来源：官方文档、社区、内部等
    
    @Field(type = FieldType.Keyword)
    private String language; // 语言：中文、英文等

    /**
     * 与 Elasticsearch 中常见存法一致：多为 {@code yyyy-MM-dd} 日期。
     * 使用 {@link LocalDateTime} 时，若索引里只有日期无时间，反序列化会抛 ConversionException。
     */
    @Field(type = FieldType.Date, format = {}, pattern = "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss.SSSXXX||epoch_millis")
    private LocalDate createdAt;

    @Field(type = FieldType.Date, format = {}, pattern = "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss.SSSXXX||epoch_millis")
    private LocalDate updatedAt;
    @Field(type = FieldType.Integer)
    private int popularity; // 热门程度
    
    @Field(type = FieldType.Double)
    private double qualityScore; // 质量评分
    
    // BM25相关字段
    @Field(type = FieldType.Text)
    private String bm25Content;
    
    // 用于混合检索的权重
    @Field(type = FieldType.Double)
    private double retrievalWeight;
}