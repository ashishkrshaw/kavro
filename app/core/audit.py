"""
audit.py - security event logging
logs important security stuff like logins, key changes etc
"""

import logging
import json
from datetime import datetime, timezone

# setup logger
audit_logger = logging.getLogger("security_audit")
audit_logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(handler)

# TODO: in prod, send logs to cloudwatch or splunk


async def log_security_event(event: str, identifier: str, status: str, 
                            ip: str = None, details: dict = None):
    """
    log security events
    event: login, register, key_publish etc
    identifier: user_id or username
    status: success or failure
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "identifier": identifier,
        "status": status,
        "ip_address": ip,
        "details": details or {}
    }
    audit_logger.info(json.dumps(entry))
