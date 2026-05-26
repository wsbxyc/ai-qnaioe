package com.tech.assistant.controller;

import com.tech.assistant.dto.AuthRequest;
import com.tech.assistant.dto.AuthResponse;
import com.tech.assistant.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 认证控制器
 * 处理用户注册和登录
 */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@CrossOrigin(originPatterns = {"http://localhost:*", "http://127.0.0.1:*"})
public class AuthController {

    /**
     * 认证服务
     */
    private final AuthService authService;

    /**
     * 用户注册
     * @param request 注册请求
     * @return 认证响应
     */
    @PostMapping("/register")
    public AuthResponse register(@RequestBody AuthRequest request) {
        return authService.register(request);
    }

    /**
     * 用户登录
     * @param request 登录请求
     * @return 认证响应
     */
    @PostMapping("/login")
    public AuthResponse login(@RequestBody AuthRequest request) {
        return authService.login(request);
    }
}
