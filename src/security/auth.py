from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "agrorisk-dev-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

USERS = {
    "carlos@agrorisk.local": {"id_usuario": 1, "nome": "Carlos Silva", "role": "Operador", "senha": "operador123", "id_equipamento_acesso": "EQ-MT-0023"},
    "fernanda@agrorisk.local": {"id_usuario": 2, "nome": "Fernanda Costa", "role": "GestorFrota", "senha": "gestor123", "id_equipamento_acesso": None},
    "ricardo@sompo.local": {"id_usuario": 3, "nome": "Ricardo Mendes", "role": "AnalistaSeguradora", "senha": "analista123", "id_equipamento_acesso": None},
}

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate(email: str, senha: str) -> dict | None:
    user = USERS.get(email)
    if not user or user["senha"] != senha:
        return None
    public = {k: v for k, v in user.items() if k != "senha"}
    public["email"] = email
    return public


def create_access_token(user: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user["email"],
        "id_usuario": user["id_usuario"],
        "role": user["role"],
        "id_equipamento_acesso": user.get("id_equipamento_acesso"),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_email(email: str) -> dict | None:
    user = USERS.get(email)
    if not user:
        return None
    return {k: v for k, v in user.items() if k != "senha"}


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
