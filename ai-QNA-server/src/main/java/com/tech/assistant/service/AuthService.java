package com.tech.assistant.service;

import com.tech.assistant.dto.AuthRequest;
import com.tech.assistant.dto.AuthResponse;
import com.tech.assistant.model.User;
import com.tech.assistant.repository.UserRepository;
import com.tech.assistant.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

/**
 * 用户认证服务
 * 处理用户注册、登录和用户信息查询
 */
@Service
@RequiredArgsConstructor
public class AuthService {

    /**
     * 用户数据访问层
     */
    private final UserRepository userRepository;

    /**
     * 密码编码器
     */
    private final PasswordEncoder passwordEncoder;

    /**
     * JWT工具类
     */
    private final JwtUtil jwtUtil;

    /**
     * 用户注册
     * @param request 注册请求（包含用户名、密码、邮箱）
     * @return 注册响应（包含JWT token、用户信息）
     */
    public AuthResponse register(AuthRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            return AuthResponse.builder()
                    .success(false)
                    .message("用户名已存在")
                    .build();
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .email(request.getEmail())
                .build();

        user = userRepository.save(user);

        String token = jwtUtil.generateToken(user.getUsername(), user.getId());

        return AuthResponse.builder()
                .success(true)
                .token(token)
                .userId(user.getId())
                .username(user.getUsername())
                .message("注册成功")
                .build();
    }

    /**
     * 用户登录
     * @param request 登录请求（包含用户名、密码）
     * @return 登录响应（包含JWT token、用户信息）
     */
    public AuthResponse login(AuthRequest request) {
        User user = userRepository.findByUsername(request.getUsername())
                .orElse(null);

        if (user == null) {
            return AuthResponse.builder()
                    .success(false)
                    .message("用户不存在")
                    .build();
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            return AuthResponse.builder()
                    .success(false)
                    .message("密码错误")
                    .build();
        }

        String token = jwtUtil.generateToken(user.getUsername(), user.getId());

        return AuthResponse.builder()
                .success(true)
                .token(token)
                .userId(user.getId())
                .username(user.getUsername())
                .message("登录成功")
                .build();
    }

    /**
     * 根据用户ID获取用户信息
     * @param userId 用户ID
     * @return 用户信息（若不存在则返回null）
     */
    public User getUserById(Long userId) {
        return userRepository.findById(userId).orElse(null);
    }
}
