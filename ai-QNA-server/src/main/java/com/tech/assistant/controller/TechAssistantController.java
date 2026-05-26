package com.tech.assistant.controller;

import com.tech.assistant.model.IntentResult;
import com.tech.assistant.model.RetrievalResult;
import com.tech.assistant.model.TechResponse;
import com.tech.assistant.service.IntentRouter;
import com.tech.assistant.service.TechAssistantService;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.constraints.NotBlank;
import java.util.List;

/**
 * 技术助手控制器
 * 提供智能技术问答、意图识别、混合检索等接口
 */
@Slf4j
@RestController
@RequestMapping("/api/tech-assistant")
@Validated
public class        TechAssistantController {

    /**
     * 技术助手服务
     */
    @Autowired
    private TechAssistantService techAssistantService;

    /**
     * 意图路由服务
     */
    @Autowired
    private IntentRouter intentRouter;

    /**
     * 智能技术问答
     * @param request 技术查询请求
     * @return 技术助手响应
     */
    @PostMapping("/query")
    public ResponseEntity<TechResponse> query(@RequestBody @Validated TechRequest request) {
        log.info("收到技术查询请求：{}", request.getQuery());

        // 1. 智能路由识别意图
        IntentResult intentResult = intentRouter.routeIntent(request.getQuery());
        
        // 2. 调用技术助手服务
        TechResponse response = techAssistantService.processQuery(
            request.getQuery(), 
            intentResult, 
            request.getTechStack(), 
            request.getCategory()
        );

        return ResponseEntity.ok(response);
    }

    /**
     * 意图识别测试接口
     * @param request 意图识别请求
     * @return 意图识别结果
     */
    @PostMapping("/intent")
    public ResponseEntity<IntentResult> detectIntent(@RequestBody @Validated IntentRequest request) {
        log.info("意图识别测试：{}", request.getQuery());
        
        IntentResult intentResult = intentRouter.routeIntent(request.getQuery());
        
        return ResponseEntity.ok(intentResult);
    }

    /**
     * 混合检索测试接口
     * @param request 检索请求
     * @return 检索响应
     */
    @PostMapping("/retrieve")
    public ResponseEntity<RetrievalResponse> retrieve(@RequestBody @Validated RetrievalRequest request) {
        log.info("混合检索测试：{}", request.getQuery());
        
        IntentResult intentResult = intentRouter.routeIntent(request.getQuery());
        List<RetrievalResult> results = techAssistantService.hybridRetrieve(
            request.getQuery(),
            request.getTechStack(),
            request.getCategory(),
            intentResult.getIntent()
        );
        
        RetrievalResponse response = RetrievalResponse.builder()
            .success(true)
            .results(results)
            .count(results.size())
            .build();
            
        return ResponseEntity.ok(response);
    }

    /**
     * 健康检查
     * @return 健康检查响应
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("企业级智能技术助手服务运行正常");
    }

    /**
     * 技术查询请求
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TechRequest {
        /**
         * 查询问题
         */
        @NotBlank(message = "查询问题不能为空")
        private String query;
        
        /**
         * 技术栈（Spring Boot, Docker, Java等）
         */
        private String techStack;

        /**
         * 分类（CONFIG, API, TROUBLESHOOTING等）
         */
        private String category;

        /**
         * 会话ID
         */
        private String sessionId;
    }

    /**
     * 意图识别请求
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class IntentRequest {
        /**
         * 查询问题
         */
        @NotBlank(message = "查询问题不能为空")
        private String query;
    }

    /**
     * 检索请求
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RetrievalRequest {
        /**
         * 查询问题
         */
        @NotBlank(message = "查询问题不能为空")
        private String query;
        
        /**
         * 技术栈
         */
        private String techStack;

        /**
         * 分类
         */
        private String category;
    }

    /**
     * 检索响应
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RetrievalResponse {
        /**
         * 是否成功
         */
        private boolean success;

        /**
         * 检索结果列表
         */
        private List<RetrievalResult> results;

        /**
         * 结果数量
         */
        private int count;
    }
}