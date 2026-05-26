package com.tech.assistant.service;

import com.tech.assistant.dto.ChatSessionRequest;
import com.tech.assistant.dto.ChatSessionResponse;
import com.tech.assistant.model.ChatSession;
import com.tech.assistant.model.User;
import com.tech.assistant.repository.ChatSessionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 会话服务
 * 处理聊天会话的创建、查询、更新和删除
 */
@Service
@RequiredArgsConstructor
public class ChatSessionService {

    /**
     * 会话数据访问层
     */
    private final ChatSessionRepository chatSessionRepository;

    /**
     * 日期时间格式化器
     */
    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    /**
     * 创建新会话
     * @param user 用户
     * @param request 会话请求（包含标题、消息）
     * @return 会话响应
     */
    public ChatSessionResponse createSession(User user, ChatSessionRequest request) {
        ChatSession session = ChatSession.builder()
                .user(user)
                .title(request.getTitle())
                .messages(request.getMessages())
                .build();

        session = chatSessionRepository.save(session);
        return convertToResponse(session);
    }

    /**
     * 获取用户的所有会话（按更新时间倒序）
     * @param user 用户
     * @return 会话列表
     */
    public List<ChatSessionResponse> getSessionsByUser(User user) {
        return chatSessionRepository.findByUserOrderByUpdatedAtDesc(user)
                .stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    /**
     * 更新会话
     * @param sessionId 会话ID
     * @param user 用户（用于权限验证）
     * @param request 会话更新请求
     * @return 更新后的会话（无权限或不存在返回null）
     */
    public ChatSessionResponse updateSession(Long sessionId, User user, ChatSessionRequest request) {
        ChatSession session = chatSessionRepository.findById(sessionId).orElse(null);
        if (session == null || !session.getUser().getId().equals(user.getId())) {
            return null;
        }

        if (request.getTitle() != null) {
            session.setTitle(request.getTitle());
        }
        if (request.getMessages() != null) {
            session.setMessages(request.getMessages());
        }

        session = chatSessionRepository.save(session);
        return convertToResponse(session);
    }

    /**
     * 删除会话
     * @param sessionId 会话ID
     * @param user 用户（用于权限验证）
     * @return 是否删除成功
     */
    public boolean deleteSession(Long sessionId, User user) {
        ChatSession session = chatSessionRepository.findById(sessionId).orElse(null);
        if (session == null || !session.getUser().getId().equals(user.getId())) {
            return false;
        }
        chatSessionRepository.delete(session);
        return true;
    }

    /**
     * 将会话实体转换为响应对象
     * @param session 会话实体
     * @return 会话响应对象
     */
    private ChatSessionResponse convertToResponse(ChatSession session) {
        return ChatSessionResponse.builder()
                .id(session.getId())
                .title(session.getTitle())
                .messages(session.getMessages())
                .createdAt(session.getCreatedAt() != null ? session.getCreatedAt().format(formatter) : null)
                .updatedAt(session.getUpdatedAt() != null ? session.getUpdatedAt().format(formatter) : null)
                .build();
    }
}
