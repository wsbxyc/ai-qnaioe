package com.tech.assistant.controller;

import com.tech.assistant.dto.ChatSessionRequest;
import com.tech.assistant.dto.ChatSessionResponse;
import com.tech.assistant.model.User;
import com.tech.assistant.service.AuthService;
import com.tech.assistant.service.ChatSessionService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 会话控制器
 * 处理聊天会话的CRUD操作
 */
@RestController
@RequestMapping("/api/sessions")
@RequiredArgsConstructor
@CrossOrigin(originPatterns = {"http://localhost:*", "http://127.0.0.1:*"})
public class ChatSessionController {

    /**
     * 会话服务
     */
    private final ChatSessionService chatSessionService;

    /**
     * 认证服务
     */
    private final AuthService authService;

    /**
     * 获取用户的所有会话
     * @param authentication 认证信息
     * @return 响应结果
     */
    @GetMapping
    public Map<String, Object> getSessions(Authentication authentication) {
        Map<String, Object> result = new HashMap<>();
        try {
            Long userId = (Long) authentication.getPrincipal();
            User user = authService.getUserById(userId);
            if (user == null) {
                result.put("success", false);
                result.put("message", "用户不存在");
                return result;
            }

            List<ChatSessionResponse> sessions = chatSessionService.getSessionsByUser(user);
            result.put("success", true);
            result.put("data", sessions);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }
        return result;
    }

    /**
     * 创建新会话
     * @param request 会话请求
     * @param authentication 认证信息
     * @return 响应结果
     */
    @PostMapping
    public Map<String, Object> createSession(@RequestBody ChatSessionRequest request, Authentication authentication) {
        Map<String, Object> result = new HashMap<>();
        try {
            Long userId = (Long) authentication.getPrincipal();
            User user = authService.getUserById(userId);
            if (user == null) {
                result.put("success", false);
                result.put("message", "用户不存在");
                return result;
            }

            ChatSessionResponse session = chatSessionService.createSession(user, request);
            result.put("success", true);
            result.put("data", session);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }
        return result;
    }

    /**
     * 更新会话
     * @param id 会话ID
     * @param request 会话请求
     * @param authentication 认证信息
     * @return 响应结果
     */
    @PutMapping("/{id}")
    public Map<String, Object> updateSession(@PathVariable("id") Long id, 
                                             @RequestBody ChatSessionRequest request, 
                                             Authentication authentication) {
        Map<String, Object> result = new HashMap<>();
        try {
            Long userId = (Long) authentication.getPrincipal();
            User user = authService.getUserById(userId);
            if (user == null) {
                result.put("success", false);
                result.put("message", "用户不存在");
                return result;
            }

            ChatSessionResponse session = chatSessionService.updateSession(id, user, request);
            if (session == null) {
                result.put("success", false);
                result.put("message", "会话不存在或无权限");
                return result;
            }
            result.put("success", true);
            result.put("data", session);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }
        return result;
    }

    /**
     * 删除会话
     * @param id 会话ID
     * @param authentication 认证信息
     * @return 响应结果
     */
    @DeleteMapping("/{id}")
    public Map<String, Object> deleteSession(@PathVariable("id") Long id, Authentication authentication) {
        Map<String, Object> result = new HashMap<>();
        try {
            Long userId = (Long) authentication.getPrincipal();
            User user = authService.getUserById(userId);
            if (user == null) {
                result.put("success", false);
                result.put("message", "用户不存在");
                return result;
            }

            boolean deleted = chatSessionService.deleteSession(id, user);
            result.put("success", deleted);
            result.put("message", deleted ? "删除成功" : "删除失败");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }
        return result;
    }
}
