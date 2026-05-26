package com.tech.assistant.service;

import org.springframework.stereotype.Service;

/**
 * 简单嵌入服务
 */
@Service
public class SimpleEmbeddingService {
    
    public float[] embed(String text) {
        // 返回随机嵌入向量
        float[] embedding = new float[1536];
        for (int i = 0; i < embedding.length; i++) {
            embedding[i] = (float) (Math.random() * 2 - 1);
        }
        return embedding;
    }
}