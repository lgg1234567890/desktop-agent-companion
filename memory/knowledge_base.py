# -*- coding: utf-8 -*-
"""
知识库模块：文档加载、切分、向量化、检索
"""
import os
import re
from .vector_store import get_vector_store
from .embedding_client import EmbeddingClient


class KnowledgeBase:
    def __init__(self, api_key, api_url=None, persist_dir=None, collection_name="character_knowledge"):
        if persist_dir is None:
            persist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "vector_db")
        self.embedder = EmbeddingClient(api_key, api_url)
        self.vector_store = get_vector_store(persist_dir, collection_name)
        self.collection_name = collection_name

    def load_and_index(self, knowledge_dir, force_rebuild=False):
        """
        加载知识目录下的所有 .txt 文件，切分后向量化入库。
        force_rebuild=True 时清空重建。
        返回入库的文档数量。
        """
        if force_rebuild:
            self.vector_store.clear()

        if self.vector_store.count() > 0 and not force_rebuild:
            print(f"[KnowledgeBase] 知识库已有 {self.vector_store.count()} 条记录，跳过构建")
            return self.vector_store.count()

        all_chunks = []
        all_metadatas = []
        if not os.path.exists(knowledge_dir):
            print(f"[KnowledgeBase] 知识目录不存在: {knowledge_dir}")
            return 0

        for filename in os.listdir(knowledge_dir):
            if not filename.endswith(".txt"):
                continue
            filepath = os.path.join(knowledge_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                chunks = self._split_by_paragraph(content)
                for chunk in chunks:
                    all_chunks.append(chunk)
                    all_metadatas.append({"source": filename})
            except Exception as e:
                print(f"[KnowledgeBase] 读取文件失败 {filename}: {e}")

        if not all_chunks:
            print("[KnowledgeBase] 没有可索引的文档")
            return 0

        # 批量向量化
        print(f"[KnowledgeBase] 正在向量化 {len(all_chunks)} 条文档...")
        batch_size = 10
        all_embeddings = []
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            embs = self.embedder.embed_batch(batch)
            if not embs:
                print(f"[KnowledgeBase] 第 {i} 批向量化失败，跳过")
                continue
            all_embeddings.extend(embs)
            print(f"[KnowledgeBase] 已处理 {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

        if all_embeddings:
            self.vector_store.add(all_chunks[:len(all_embeddings)], all_embeddings, all_metadatas[:len(all_embeddings)])
            print(f"[KnowledgeBase] 入库完成，共 {self.vector_store.count()} 条记录")
        return self.vector_store.count()

    def _split_by_paragraph(self, text, max_len=300):
        """按段落切分，长段落再按句子切分"""
        # 按空行分段
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) <= max_len:
                chunks.append(para)
            else:
                # 按句子切分
                sentences = re.split(r'(?<=[。！？])', para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) <= max_len:
                        current += sent
                    else:
                        if current:
                            chunks.append(current.strip())
                        current = sent
                if current.strip():
                    chunks.append(current.strip())
        return chunks

    def search(self, query, top_k=3, min_score=0.3):
        """
        检索相关知识片段。
        返回 list[{"text", "metadata", "score"}]
        """
        if self.vector_store.count() == 0:
            return []
        query_emb = self.embedder.embed(query)
        if query_emb is None:
            return []
        return self.vector_store.query(query_emb, top_k=top_k, min_score=min_score)

    def build_context(self, query, top_k=3, min_score=0.3):
        """
        检索并格式化为可注入 System Prompt 的上下文字符串。
        """
        results = self.search(query, top_k=top_k, min_score=min_score)
        if not results:
            return ""
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"[参考资料{i}](相似度{r['score']:.2f}): {r['text']}")
        return "\n".join(context_parts)
