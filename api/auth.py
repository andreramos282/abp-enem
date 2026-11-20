"""Senhas (scrypt, da biblioteca padrão) e tokens de acesso (JWT HS256)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

# Parâmetros do scrypt (recomendação OWASP para senhas: N=2^17 é o ideal; 2^14 mantém o login rápido
# no plano gratuito do Render e ainda é bem mais seguro que um hash comum).
_N, _R, _P = 2**14, 8, 1


def gerar_hash(senha: str) -> str:
    sal = secrets.token_bytes(16)
    chave = hashlib.scrypt(senha.encode(), salt=sal, n=_N, r=_R, p=_P)
    return f"scrypt${_N}${_R}${_P}${base64.b64encode(sal).decode()}${base64.b64encode(chave).decode()}"


def conferir_senha(senha: str, guardado: str) -> bool:
    try:
        _, n, r, p, sal, chave = guardado.split("$")
        calculada = hashlib.scrypt(senha.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculada, base64.b64decode(chave))


def criar_token(usuario_id: int, segredo: str, horas: int) -> str:
    agora = datetime.now(UTC)
    return jwt.encode({"sub": str(usuario_id), "iat": agora, "exp": agora + timedelta(hours=horas)}, segredo, "HS256")


def ler_token(token: str, segredo: str) -> int | None:
    """Id do usuário do token, ou None se o token for inválido ou estiver vencido."""
    try:
        return int(jwt.decode(token, segredo, algorithms=["HS256"])["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
