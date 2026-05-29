#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 模型测试脚本
用于测试 Embedding 和 Rerank 模型的连接和功能
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

if sys.platform == "win32":
    try:
        os.system("chcp 65001")
    except:
        pass
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass


def make_post_request(url: str, headers: dict, payload: dict, timeout: int = 30) -> dict:
    """发送 POST 请求"""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return {
                "status": "success",
                "data": json.loads(response.read().decode('utf-8'))
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "error": f"HTTP Error {e.code}: {e.reason}",
            "details": e.read().decode('utf-8') if e.fp else ""
        }
    except urllib.error.URLError as e:
        return {
            "status": "error",
            "error": f"URL Error: {e.reason}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def test_embedding_model(base_url: str, model: str, api_key: str, test_text: str = "这是一段测试文本"):
    """测试 Embedding 模型"""
    print(f"\n{'='*60}")
    print(f"Testing Embedding Model")
    print(f"{'='*60}")
    print(f"Endpoint: {base_url}")
    print(f"Model: {model}")

    if not api_key or "your_" in api_key or api_key == "your_api_key_here":
        print("WARNING: API Key not configured, using mock test")
        return {"status": "mock", "embedding": [0.0] * 768}

    try:
        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": test_text,
            "encoding_format": "float"
        }

        print(f"\nSending request...")
        result = make_post_request(url, headers, payload)

        if result["status"] == "success":
            response_data = result["data"]
            if "data" in response_data and len(response_data["data"]) > 0:
                embedding = response_data["data"][0]["embedding"]
                print(f"SUCCESS: Embedding generated!")
                print(f"   Vector dimension: {len(embedding)}")
                print(f"   First 5 values: {embedding[:5]}")
                return {"status": "success", "embedding": embedding}
            else:
                print(f"ERROR: Invalid response format: {response_data}")
                return {"status": "error", "error": "Invalid response format"}
        else:
            print(f"ERROR: Request failed: {result.get('error')}")
            return {"status": "error", "error": result.get("error")}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "error": str(e)}


def test_rerank_model(base_url: str, model: str, api_key: str, query: str = "主角的身份", documents: list = None):
    """测试 Rerank 模型"""
    if documents is None:
        documents = [
            "主角是一个普通的少年",
            "这个世界有修仙者存在",
            "主角获得了神秘系统",
            "反派正在追杀主角"
        ]

    print(f"\n{'='*60}")
    print(f"Testing Rerank Model")
    print(f"{'='*60}")
    print(f"Endpoint: {base_url}")
    print(f"Model: {model}")

    if not api_key or "your_" in api_key or api_key == "your_rerank_api_key_here":
        print("WARNING: API Key not configured, using mock test")
        return {"status": "mock", "results": [(0, 0.9), (1, 0.8), (2, 0.7), (3, 0.6)]}

    try:
        url = f"{base_url}/rerank"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "query": query,
            "documents": documents,
            "top_n": min(5, len(documents))
        }

        print(f"\nSending request...")
        print(f"Query: {query}")
        print(f"Documents: {documents}")

        result = make_post_request(url, headers, payload)

        if result["status"] == "success":
            response_data = result["data"]
            if "results" in response_data:
                print(f"SUCCESS: Rerank results generated!")
                for r in response_data["results"]:
                    print(f"   Index: {r['index']}, Score: {r['relevance_score']:.4f}")
                return {"status": "success", "results": response_data["results"]}
            else:
                print(f"ERROR: Invalid response format: {response_data}")
                return {"status": "error", "error": "Invalid response format"}
        else:
            print(f"ERROR: Request failed: {result.get('error')}")
            return {"status": "error", "error": result.get("error")}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "error": str(e)}


def cosine_similarity(vec1: list, vec2: list) -> float:
    """计算余弦相似度"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def test_vector_search(embedding1: list, embedding2: list):
    """测试向量搜索（相似度计算）"""
    print(f"\n{'='*60}")
    print(f"Testing Vector Search")
    print(f"{'='*60}")

    if len(embedding1) != len(embedding2):
        print(f"ERROR: Vector dimension mismatch: {len(embedding1)} vs {len(embedding2)}")
        return

    similarity = cosine_similarity(embedding1, embedding2)
    print(f"Cosine similarity: {similarity:.4f}")

    if similarity > 0.9:
        print(f"   Two texts are highly similar")
    elif similarity > 0.7:
        print(f"   Two texts are similar")
    elif similarity > 0.5:
        print(f"   Two texts have some correlation")
    else:
        print(f"   Two texts are not similar")


def main():
    print("="*60)
    print("RAG Model Testing Tool")
    print("="*60)

    project_path = Path.cwd()
    env_file = project_path / ".env"

    config = {}
    if env_file.exists():
        print(f"\nLoading config from {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    else:
        print(f"\nWARNING: .env file not found, using .env.example")
        example_file = project_path / ".env.example"
        if example_file.exists():
            with open(example_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()

    print("\nCurrent Config:")
    print(f"  EMBED_BASE_URL: {config.get('EMBED_BASE_URL', 'N/A')}")
    print(f"  EMBED_MODEL: {config.get('EMBED_MODEL', 'N/A')}")
    embed_key = config.get('EMBED_API_KEY', '')
    print(f"  EMBED_API_KEY: {'***' + embed_key[-4:] if embed_key and len(embed_key) > 4 else 'N/A'}")
    print(f"  RERANK_BASE_URL: {config.get('RERANK_BASE_URL', 'N/A')}")
    print(f"  RERANK_MODEL: {config.get('RERANK_MODEL', 'N/A')}")
    rerank_key = config.get('RERANK_API_KEY', '')
    print(f"  RERANK_API_KEY: {'***' + rerank_key[-4:] if rerank_key and len(rerank_key) > 4 else 'N/A'}")

    embed_result = test_embedding_model(
        config.get('EMBED_BASE_URL', ''),
        config.get('EMBED_MODEL', ''),
        config.get('EMBED_API_KEY', '')
    )

    rerank_result = test_rerank_model(
        config.get('RERANK_BASE_URL', ''),
        config.get('RERANK_MODEL', ''),
        config.get('RERANK_API_KEY', '')
    )

    if embed_result.get("status") == "success" and len(embed_result.get("embedding", [])) > 0:
        test_vector_search(
            embed_result["embedding"],
            embed_result["embedding"]
        )

    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Embedding Model: {'SUCCESS' if embed_result.get('status') == 'success' else 'MOCK' if embed_result.get('status') == 'mock' else 'FAILED'}")
    print(f"Rerank Model: {'SUCCESS' if rerank_result.get('status') == 'success' else 'MOCK' if rerank_result.get('status') == 'mock' else 'FAILED'}")

    if embed_result.get('status') != 'success' and rerank_result.get('status') != 'success':
        print(f"\nPlease configure valid API Key:")
        print(f"1. Edit .env file")
        print(f"2. Fill in EMBED_BASE_URL, EMBED_API_KEY")
        print(f"3. Verify model name EMBED_MODEL is correct")

if __name__ == "__main__":
    main()
