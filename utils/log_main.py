import logging
import json
import datetime as st
from typing import override


logger = logging.getLogger("debate_logger")

class MyJSONFormatter(logging.Formatter):
    def __init__(self, fmt_keys: dict):
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}
        super().__init__()
    
    @override
    def format(self, record: logging.LogRecord):
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)
    
    @override
    def _prepare_log_dict(self, record: logging.LogRecord):
        always_include = {
            "message": record.getMessage(),
            "timestamp": st.datetime.fromtimestamp(record.created, tz=st.timezone.utc).isoformat(), # TODO: change to local time
        }
        
        message = {}
        for key, val in self.fmt_keys.items():
            if val in always_include:
                message[key] = always_include.pop(val)
            else:
                message[key] = getattr(record, val)
        
        # Add specific extra attributes we care about
        for attr in ["msg_type", "speaker", "receiver", "sender", "round", "topic"]:
            if hasattr(record, attr) and attr not in message:
                message[attr] = getattr(record, attr)
                
        message.update(always_include)
        return message
#default html, will be changed to a more useful format
class MyHTMLFormatter(logging.Formatter):
    def __init__(self, fmt_keys: dict):
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}
        super().__init__()
    
    def format(self, record: logging.LogRecord):
        # Simple HTML format, change to fit the original format
        message = record.getMessage()
        return f"<div>{message}</div>"

# Filter classes for directing logs to the right handlers
class MainDebateFilter(logging.Filter):
    """Filter that only allows log records related to the main debate"""
    def filter(self, record):
        return getattr(record, "msg_type", None) == "main debate"

class PersuadorHelperFilter(logging.Filter):
    """Filter that only allows log records related to persuador-helper communication"""
    def filter(self, record):
        return getattr(record, "msg_type", None) == "persuador_helper"


