"""Free/Pro/Business feature gating."""

from typing import Any

TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "allowed_tools": [
            "get_account_info",
            "get_friend_count",
            "get_message_quota",
        ],
        "daily_call_limit": 100,
    },
    "pro": {
        "allowed_tools": [
            "get_account_info",
            "get_friend_count",
            "get_message_quota",
            "send_broadcast",
            "send_push_message",
            "send_multicast",
            "send_narrowcast",
            "get_message_stats",
            "get_user_profile",
            "list_rich_menus",
            "create_rich_menu",
            "set_default_rich_menu",
            "link_rich_menu_to_user",
        ],
        "daily_call_limit": 5000,
    },
    "business": {
        "allowed_tools": "__all__",
        "daily_call_limit": -1,  # unlimited
    },
}


def is_tool_allowed(tier: str, tool_name: str) -> bool:
    """Check if a tool is allowed for the given tier."""
    tier_config = TIERS.get(tier)
    if not tier_config:
        return False
    allowed = tier_config["allowed_tools"]
    if allowed == "__all__":
        return True
    return tool_name in allowed


def get_daily_limit(tier: str) -> int:
    """Get daily call limit for a tier. Returns -1 for unlimited."""
    tier_config = TIERS.get(tier)
    if not tier_config:
        return 0
    limit: int = tier_config["daily_call_limit"]
    return limit


def get_upgrade_message(tier: str, tool_name: str) -> str:
    """Get bilingual upgrade instruction message."""
    if tier == "free":
        return (
            f"เครื่องมือ '{tool_name}' ไม่สามารถใช้งานได้ในแผน Free\n"
            f"กรุณาอัปเกรดเป็น Pro (฿500/เดือน) เพื่อใช้งานเครื่องมือนี้\n\n"
            f"The tool '{tool_name}' is not available on the Free plan.\n"
            f"Please upgrade to Pro (฿500/mo) to access this tool."
        )
    if tier == "pro":
        return (
            f"เครื่องมือ '{tool_name}' ไม่สามารถใช้งานได้ในแผน Pro\n"
            f"กรุณาอัปเกรดเป็น Business (฿1,500/เดือน) เพื่อใช้งานเครื่องมือนี้\n\n"
            f"The tool '{tool_name}' is not available on the Pro plan.\n"
            f"Please upgrade to Business (฿1,500/mo) to access this tool."
        )
    return (
        f"เครื่องมือ '{tool_name}' ไม่สามารถใช้งานได้ในแผนปัจจุบัน\n"
        f"The tool '{tool_name}' is not available on your current plan."
    )


def get_limit_exceeded_message(tier: str, daily_limit: int) -> str:
    """Get bilingual message when daily call limit is exceeded."""
    if tier == "free":
        return (
            f"คุณใช้งานครบ {daily_limit} ครั้ง/วัน สำหรับแผน Free แล้ว\n"
            f"กรุณาอัปเกรดเป็น Pro (฿500/เดือน) เพื่อเพิ่มเป็น 5,000 ครั้ง/วัน\n\n"
            f"You've reached the {daily_limit} calls/day limit on the Free plan.\n"
            f"Upgrade to Pro (฿500/mo) for 5,000 calls/day."
        )
    if tier == "pro":
        return (
            f"คุณใช้งานครบ {daily_limit:,} ครั้ง/วัน สำหรับแผน Pro แล้ว\n"
            f"กรุณาอัปเกรดเป็น Business (฿1,500/เดือน) เพื่อใช้งานไม่จำกัด\n\n"
            f"You've reached the {daily_limit:,} calls/day limit on the Pro plan.\n"
            f"Upgrade to Business (฿1,500/mo) for unlimited calls."
        )
    return (
        "คุณใช้งานเกินจำนวนครั้งที่กำหนดแล้ว\n"
        "You've exceeded the daily call limit."
    )
