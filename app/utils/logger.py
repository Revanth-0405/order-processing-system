import logging
import json
import traceback
from datetime import datetime, timezone
from flask import has_request_context, g

class JSONFormatter(logging.Formatter):
    def __init__(self, service_name="flask_api"):
        super().__init__()
        self.service_name = service_name

    def format(self, record):
        # Get request_id if we are inside a Flask request
        req_id = "N/A"
        if has_request_context() and hasattr(g, 'request_id'):
            req_id = g.request_id

        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "request_id": req_id
        }
        
        # Include exception traceback if there is an error
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger(name, service_name="flask_api"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate logs if already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JSONFormatter(service_name=service_name)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger