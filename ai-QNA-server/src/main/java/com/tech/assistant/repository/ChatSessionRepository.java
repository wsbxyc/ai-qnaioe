package com.tech.assistant.repository;

import com.tech.assistant.model.ChatSession;
import com.tech.assistant.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 聊天会话数据访问层
 * 提供聊天会话相关的数据库操作
 */
@Repository
public interface ChatSessionRepository extends JpaRepository<ChatSession, Long> {
    
    /**
     * 根据用户查询其所有会话，按更新时间倒序排列
     * @param user 用户
     * @return 会话列表
     */
    List<ChatSession> findByUserOrderByUpdatedAtDesc(User user);
}
