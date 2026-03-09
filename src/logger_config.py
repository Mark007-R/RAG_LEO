import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

from .config import settings

class ColoredFormatter(logging.Formatter):
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logging():
    
    logs_dir = settings.get_logs_path()
    logs_dir.mkdir(exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    log_file = logs_dir / f"rag_leo.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    error_log_file = logs_dir / f"errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    access_log_file = logs_dir / f"access.log"
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(file_formatter)
    
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    
    root_logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Log dir: {logs_dir}")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

class RequestLogger:
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('access')
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.log_request)
        app.after_request(self.log_response)
    
    def log_request(self):
        from flask import request
        self.logger.info(
            f"Request: {request.method} {request.path} "
            f"- IP: {request.remote_addr} "
            f"- Agent: {request.user_agent.string[:50]}"
        )
    
    def log_response(self, response):
        from flask import request
        self.logger.info(
            f"Response: {response.status_code} "
            f"- {request.method} {request.path} "
            f"- Size: {response.content_length or 0} bytes"
        )
        return response
