# -*- coding: utf-8 -*-
"""
向量存储模块
优先使用 ChromaDB，未安装时自动降级为 numpy 实现。
对外提供统一接口：add(texts, metadatas) / query(query, top_k)
"""
import os
import json
import numpy as np

EMBED_DIM = 1024  # 阿里云 text-embedding-v3 默认维度


class NumpyVectorStore:
    """基于 numpy 的轻量向量存储，持久化到 JSON 文件"""

    def __init__(self, persist_dir, collection_name="character_knowledge"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(persist_dir, exist_ok=True)
        self.store_path = os.path.join(persist_dir, f"{collection_name}.json")
        self.texts = []
        self.metadatas = []
        self.embeddings = []
        self._load()

    def _load(self):
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.texts = data.get("texts", [])
                self.metadatas = data.get("metadatas", [])
                self.embeddings = [np.array(e, dtype=np.float32) for e in data.get("embeddings", [])]
            except Exception as e:
                print(f"[VectorStore] 加载持久化数据失败: {e}")

    def _save(self):
        try:
            data = {
                "texts": self.texts,
                "metadatas": self.metadatas,
                "embeddings": [e.tolist() for e in self.embeddings],
            }
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"[VectorStore] 持久化失败: {e}")

    def add(self, texts, embeddings, metadatas=None):
        if metadatas is None:
            metadatas = [{} for _ in texts]
        for text, emb, meta in zip(texts, embeddings, metadatas):
            self.texts.append(text)
            self.metadatas.append(meta)
            self.embeddings.append(np.array(emb, dtype=np.float32))
        self._save()

    def query(self, query_embedding, top_k=3, min_score=0.0):
        if not self.embeddings:
            return []
        query_vec = np.array(query_embedding, dtype=np.float32)
        # 余弦相似度
        scores = []
        for emb in self.embeddings:
            dot = np.dot(query_vec, emb)
            norm = np.linalg.norm(query_vec) * np.linalg.norm(emb)
            score = float(dot / norm) if norm > 0 else 0.0
            scores.append(score)
        # 排序
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in indexed[:top_k]:
            if score >= min_score:
                results.append({
                    "text": self.texts[idx],
                    "metadata": self.metadatas[idx],
                    "score": score,
                })
        return results

    def count(self):
        return len(self.texts)

    def clear(self):
        self.texts = []
        self.metadatas = []
        self.embeddings = []
        if os.path.exists(self.store_path):
            os.remove(self.store_path)


class ChromaVectorStore:
    """ChromaDB 向量存储（优先使用）"""

    def __init__(self, persist_dir, collection_name="character_knowledge"):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, texts, embeddings, metadatas=None):
        if metadatas is None:
            metadatas = [{} for _ in texts]
        ids = [f"doc_{i}_{abs(hash(t)) % 100000}" for i, t in enumerate(texts)]
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(self, query_embedding, top_k=3, min_score=0.0):
        if self.collection.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        outputs = []
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            # chroma cosine distance = 1 - cosine_similarity
            score = 1.0 - float(dist)
            if score >= min_score:
                outputs.append({"text": doc, "metadata": meta, "score": score})
        return outputs

    def count(self):
        return self.collection.count()

    def clear(self):
        name = self.collection.name
        self.client.delete_collection(name=name)
        self.collection = self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )


def get_vector_store(persist_dir, collection_name="character_knowledge", prefer_chroma=False):
    """
    工厂函数：默认使用 numpy 实现（稳定、轻量、无原生依赖），
    prefer_chroma=True 时优先尝试 ChromaDB，失败则降级 numpy。
    """
    if prefer_chroma:
        try:
            store = ChromaVectorStore(persist_dir, collection_name)
            print(f"[VectorStore] 使用 ChromaDB ({collection_name})")
            return store
        except Exception as e:
            print(f"[VectorStore] ChromaDB 不可用，降级为 numpy 实现: {e}")
    # 默认使用 numpy 实现（桌面端推荐：稳定、轻量、无DLL依赖）
    store = NumpyVectorStore(persist_dir, collection_name)
    print(f"[VectorStore] 使用 numpy 轻量向量存储 ({collection_name}, {store.count()}条)")
    return store
