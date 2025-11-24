import re
from typing import Dict, Any


def validate_product_name(name: str) -> bool:
    return bool(name and name.strip())


def sanitize_input(text: str) -> str:
    if not text:
        return ""
    return text.strip()


def format_log_entry(log: Any) -> str:
    """
    Safely formats a log entry.
    Supports both:
    - structured dict logs (recommended)
    - legacy string logs (fallback)
    """

    # -----------------------------
    # BACKWARD COMPATIBILITY FIX
    # If old logger strings appear (e.g. "🧠 THOUGHT: ...")
    # -----------------------------
    if isinstance(log, str):
        return log  # Just return it as-is to avoid crashes

    # -----------------------------
    # STRUCTURED LOG FORMAT
    # -----------------------------
    log_type = log.get("type", "info")
    content = log.get("content", "")
    details = log.get("details", "")

    if log_type == "thought":
        return f"💭 **Thought**: {content}"

    elif log_type == "action":
        if details:
            return f"⚡ **Action**: {content}\n   _{details}_"
        return f"⚡ **Action**: {content}"

    elif log_type == "observation":
        return f"👁️ **Observation**: {content}"

    else:
        return f"ℹ️ {content}"


def generate_filename(product_name: str, extension: str) -> str:
    clean_name = re.sub(r'[^\w\s-]', '', product_name)
    clean_name = re.sub(r'[-\s]+', '_', clean_name)
    return f"competitor_analysis_{clean_name}.{extension}"
