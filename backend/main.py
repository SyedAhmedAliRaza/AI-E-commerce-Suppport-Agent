import os
import shutil
import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from services.chroma_service import chroma_service
from services.policy_service import policy_service
from services.sheets_service import sheets_service
from services.email_service import email_service
from agent_engine import agent_engine

app = FastAPI(
    title="TechMania AI E-Commerce Support Backend",
    description="FastAPI backend powered by ChromaDB, Google Sheets, python-docx policy RAG, and automated refund emails.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    customer_email: Optional[str] = None
    order_id: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "company": settings.COMPANY_NAME,
        "chroma_db_status": "ready",
        "chroma_policy_chunks": chroma_service.policy_collection.count(),
        "chroma_chat_messages": chroma_service.conversation_collection.count(),
        "use_live_sheets": sheets_service.use_live_sheets,
        "has_smtp": settings.has_smtp,
        "has_gemini": settings.has_gemini
    }

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
        
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    result = agent_engine.process_message(
        user_message=req.message,
        session_id=session_id,
        customer_email=req.customer_email,
        order_id_hint=req.order_id
    )
    return result

@app.get("/chat/history/{session_id}")
def get_chat_history(session_id: str):
    history = chroma_service.get_conversation_history(session_id)
    return {"session_id": session_id, "messages": history}

@app.get("/chat/sessions")
def get_all_sessions():
    sessions = chroma_service.get_all_sessions()
    return {"sessions": sessions}

@app.get("/products")
def get_products():
    products = sheets_service.get_all_products()
    return {"products": products}

@app.get("/orders")
def get_orders():
    orders = sheets_service.get_all_orders()
    return {"orders": orders}

@app.get("/logs")
def get_logs():
    logs = sheets_service.get_all_logs()
    return {"logs": logs}

@app.post("/policy/reindex")
def reindex_policy():
    count = policy_service.load_and_index_policy()
    return {"status": "success", "indexed_chunks": count}

@app.post("/policy/upload")
async def upload_policy(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only Word (.docx) files are supported.")
        
    destination_path = settings.POLICY_DOCX_PATH
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    count = policy_service.load_and_index_policy()
    return {
        "status": "success",
        "filename": file.filename,
        "indexed_chunks": count,
        "message": f"Successfully uploaded and indexed '{file.filename}' into ChromaDB!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
