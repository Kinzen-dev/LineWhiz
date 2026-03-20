"""API key generation + validation."""

import secrets
from dataclasses import dataclass

import aiosqlite

API_KEY_PREFIX = "lw_"
API_KEY_LENGTH = 32


@dataclass
class ApiKeyInfo:
    """Validated API key information."""

    key: str
    user_id: str
    tier: str
    is_active: bool


async def generate_api_key(
    conn: aiosqlite.Connection,
    user_id: str,
    tier: str = "free",
) -> str:
    """Generate a new API key and store it in the database.

    สร้าง API key ใหม่และบันทึกลงฐานข้อมูล
    """
    key = f"{API_KEY_PREFIX}{secrets.token_hex(API_KEY_LENGTH)}"

    await conn.execute(
        "INSERT INTO api_keys (key, user_id, tier) VALUES (?, ?, ?)",
        (key, user_id, tier),
    )
    await conn.commit()
    return key


async def validate_api_key(
    conn: aiosqlite.Connection,
    key: str,
) -> ApiKeyInfo | None:
    """Validate an API key and return its info, or None if invalid.

    ตรวจสอบ API key และคืนค่าข้อมูล หรือ None ถ้าไม่ถูกต้อง
    """
    cursor = await conn.execute(
        "SELECT key, user_id, tier, is_active FROM api_keys WHERE key = ?",
        (key,),
    )
    row = await cursor.fetchone()

    if row is None:
        return None

    return ApiKeyInfo(
        key=row[0],
        user_id=row[1],
        tier=row[2],
        is_active=bool(row[3]),
    )


async def deactivate_api_key(
    conn: aiosqlite.Connection,
    key: str,
) -> bool:
    """Deactivate an API key. Returns True if key existed.

    ปิดการใช้งาน API key
    """
    cursor = await conn.execute(
        "UPDATE api_keys SET is_active = 0 WHERE key = ?",
        (key,),
    )
    await conn.commit()
    return cursor.rowcount > 0


async def update_tier(
    conn: aiosqlite.Connection,
    key: str,
    new_tier: str,
) -> bool:
    """Update the tier for an API key. Returns True if key existed.

    อัปเกรด/เปลี่ยนแผนสำหรับ API key
    """
    cursor = await conn.execute(
        "UPDATE api_keys SET tier = ? WHERE key = ?",
        (new_tier, key),
    )
    await conn.commit()
    return cursor.rowcount > 0
