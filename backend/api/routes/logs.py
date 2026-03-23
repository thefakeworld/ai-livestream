"""
Logs API Routes
Receives and stores frontend logs
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from core.config import get_settings
from core.logger import get_logger

router = APIRouter()
logger = get_logger("logs")


class FrontendLogEntry(BaseModel):
    """Frontend log entry model"""
    timestamp: str
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stack: Optional[str] = None
    url: Optional[str] = None
    userAgent: Optional[str] = None
    sessionId: Optional[str] = None


@router.post("/frontend")
async def receive_frontend_log(log_entry: FrontendLogEntry, request: Request):
    """
    Receive and store frontend logs
    
    Args:
        log_entry: Log entry from frontend
        
    Returns:
        Success status
    """
    settings = get_settings()
    
    # Log to backend logger
    log_level = log_entry.level.lower()
    message = f"[Frontend] {log_entry.message}"
    
    if log_level == "error" or log_level == "fatal":
        logger.error(message, extra={
            "context": log_entry.context,
            "error": log_entry.error,
            "stack": log_entry.stack,
            "url": log_entry.url,
            "sessionId": log_entry.sessionId,
        })
    elif log_level == "warn":
        logger.warning(message)
    else:
        logger.info(message)
    
    # Write to frontend log file
    try:
        log_file = settings.LOGS_DIR / "frontend_errors.jsonl"
        
        log_data = log_entry.model_dump()
        log_data["received_at"] = datetime.now().isoformat()
        log_data["client_ip"] = request.client.host if request.client else None
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            
    except Exception as e:
        logger.error(f"Failed to write frontend log: {e}")
    
    return {"success": True, "message": "Log received"}


@router.get("/frontend")
async def get_frontend_logs(limit: int = 100):
    """
    Get recent frontend logs
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of recent log entries
    """
    settings = get_settings()
    log_file = settings.LOGS_DIR / "frontend_errors.jsonl"
    
    logs = []
    
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-limit:]:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to read frontend logs: {e}")
    
    return {
        "logs": logs,
        "total": len(logs),
    }


@router.delete("/frontend")
async def clear_frontend_logs():
    """
    Clear frontend logs
    
    Returns:
        Success status
    """
    settings = get_settings()
    log_file = settings.LOGS_DIR / "frontend_errors.jsonl"
    
    if log_file.exists():
        log_file.unlink()
        
    logger.info("Frontend logs cleared")
    
    return {"success": True, "message": "Logs cleared"}
