import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings

class SimpleOfflineEmbeddingFunction(chromadb.EmbeddingFunction):
    def name(self) -> str:
        return "simple_offline_embedding"

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            vec = [0.0] * 64
            words = text.lower().split()
            for w in words:
                idx = abs(hash(w)) % 64
                vec[idx] += 1.0
            norm = (sum(v * v for v in vec) ** 0.5) or 1.0
            vec = [v / norm for v in vec]
            embeddings.append(vec)
        return embeddings

class ChromaService:
    def __init__(self):
        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        self.embedding_fn = SimpleOfflineEmbeddingFunction()
        
        self.policy_collection = self.client.get_or_create_collection(
            name="techmania_policies",
            embedding_function=self.embedding_fn,
            metadata={"description": "TechMania store policies and return rules"}
        )
        
        self.conversation_collection = self.client.get_or_create_collection(
            name="techmania_conversations",
            embedding_function=self.embedding_fn,
            metadata={"description": "Customer support conversation logs"}
        )

    def index_policy_documents(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
            
        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"section": c.get("section", "General"), "source": "company_policy.docx"} for c in chunks]
        
        self.policy_collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_policy(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        if self.policy_collection.count() == 0:
            return []
            
        results = self.policy_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        policy_hits = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}]*len(docs)
            dists = results["distances"][0] if "distances" in results else [0.0]*len(docs)
            
            for doc, meta, dist in zip(docs, metas, dists):
                policy_hits.append({
                    "text": doc,
                    "section": meta.get("section", "General Policy"),
                    "relevance_score": round(1.0 - min(dist, 1.0), 3) if dist else 1.0
                })
                
        return policy_hits

    def store_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        customer_email: str = "",
        order_id: str = "",
        intent: str = "GENERAL"
    ) -> str:
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        asia_tz = ZoneInfo("Asia/Karachi")
        timestamp = datetime.now(asia_tz).isoformat()
        
        metadata = {
            "session_id": session_id,
            "role": role,
            "timestamp": timestamp,
            "customer_email": customer_email or "",
            "order_id": order_id or "",
            "intent": intent or "GENERAL"
        }
        
        self.conversation_collection.add(
            ids=[msg_id],
            documents=[content],
            metadatas=[metadata]
        )
        return msg_id

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        if self.conversation_collection.count() == 0:
            return []
            
        results = self.conversation_collection.get(
            where={"session_id": session_id}
        )
        
        if not results or not results.get("ids"):
            return []
            
        history = []
        docs = results["documents"]
        metas = results["metadatas"]
        
        for doc, meta in zip(docs, metas):
            history.append({
                "role": meta.get("role", "user"),
                "content": doc,
                "timestamp": meta.get("timestamp", ""),
                "customer_email": meta.get("customer_email", ""),
                "order_id": meta.get("order_id", ""),
                "intent": meta.get("intent", "")
            })
            
        history.sort(key=lambda x: x["timestamp"])
        return history[-limit:]

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        if self.conversation_collection.count() == 0:
            return []
            
        results = self.conversation_collection.get()
        if not results or not results.get("metadatas"):
            return []
            
        sessions = {}
        for doc, meta in zip(results["documents"], results["metadatas"]):
            sid = meta.get("session_id")
            if not sid:
                continue
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "customer_email": meta.get("customer_email", ""),
                    "message_count": 0,
                    "last_timestamp": meta.get("timestamp", ""),
                    "last_message": doc
                }
            sessions[sid]["message_count"] += 1
            if meta.get("timestamp", "") > sessions[sid]["last_timestamp"]:
                sessions[sid]["last_timestamp"] = meta.get("timestamp", "")
                sessions[sid]["last_message"] = doc
                if meta.get("customer_email"):
                    sessions[sid]["customer_email"] = meta["customer_email"]
                    
        return sorted(list(sessions.values()), key=lambda x: x["last_timestamp"], reverse=True)

chroma_service = ChromaService()
