import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
import json
import uuid
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = None
        self.collection = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collection for RCA data
            self.collection = self.client.get_or_create_collection(
                name="rca_collection",
                metadata={"description": "Historical RCA data for similarity matching"}
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def store_rca(self, rca_id: str, rca_data: Dict[str, Any], 
                       alert_patterns: List[str]) -> bool:
        """Store RCA data in vector database"""
        try:
            if not self.collection:
                await self.initialize()
            
            # Prepare document for storage
            document_text = self._prepare_rca_document(rca_data, alert_patterns)
            
            # Generate metadata
            metadata = {
                "rca_id": rca_id,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_count": len(alert_patterns),
                "status": rca_data.get("status", "unknown")
            }
            
            # Store in collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
            
            logger.info(f"RCA {rca_id} stored in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store RCA in vector database: {e}")
            return False
    
    async def search_similar_rca(self, alert_patterns: List[str], 
                                limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar RCA cases based on alert patterns"""
        try:
            if not self.collection:
                await self.initialize()
            
            # Prepare query text
            query_text = self._prepare_query_text(alert_patterns)
            
            # Search for similar cases
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_cases = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    similar_cases.append({
                        "document": doc,
                        "metadata": results["metadatas"][0][i],
                        "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                    })
            
            logger.info(f"Found {len(similar_cases)} similar RCA cases")
            return similar_cases
            
        except Exception as e:
            logger.error(f"Failed to search similar RCA cases: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector collection statistics"""
        try:
            if not self.collection:
                await self.initialize()
            
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"total_documents": 0, "collection_name": "unknown"}
    
    def _prepare_rca_document(self, rca_data: Dict[str, Any], 
                            alert_patterns: List[str]) -> str:
        """Prepare RCA data as a document for vector storage"""
        document_parts = [
            f"Root Cause: {rca_data.get('root_cause', '')}",
            f"Solution: {rca_data.get('solution', '')}",
            f"Impact: {rca_data.get('impact', '')}",
            f"Alert Patterns: {' | '.join(alert_patterns)}"
        ]
        return " ".join(document_parts)
    
    def _prepare_query_text(self, alert_patterns: List[str]) -> str:
        """Prepare alert patterns as query text"""
        return f"Alert Patterns: {' | '.join(alert_patterns)}"
    
    async def cleanup(self):
        """Cleanup vector store resources"""
        try:
            if self.client:
                # ChromaDB cleanup if needed
                pass
            logger.info("Vector store cleanup completed")
        except Exception as e:
            logger.error(f"Error during vector store cleanup: {e}")

# Global vector store instance
vector_store = VectorStore()

async def init_vector_store():
    """Initialize the global vector store instance"""
    await vector_store.initialize()

def get_vector_store() -> VectorStore:
    """Get the global vector store instance"""
    return vector_store
