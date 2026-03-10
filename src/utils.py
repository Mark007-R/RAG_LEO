import os
import pickle
import logging
from typing import Any, Optional, List

logger = logging.getLogger(__name__)

def ensure_dirs(dirs: Optional[List[str]] = None) -> None:
    """Ensure required directories exist."""
    default_dirs = ['uploads', 'indexes', 'metadata', 'logs', 'temp']
    directories = dirs or default_dirs
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

def save_pickle(obj: Any, path: str) -> None:
    """Save object to pickle file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        file_size = os.path.getsize(path)
        logger.debug(f"Saved pickle to {path} ({file_size} bytes)")
        
    except Exception as e:
        logger.error(f"Failed to save pickle to {path}: {e}")
        raise IOError(f"Pickle save failed: {str(e)}")

def load_pickle(path: str) -> Any:
    """Load object from pickle file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Pickle file not found: {path}")
    
    try:
        with open(path, 'rb') as f:
            obj = pickle.load(f)
        
        logger.debug(f"Loaded pickle from {path}")
        return obj
        
    except Exception as e:
        logger.error(f"Failed to load pickle from {path}: {e}")
        raise IOError(f"Pickle load failed: {str(e)}")

def get_file_size(path: str) -> int:
    """Get file size in bytes."""
    if not os.path.exists(path):
        return 0
    return os.path.getsize(path)

def format_file_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_directory_size(directory: str) -> int:
    """Calculate total size of a directory in bytes."""
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating directory size for {directory}: {e}")
    
    return total_size