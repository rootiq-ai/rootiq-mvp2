from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.database import get_db, test_connection
from app.core.vector_store import get_vector_store
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI Observability RCA"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including all components"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    overall_healthy = True
    
    # Check database connection
    try:
        db_healthy = test_connection()
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "details": "PostgreSQL connection" if db_healthy else "Connection failed"
        }
        if not db_healthy:
            overall_healthy = False
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "details": f"Database error: {str(e)}"
        }
        overall_healthy = False
    
    # Check LLM service (Ollama)
    try:
        llm_service = LLMService()
        llm_healthy = await llm_service.test_connection()
        health_status["components"]["llm"] = {
            "status": "healthy" if llm_healthy else "unhealthy",
            "details": f"Ollama connection with {llm_service.model}" if llm_healthy else "Ollama connection failed"
        }
        if not llm_healthy:
            overall_healthy = False
    except Exception as e:
        health_status["components"]["llm"] = {
            "status": "unhealthy",
            "details": f"LLM service error: {str(e)}"
        }
        overall_healthy = False
    
    # Check vector store
    try:
        vector_store = get_vector_store()
        vector_stats = await vector_store.get_collection_stats()
        health_status["components"]["vector_store"] = {
            "status": "healthy",
            "details": f"ChromaDB with {vector_stats.get('total_documents', 0)} documents"
        }
    except Exception as e:
        health_status["components"]["vector_store"] = {
            "status": "unhealthy",
            "details": f"Vector store error: {str(e)}"
        }
        overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "degraded"
    
    # Return appropriate HTTP status code
    if not overall_healthy:
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/health/database")
async def database_health_check():
    """Check database connectivity"""
    try:
        db_healthy = test_connection()
        if db_healthy:
            return {
                "status": "healthy",
                "component": "database",
                "details": "PostgreSQL connection successful"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "component": "database",
                    "details": "Database connection failed"
                }
            )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "component": "database",
                "details": f"Database error: {str(e)}"
            }
        )

@router.get("/health/llm")
async def llm_health_check():
    """Check LLM service connectivity"""
    try:
        llm_service = LLMService()
        llm_healthy = await llm_service.test_connection()
        
        if llm_healthy:
            return {
                "status": "healthy",
                "component": "llm",
                "details": f"Ollama connection successful with model: {llm_service.model}"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "component": "llm",
                    "details": "Ollama connection failed or model not available"
                }
            )
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "component": "llm",
                "details": f"LLM service error: {str(e)}"
            }
        )

@router.get("/health/vector-store")
async def vector_store_health_check():
    """Check vector store connectivity"""
    try:
        vector_store = get_vector_store()
        stats = await vector_store.get_collection_stats()
        
        return {
            "status": "healthy",
            "component": "vector_store",
            "details": f"ChromaDB operational with {stats.get('total_documents', 0)} documents",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "component": "vector_store",
                "details": f"Vector store error: {str(e)}"
            }
        )

@router.get("/version")
async def get_version():
    """Get application version information"""
    return {
        "application": "AI Observability RCA",
        "version": "1.0.0",
        "build_date": "2024-12-01",
        "python_version": "3.12.3",
        "api_version": "v1"
    }
