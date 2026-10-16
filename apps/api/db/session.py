import os
import json
import uuid
import datetime
import logging
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("db.session")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/capstone")

def get_connection():
    """Return a raw connection to PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize PostgreSQL tables matching the Prisma schema."""
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS "Conversation" (
        "id" TEXT PRIMARY KEY,
        "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS "Message" (
        "id" TEXT PRIMARY KEY,
        "conversationId" TEXT NOT NULL REFERENCES "Conversation"("id") ON DELETE CASCADE,
        "role" TEXT NOT NULL,
        "content" TEXT NOT NULL,
        "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS "AuditLog" (
        "id" TEXT PRIMARY KEY,
        "messageId" TEXT NOT NULL REFERENCES "Message"("id") ON DELETE CASCADE,
        "stepType" TEXT NOT NULL,
        "stepDetail" JSONB NOT NULL,
        "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_tables_sql)
            conn.commit()
        logger.info("Database schema verified and initialized in PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL schema: {e}")
        raise e

def check_db_health() -> bool:
    """Check if the database connection is alive and healthy."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                res = cur.fetchone()
                return res is not None and res[0] == 1
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False

def create_conversation() -> str:
    """Create a new conversation record and return its UUID."""
    conv_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO "Conversation" ("id") VALUES (%s);', (conv_id,))
        conn.commit()
    return conv_id

def ensure_conversation(conversation_id: Optional[str]) -> str:
    """Ensure conversation exists; if not or None, create a new one."""
    if not conversation_id:
        return create_conversation()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT "id" FROM "Conversation" WHERE "id" = %s;', (conversation_id,))
            row = cur.fetchone()
            if not row:
                cur.execute('INSERT INTO "Conversation" ("id") VALUES (%s);', (conversation_id,))
        conn.commit()
    return conversation_id

def save_message(conversation_id: str, role: str, content: str) -> str:
    """Save a user or assistant message and return its messageId."""
    ensure_conversation(conversation_id)
    msg_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO "Message" ("id", "conversationId", "role", "content") VALUES (%s, %s, %s, %s);',
                (msg_id, conversation_id, role, content)
            )
        conn.commit()
    return msg_id

def save_audit_log(message_id: str, step_type: str, step_detail: Dict[str, Any]) -> str:
    """
    Save an audit log entry for a specific step.
    stepType must be one of: 'plan', 'retrieval', 'tool_call', 'clarify', 'final_answer'
    """
    audit_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO "AuditLog" ("id", "messageId", "stepType", "stepDetail") VALUES (%s, %s, %s, %s);',
                (audit_id, message_id, step_type, json.dumps(step_detail))
            )
        conn.commit()
    return audit_id

def get_conversation_history(conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent messages for conversation context."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'SELECT "id", "role", "content", "createdAt" FROM "Message" WHERE "conversationId" = %s ORDER BY "createdAt" ASC LIMIT %s;',
                (conversation_id, limit)
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def get_audit_logs_for_message(message_id: str) -> List[Dict[str, Any]]:
    """Retrieve all audit logs attached to a given message."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'SELECT "id", "stepType", "stepDetail", "createdAt" FROM "AuditLog" WHERE "messageId" = %s ORDER BY "createdAt" ASC;',
                (message_id,)
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
