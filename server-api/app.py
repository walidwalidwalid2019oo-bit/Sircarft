"""Authenticated Sircarft request API.

This service records validated provisioning requests. It deliberately does not
start Minecraft processes or expose a host/container control interface.
"""
from __future__ import annotations

import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

TOKEN_PLACEHOLDERS = {
    "replace_with_a_random_32_plus_character_secret",
    "put_your_server_token_here",
}
OWNER_ID = "single-tenant"
security = HTTPBearer(auto_error=False)
app = FastAPI(title="Sircarft Server API", version="0.1.0")


class CreateServerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=24)
    edition: Literal["Java", "Bedrock"]
    mode: Literal["Survival", "Creative", "Adventure"]


def configured_token() -> str:
    return os.getenv("SIRCARFT_API_TOKEN", "").strip()


def token_is_configured() -> bool:
    token = configured_token()
    return len(token) >= 32 and token.casefold() not in TOKEN_PLACEHOLDERS


def require_owner(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    expected = configured_token()
    if not token_is_configured():
        raise HTTPException(status_code=503, detail="Server API authentication is not configured.")
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="A bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # HTTP bearer credentials may contain non-ASCII input. compare_digest(str, str)
    # rejects non-ASCII strings with TypeError; UTF-8 bytes keep the comparison safe
    # and ensure malformed credentials are rejected as 401 rather than 500.
    supplied = credentials.credentials.encode("utf-8")
    configured = expected.encode("utf-8")
    if not hmac.compare_digest(supplied, configured):
        raise HTTPException(
            status_code=401,
            detail="Invalid bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # The first deployment is intentionally single-tenant. Replace this identity
    # with a verified account subject before exposing the service to multiple users.
    return OWNER_ID


def database_path() -> Path:
    configured = os.getenv("SIRCARFT_DB_PATH", "data/sircarft.sqlite3").strip()
    path = Path(configured or "data/sircarft.sqlite3")
    return path if path.is_absolute() else ROOT / path


def max_servers() -> int:
    try:
        value = int(os.getenv("SIRCARFT_MAX_SERVERS", "2"))
    except ValueError:
        value = 2
    return min(max(value, 1), 20)


def connect_database() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=5, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            edition TEXT NOT NULL,
            mode TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_servers_owner ON servers(owner_id, created_at);
        CREATE TABLE IF NOT EXISTS provisioning_jobs (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            server_id TEXT NOT NULL REFERENCES servers(id),
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(owner_id, idempotency_key)
        );
        """
    )
    return db


def get_database():
    db = connect_database()
    try:
        yield db
    finally:
        db.close()


def server_record(row: sqlite3.Row) -> dict[str, str]:
    return {
        "id": row["id"],
        "name": row["name"],
        "edition": row["edition"],
        "mode": row["mode"],
        "plan": row["plan"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def job_record(row: sqlite3.Row) -> dict[str, str]:
    return {
        "id": row["id"],
        "server_id": row["server_id"],
        "kind": row["kind"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def validate_idempotency_key(value: str | None) -> str:
    key = (value or "").strip()
    if not 16 <= len(key) <= 128 or not all(ch.isalnum() or ch in "-_.:" for ch in key):
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key must be 16–128 letters, numbers, or - _ . : characters.",
        )
    return key


@app.get("/health")
def health():
    configured = token_is_configured()
    return {
        "service": "Sircarft Server API",
        "status": "degraded" if configured else "setup_required",
        "authentication_configured": configured,
        "provisioning": "queue_only",
        "note": "No Minecraft runtime worker is connected.",
    }


@app.get("/v1/servers")
def list_servers(
    owner_id: str = Depends(require_owner),
    db: sqlite3.Connection = Depends(get_database),
):
    rows = db.execute(
        "SELECT * FROM servers WHERE owner_id = ? ORDER BY created_at DESC",
        (owner_id,),
    ).fetchall()
    return {"servers": [server_record(row) for row in rows]}


@app.post("/v1/servers", status_code=202)
def create_server(
    request: CreateServerRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    owner_id: str = Depends(require_owner),
    db: sqlite3.Connection = Depends(get_database),
):
    name = request.name.strip()
    if not name or any(ord(character) < 32 for character in name):
        raise HTTPException(status_code=422, detail="World name must contain visible characters only.")
    key = validate_idempotency_key(idempotency_key)
    payload = {
        "name": name,
        "edition": request.edition,
        "mode": request.mode,
        "plan": "free",
    }
    payload_json = json.dumps(payload, sort_keys=True)

    db.execute("BEGIN IMMEDIATE")
    existing = db.execute(
        """SELECT j.id AS job_id, j.server_id, j.kind, j.status AS job_status,
                  j.created_at AS job_created_at, j.payload_json,
                  s.*
           FROM provisioning_jobs j
           JOIN servers s ON s.id = j.server_id
           WHERE j.owner_id = ? AND j.idempotency_key = ?""",
        (owner_id, key),
    ).fetchone()
    if existing:
        if existing["payload_json"] != payload_json:
            db.rollback()
            raise HTTPException(status_code=409, detail="This idempotency key was already used for a different request.")
        db.commit()
        server = server_record(existing)
        job = {
            "id": existing["job_id"],
            "server_id": existing["server_id"],
            "kind": existing["kind"],
            "status": existing["job_status"],
            "created_at": existing["job_created_at"],
        }
        return {"server": server, "job": job, "replayed": True}

    count = db.execute(
        "SELECT COUNT(*) FROM servers WHERE owner_id = ?",
        (owner_id,),
    ).fetchone()[0]
    if count >= max_servers():
        db.rollback()
        raise HTTPException(status_code=409, detail="The configured server-slot limit has been reached.")

    server_id = str(uuid4())
    job_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute(
        """INSERT INTO servers(id, owner_id, name, edition, mode, plan, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (server_id, owner_id, name, request.edition, request.mode, "free", "queued", created_at),
    )
    db.execute(
        """INSERT INTO provisioning_jobs(id, owner_id, server_id, kind, status,
           idempotency_key, payload_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_id, owner_id, server_id, "provision", "queued", key, payload_json, created_at),
    )
    db.commit()

    server = db.execute("SELECT * FROM servers WHERE id = ?", (server_id,)).fetchone()
    job = db.execute("SELECT * FROM provisioning_jobs WHERE id = ?", (job_id,)).fetchone()
    return {
        "server": server_record(server),
        "job": job_record(job),
        "replayed": False,
        "notice": "Request stored in the provisioning queue. No Minecraft process is running yet.",
    }


@app.get("/v1/servers/{server_id}")
def get_server(
    server_id: str,
    owner_id: str = Depends(require_owner),
    db: sqlite3.Connection = Depends(get_database),
):
    row = db.execute(
        "SELECT * FROM servers WHERE id = ? AND owner_id = ?",
        (server_id, owner_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Server record not found.")
    return {"server": server_record(row)}


@app.get("/v1/jobs/{job_id}")
def get_job(
    job_id: str,
    owner_id: str = Depends(require_owner),
    db: sqlite3.Connection = Depends(get_database),
):
    row = db.execute(
        "SELECT * FROM provisioning_jobs WHERE id = ? AND owner_id = ?",
        (job_id, owner_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Provisioning job not found.")
    return {"job": job_record(row)}
