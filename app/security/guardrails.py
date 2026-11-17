import re
from typing import Iterable

from app.core.config import settings

# Padrões comuns de tentativa de prompt injection e jailbreak
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules)", re.IGNORECASE),
    re.compile(r"(show|reveal|display|output|print|give\s+me)\s+(your\s+)?(system\s+prompt|initial\s+instructions|internal\s+prompt)", re.IGNORECASE),
    re.compile(r"\b(system\s+prompt|prompt\s+de\s+sistema|instru[cç][oõ]es\s+iniciais|regras\s+internas)\b", re.IGNORECASE),
    re.compile(r"(qual\s+([eé]\s+)?(o\s+)?|mostre|revele|imprima|exiba)\s*(o\s+)?(seu\s+)?(prompt\s+de\s+sistema|instru[cç][oõ]es|regras\s+internas)", re.IGNORECASE),
    re.compile(r"(reveal|print|show|dump)\s+(the\s+)?(api[_\s-]?key|secret|token|credentials|gemini_api_key|os\.environ)", re.IGNORECASE),
    re.compile(r"(mostre|revele|imprima|qual\s+([eé]\s+)?(a\s+)?)\s*(sua\s+)?(chave\s+de\s+api|chave\s+secreta|api[_\s-]?key|token)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+(developer|dan|sudo|jailbreak)\s+mode", re.IGNORECASE),
    re.compile(r"voc[eê]\s+agora\s+est[aá]\s+no\s+modo\s+(dan|desenvolvedor|livre|irrestrito)", re.IGNORECASE),
    re.compile(r"\b(cat\s+\.env|\.env|etc/passwd|os\.environ|environ\.get)\b", re.IGNORECASE),
]

# Regex para detecção de chaves e segredos em saídas
_CREDENTIAL_PATTERNS = [
    # Chaves da Google Cloud / Gemini API (AIza...)
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    # Padrão JWT (três segmentos base64 separados por ponto)
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # Formato genérico de segredos sk-...
    re.compile(r"\b(sk-[A-Za-z0-9]{20,})\b"),
]

PROTECTED_REPLACEMENT = "[PROTECTED_CREDENTIAL]"
MAX_USER_INPUT_LENGTH = 12000


class PromptInjectionException(ValueError):
    """Exceção levantada quando uma tentativa maliciosa de injeção é identificada."""
    pass


def sanitize_input(text: str) -> str:
    """Higieniza o texto de entrada do usuário.
    
    Remove caracteres nulos e valida o tamanho máximo permitido.
    """
    if not text:
        return ""
    # Remove null bytes e caracteres de controle perigosos
    cleaned = text.replace("\x00", "").strip()
    if len(cleaned) > MAX_USER_INPUT_LENGTH:
        cleaned = cleaned[:MAX_USER_INPUT_LENGTH]
    return cleaned


def detect_prompt_injection(text: str) -> bool:
    """Verifica se o texto contém assinaturas típicas de prompt injection ou extração de credenciais."""
    if not text:
        return False
    
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_output(text: str, additional_secrets: Iterable[str] | None = None) -> str:
    """Escaneia a resposta e substitui quaisquer dados sensíveis ou chaves vazadas.
    
    Garante que a chave do Gemini e segredos do sistema nunca cheguem ao usuário.
    """
    if not text:
        return ""

    sanitized = text

    # Redige segredos conhecidos da configuração (se preenchidos)
    known_secrets = set()
    if settings.gemini_api_key and len(settings.gemini_api_key) > 5:
        known_secrets.add(settings.gemini_api_key)
    if settings.jwt_secret and len(settings.jwt_secret) > 5:
        known_secrets.add(settings.jwt_secret)
    if settings.db_password and len(settings.db_password) > 3:
        known_secrets.add(settings.db_password)
    if settings.meta_app_secret and len(settings.meta_app_secret) > 5:
        known_secrets.add(settings.meta_app_secret)
    if settings.token_encryption_key and len(settings.token_encryption_key) > 5:
        known_secrets.add(settings.token_encryption_key)

    if additional_secrets:
        for sec in additional_secrets:
            if sec and len(sec) > 3:
                known_secrets.add(sec)

    for secret in known_secrets:
        if secret in sanitized:
            sanitized = sanitized.replace(secret, PROTECTED_REPLACEMENT)

    # Redige padrões conhecidos de credenciais (AIza, JWT, sk-...)
    for pattern in _CREDENTIAL_PATTERNS:
        sanitized = pattern.sub(PROTECTED_REPLACEMENT, sanitized)

    return sanitized
