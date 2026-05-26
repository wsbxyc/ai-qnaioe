#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

BASE_URL = "http://localhost:8080/api"

def test_chat():
    questions = [
        "感冒发烧吃什么药？",
        "高血压患者应该注意什么？",
        "阿司匹林的副作用有哪些？",
        "糖尿病如何治疗？",
        "布洛芬可以和阿莫西林一起吃吗？"
    ]
    
    session_id = None
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"问：{question}")
        print(f"{'='*60}")
        
        payload = {
            "query": question,
            "sessionId": session_id
        }
        
        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
            result = response.json()
            
            if result.get("success"):
                print(f"答：{result['answer']}")
                session_id = result.get("sessionId")
            else:
                print("回答失败")
        except Exception as e:
            print(f"请求失败：{e}")
        
        print()

if __name__ == "__main__":
    print("开始测试医药 RAG 系统 API...")
    print("\n【测试智能问答】")
    test_chat()
    print("\n测试完成！")
