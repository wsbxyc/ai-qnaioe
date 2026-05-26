package com.tech.assistant;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.elasticsearch.repository.config.EnableElasticsearchRepositories;

/**
 * 技术助手应用入口
 * 企业级智能技术助手系统
 */
@SpringBootApplication
@EnableElasticsearchRepositories(basePackages = "com.tech.assistant.repository")
public class TechAssistantApplication {

    /**
     * 应用启动入口
     * @param args 命令行参数
     */
    public static void main(String[] args) {
        SpringApplication.run(TechAssistantApplication.class, args);
    }
}