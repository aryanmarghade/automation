from typing import Dict, Any, List, Optional
import httpx
import json
from app.core.config import settings

class BaseAIProvider:
    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.2) -> Dict[str, Any]:
        raise NotImplementedError

    async def list_models(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = []
                    for m in data.get("models", []):
                        models.append({
                            "id": m.get("name"),
                            "name": m.get("name"),
                            "size_bytes": m.get("size", 0),
                            "modified_at": m.get("modified_at"),
                            "provider": "ollama"
                        })
                    return models
                return []
        except Exception:
            return []

    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        target_model = model or settings.DEFAULT_OLLAMA_MODEL
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        # Add tools if provided and supported
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    msg = data.get("message", {})
                    return {
                        "role": "assistant",
                        "content": msg.get("content", ""),
                        "tool_calls": msg.get("tool_calls", []),
                        "model": target_model,
                        "raw": data
                    }
                else:
                    return {
                        "error": f"Ollama HTTP {res.status_code}: {res.text}",
                        "content": ""
                    }
            except Exception as e:
                return {
                    "error": f"Failed to connect to Ollama ({self.base_url}): {str(e)}",
                    "content": ""
                }

class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = (base_url or settings.OPENAI_API_BASE).rstrip("/")

    async def list_models(self) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    return [{"id": m.get("id"), "name": m.get("id"), "provider": "openai_compatible"} for m in data.get("data", [])]
                return []
        except Exception:
            return []

    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, model: str = "gpt-4o-mini", temperature: float = 0.2) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choice = data.get("choices", [{}])[0].get("message", {})
                    return {
                        "role": "assistant",
                        "content": choice.get("content", ""),
                        "tool_calls": choice.get("tool_calls", []),
                        "model": model,
                        "raw": data
                    }
                else:
                    return {"error": f"API error {res.status_code}: {res.text}", "content": ""}
            except Exception as e:
                return {"error": f"OpenAI Provider Exception: {str(e)}", "content": ""}
