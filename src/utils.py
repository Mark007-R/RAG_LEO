import os
import pickle
import json
import shutil
import logging
from pathlib import Path
from typing import Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_dirs(dirs: Optional[List[str]] = None) -> None:
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
    if not os.path.exists(path):
        return 0
    return os.path.getsize(path)

def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_directory_size(directory: str) -> int:
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

    try:
        upload_path = Path('uploads')
        for file_path in upload_path.glob(f"{doc_id}__*"):
            os.remove(file_path)
            deleted['uploads'] += 1
            logger.info(f"Deleted upload: {file_path}")
        
        index_path = Path('indexes') / f"{doc_id}.index"
        if index_path.exists():
            os.remove(index_path)
            deleted['indexes'] += 1
            logger.info(f"Deleted index: {index_path}")
        
        metadata_path = Path('metadata') / f"{doc_id}_chunks.pkl"
        if metadata_path.exists():
            os.remove(metadata_path)
            deleted['metadata'] += 1
            logger.info(f"Deleted metadata: {metadata_path}")
        
        logger.info(f"Deleted all files for doc_id: {doc_id}")
        
    except Exception as e:
        logger.error(f"Error deleting files for doc_id {doc_id}: {e}")
    
    return deleted

def backup_file(source_path: str, backup_dir: str = 'backups') -> Optional[str]:
    if not os.path.exists(source_path):
        logger.warning(f"Source file not found: {source_path}")
        return None
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(source_path)
        backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
        
        shutil.copy2(source_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to create backup of {source_path}: {e}")
        return None

def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

def safe_filename(filename: str, max_length: int = 255) -> str:
    filename = os.path.basename(filename)
    
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename

def get_all_documents() -> dict:
    documents = {}
    
    try:
        if not os.path.exists('indexes'):
            return documents
        
        for filename in os.listdir('indexes'):
            if filename.endswith('.index'):
                doc_id = filename[:-6]  # Remove '.index'
                
                index_path = os.path.join('indexes', filename)
                chunks_path = os.path.join('metadata', f'{doc_id}_chunks.pkl')
                
                documents[doc_id] = {
                    'index_exists': os.path.exists(index_path),
                    'chunks_exist': os.path.exists(chunks_path),
                    'index_size': get_file_size(index_path),
                    'created': datetime.fromtimestamp(os.path.getctime(index_path)).isoformat()
                }
        
        logger.debug(f"Found {len(documents)} indexed documents")
        
    except Exception as e:
        logger.error(f"Error getting document list: {e}")
    
    return documents