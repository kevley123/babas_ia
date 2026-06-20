"""
Jarvis V1 - Servicio LLM (DeepSeek API).

Wrapper sobre el cliente OpenAI configurado para DeepSeek.
Proporciona métodos para chat normal y chat con respuesta JSON estructurada.
"""

import json
import logging
import time

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

# Configuración de reintentos
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # segundos


class LLMService:
    """Servicio para interactuar con DeepSeek API."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """
        Args:
            api_key: API key de DeepSeek.
            base_url: URL base del API (https://api.deepseek.com).
            model: Modelo a usar (deepseek-v4-flash).
        """
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        logger.info("LLMService inicializado: model=%s, base_url=%s", model, base_url)

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict | None = None,
    ) -> str:
        """
        Envía una conversación al LLM y retorna la respuesta.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(
                    "LLM request (attempt %d): %d mensajes, temp=%.1f",
                    attempt,
                    len(messages),
                    temperature,
                )

                kwargs = {
                    "model": self._model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = self._client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason

                logger.debug(
                    "LLM response: %d chars, finish_reason=%s, usage=%s",
                    len(content),
                    finish_reason,
                    response.usage,
                )

                return content

            except RateLimitError:
                logger.warning("Rate limit alcanzado (attempt %d/%d)", attempt, MAX_RETRIES)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    raise

            except APITimeoutError:
                logger.warning("Timeout del API (attempt %d/%d)", attempt, MAX_RETRIES)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

            except APIError as e:
                logger.error("Error del API: %s (attempt %d/%d)", e, attempt, MAX_RETRIES)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    raise

        return ""  # Nunca debería llegar aquí

    def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> dict:
        """
        Envía una conversación al LLM y espera una respuesta JSON.
        Incluye reintentos automáticos si el JSON llega truncado o corrupto.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            response_text = self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Intentar parsear JSON de la respuesta
            try:
                import re
                json_text = response_text.strip()
                
                # 1. Buscar bloque markdown ```json ... ```
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', json_text, re.DOTALL)
                if match:
                    json_text = match.group(1).strip()
                else:
                    # 2. Si no hay markdown, buscar desde el primer '{' hasta el último '}'
                    match = re.search(r'\{.*\}', json_text, re.DOTALL)
                    if match:
                        json_text = match.group(0).strip()

                return json.loads(json_text)

            except json.JSONDecodeError:
                if attempt < MAX_RETRIES:
                    logger.warning("Intento %d: El LLM devolvió un JSON inválido o truncado. Reintentando...", attempt)
                    continue
                
                logger.warning(
                    "No se pudo parsear JSON del LLM tras %d intentos. Respuesta final:\n%s",
                    MAX_RETRIES,
                    response_text,
                )
                return {"error": "invalid_json", "raw_response": response_text}
