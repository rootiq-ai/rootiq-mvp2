import ollama
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.core.vector_store import get_vector_store
from app.models.alert import Alert

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL
        self.vector_store = get_vector_store()
    
    async def generate_rca(self, alerts: List[Alert], 
                          use_historical_context: bool = True) -> Dict[str, Any]:
        """Generate RCA analysis using Llama3 via Ollama"""
        try:
            # Prepare alert context
            alert_context = self._prepare_alert_context(alerts)
            
            # Get historical context if requested
            historical_context = []
            if use_historical_context:
                historical_context = await self._get_historical_context(alerts)
            
            # Generate RCA
            rca_analysis = await self._generate_analysis(alert_context, historical_context)
            
            # Extract structured data from analysis
            structured_rca = self._parse_rca_analysis(rca_analysis)
            
            logger.info(f"RCA generated for {len(alerts)} alerts")
            return structured_rca
            
        except Exception as e:
            logger.error(f"Failed to generate RCA: {e}")
            raise
    
    def _prepare_alert_context(self, alerts: List[Alert]) -> str:
        """Prepare alert information as context for LLM"""
        context_parts = []
        
        for i, alert in enumerate(alerts, 1):
            alert_info = f"""
Alert {i}:
- ID: {alert.alert_id}
- Source: {alert.source}
- Severity: {alert.severity}
- Type: {alert.alert_type}
- Title: {alert.title}
- Description: {alert.description or 'N/A'}
- Message: {alert.message}
- Timestamp: {alert.alert_timestamp}
"""
            
            # Add raw data if available
            if alert.raw_data:
                alert_info += f"- Raw Data: {json.dumps(alert.raw_data, indent=2)}\n"
            
            context_parts.append(alert_info)
        
        return "\n".join(context_parts)
    
    async def _get_historical_context(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Get historical context from vector store"""
        try:
            # Extract patterns from current alerts
            alert_patterns = []
            for alert in alerts:
                pattern = f"{alert.source} {alert.alert_type} {alert.severity} {alert.title}"
                alert_patterns.append(pattern)
            
            # Search for similar historical cases
            similar_cases = await self.vector_store.search_similar_rca(
                alert_patterns, limit=settings.MAX_HISTORICAL_CONTEXT
            )
            
            return similar_cases
            
        except Exception as e:
            logger.error(f"Failed to get historical context: {e}")
            return []
    
    async def _generate_analysis(self, alert_context: str, 
                               historical_context: List[Dict[str, Any]]) -> str:
        """Generate RCA analysis using Ollama"""
        try:
            # Prepare historical context text
            historical_text = ""
            if historical_context:
                historical_text = "\n\nHistorical Similar Cases:\n"
                for i, case in enumerate(historical_context, 1):
                    historical_text += f"Case {i} (Similarity: {case['similarity']:.2f}):\n"
                    historical_text += f"{case['document']}\n\n"
            
            # Create comprehensive prompt
            prompt = f"""You are an expert IT operations analyst specializing in root cause analysis. 
Analyze the following correlated alerts and provide a comprehensive root cause analysis.

CORRELATED ALERTS:
{alert_context}

{historical_text}

Please provide a detailed analysis in the following JSON format:
{{
    "root_cause": "Detailed explanation of the root cause",
    "solution": "Step-by-step solution to resolve the issue",
    "impact_analysis": "Analysis of the impact on systems and business",
    "confidence_score": 0.85,
    "affected_systems": ["system1", "system2"],
    "business_impact": "high/medium/low",
    "estimated_resolution_time": 60,
    "prevention_measures": "Recommendations to prevent future occurrences",
    "monitoring_recommendations": "Additional monitoring suggestions",
    "urgency_level": "critical/high/medium/low"
}}

Focus on:
1. Identifying the underlying cause, not just symptoms
2. Providing actionable solutions
3. Considering system dependencies and interactions
4. Assessing business impact accurately
5. Learning from historical similar cases if provided

Response must be valid JSON only, no additional text."""

            # Generate response
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert IT operations analyst. Provide responses in valid JSON format only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Failed to generate analysis with Ollama: {e}")
            raise
    
    def _parse_rca_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse and validate RCA analysis from LLM response"""
        try:
            # Clean the response text
            cleaned_text = analysis_text.strip()
            
            # Try to extract JSON from the response
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = cleaned_text[start_idx:end_idx]
                analysis = json.loads(json_text)
            else:
                # Fallback: try to parse the entire response as JSON
                analysis = json.loads(cleaned_text)
            
            # Validate required fields and set defaults
            validated_analysis = {
                "root_cause": analysis.get("root_cause", "Unable to determine root cause"),
                "solution": analysis.get("solution", "Further investigation required"),
                "impact_analysis": analysis.get("impact_analysis", "Impact assessment pending"),
                "confidence_score": min(max(analysis.get("confidence_score", 0.5), 0.0), 1.0),
                "affected_systems": analysis.get("affected_systems", []),
                "business_impact": analysis.get("business_impact", "medium"),
                "estimated_resolution_time": analysis.get("estimated_resolution_time", 60),
                "prevention_measures": analysis.get("prevention_measures", ""),
                "monitoring_recommendations": analysis.get("monitoring_recommendations", ""),
                "urgency_level": analysis.get("urgency_level", "medium"),
                "llm_raw_response": analysis_text,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return validated_analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            # Return a fallback analysis
            return {
                "root_cause": "Failed to parse LLM analysis",
                "solution": "Manual analysis required",
                "impact_analysis": "Unable to assess impact automatically",
                "confidence_score": 0.1,
                "affected_systems": [],
                "business_impact": "unknown",
                "estimated_resolution_time": 120,
                "prevention_measures": "Review alert correlation and analysis process",
                "monitoring_recommendations": "Implement better monitoring for similar issues",
                "urgency_level": "medium",
                "llm_raw_response": analysis_text,
                "generated_at": datetime.utcnow().isoformat(),
                "error": "JSON parsing failed"
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing RCA analysis: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            # Try to list available models
            models = await self.client.list()
            
            # Check if our model is available
            available_models = [model['name'] for model in models['models']]
            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                return False
            
            logger.info(f"Successfully connected to Ollama. Model {self.model} is available.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def generate_summary(self, rca_analysis: Dict[str, Any]) -> str:
        """Generate a concise summary of the RCA"""
        try:
            prompt = f"""Provide a concise executive summary (2-3 sentences) of this RCA analysis:

Root Cause: {rca_analysis.get('root_cause', '')}
Solution: {rca_analysis.get('solution', '')}
Impact: {rca_analysis.get('impact_analysis', '')}
Business Impact: {rca_analysis.get('business_impact', '')}

Make it suitable for management reporting."""

            response = await self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 256
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return "Summary generation failed"
    
    async def improve_analysis(self, original_analysis: Dict[str, Any], 
                             feedback: str) -> Dict[str, Any]:
        """Improve RCA analysis based on user feedback"""
        try:
            prompt = f"""Improve the following RCA analysis based on user feedback:

Original Analysis:
{json.dumps(original_analysis, indent=2)}

User Feedback:
{feedback}

Provide an improved analysis in the same JSON format, incorporating the feedback."""

            response = await self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 2048
                }
            )
            
            improved_analysis = self._parse_rca_analysis(response['message']['content'])
            improved_analysis["improved_from_feedback"] = True
            improved_analysis["original_analysis"] = original_analysis
            
            return improved_analysis
            
        except Exception as e:
            logger.error(f"Failed to improve analysis: {e}")
            return original_analysis
