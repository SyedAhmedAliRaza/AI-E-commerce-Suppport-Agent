import os
from typing import List, Dict, Any
import docx
from config import settings
from services.chroma_service import chroma_service

class PolicyService:
    def __init__(self, docx_path: str = settings.POLICY_DOCX_PATH):
        self.docx_path = docx_path

    def load_and_index_policy(self) -> int:
        if not os.path.exists(self.docx_path):
            return 0
            
        try:
            doc = docx.Document(self.docx_path)
        except Exception as e:
            print(f"Error reading policy document {self.docx_path}: {e}")
            return 0
            
        chunks = []
        current_section = "General Overview"
        current_text = []
        chunk_counter = 1
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
                
            if p.style.name.startswith("Heading") or (len(text) < 60 and text[0].isdigit() and "." in text[:3]):
                if current_text:
                    full_chunk_text = f"Section: {current_section}\n" + "\n".join(current_text)
                    chunks.append({
                        "id": f"policy_chunk_{chunk_counter}",
                        "section": current_section,
                        "text": full_chunk_text
                    })
                    chunk_counter += 1
                    current_text = []
                current_section = text
            else:
                current_text.append(text)
                
        if current_text:
            full_chunk_text = f"Section: {current_section}\n" + "\n".join(current_text)
            chunks.append({
                "id": f"policy_chunk_{chunk_counter}",
                "section": current_section,
                "text": full_chunk_text
            })
            
        if chunks:
            chroma_service.index_policy_documents(chunks)
            
        return len(chunks)

    def get_policy_context_for_query(self, query: str) -> str:
        results = chroma_service.search_policy(query, n_results=3)
        if not results:
            return "No specific policy sections found in ChromaDB vector store."
            
        context_str = "RELEVANT TECHMANIA POLICY SECTIONS (From ChromaDB):\n"
        for idx, res in enumerate(results, 1):
            context_str += f"\n--- Policy Match #{idx} ({res['section']}) ---\n{res['text']}\n"
            
        return context_str

policy_service = PolicyService()
