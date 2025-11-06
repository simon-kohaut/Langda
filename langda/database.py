import sqlite3
# import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .config import paths

import logging
logger = logging.getLogger(__name__)

class DBConfig(BaseSettings):
    """
    Database configurations, supports environment variable overrides.
    """
    db_path: Path = Field(
        default=Path(paths.base_dir) / "database",
        description="SQLite path to the dictionary storage database"
    )
    db_prefix: str = Field(
        default="langda",
        description="Database file prefix"
    )
    model_config = SettingsConfigDict(
        env_prefix="LANGDADB_",
        env_file=".env",
        extra="allow"  
    )
class DictEntry(BaseModel):
    """
    Dictionary entry model.
    """
    hash: str = Field(..., description="Primary key, hash value of the dictionary")
    content: str = Field(..., description="Dictionary content, Generated code")


class DictDB:
    """
    A manager for dictionary storage using SQLite and Pydantic for data validation.
    """
    def __init__(self, db_path="", db_prefix=""):
        if db_path:
            base_dir = Path(db_path)
            prefix = db_prefix if db_prefix else self.config.db_prefix
        else:
            self.config = DBConfig()
            base_dir = Path(self.config.db_path)
            prefix = db_prefix if db_prefix else self.config.db_prefix

        db_filename = f"{prefix}.db"
        database_path = base_dir / db_filename
        
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create database directory {base_dir}: {e}")
            raise RuntimeError(f"Failed to create database directory {base_dir}: {e}")

        self.conn = sqlite3.connect(str(database_path))
        self._create_table()
        logger.info(f"Connected to database at {database_path}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_table(self) -> None:
        """
        Create langda_dict table if it doesn't exist.
        """
        cursor = self.conn.cursor()
        try:    
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS langda_dict (
                    hash TEXT PRIMARY KEY,
                    content TEXT NOT NULL
                )
                """
            )
            self.conn.commit()
            logger.debug("Database table 'langda_dict' ensured")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise RuntimeError(f"Failed to create table: {e}")

    def add_or_update(self, hash_value: str, content: Dict[str, str]) -> str:
        """
        Add a new dictionary entry or update if already exists.
        
        args:
            hash_value: Hash value serving as the primary key
            content: Dictionary content to store
            
        return:
            str: The hash value
        """
        cursor = self.conn.cursor()
        
        # # Convert dictionary to JSON string for storage
        # content_json = json.dumps(content)
        
        # Validate with Pydantic model
        if not content:
            # raise ValueError(f"Database: the value of {hash_value} is {content}.")
            logger.warning(f"Database: Attempting to store empty content for hash {hash_value}")
        try:
            entry = DictEntry(hash=hash_value, content=content)
            # Insert or replace the entry
            cursor.execute(
                "INSERT OR REPLACE INTO langda_dict (hash, content) VALUES (?, ?)",
                (entry.hash, entry.content)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to add/update entry with hash {hash_value}: {e}")
            raise RuntimeError(f"Failed to add/update entry with hash {hash_value}: {e}")
        return hash_value

    def get_item(self, hash_value: str) -> Optional[Dict[str, str]]:
        """
        Retrieve a dictionary by its hash value.
        
        args:
            hash_value: The hash value of the dictionary to retrieve
            
        return:
            Optional[Dict[str, Any]]: The dictionary content or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM langda_dict WHERE hash = ?", (hash_value,))
        row = cursor.fetchone()
        if not row:
            return None
        # Convert JSON string back to dictionary
        return row[0]

    def get_all_items(self) -> Dict[str, Dict[str, str]]:
        """
        Get all dictionaries stored in the database.
        
        return:
            Dict[str, Dict[str, Any]]: Dictionary mapping hash values to their content
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT hash, content FROM langda_dict")
        rows = cursor.fetchall()
        
        result = {}
        for hash_value, content in rows:
            result[hash_value] = content
        
        return result

    def list_all_hashes(self) -> List[str]:
        """
        List all hash values in the database.
        
        return:
            List[str]: List of hash values
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT hash FROM langda_dict")
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def remove(self, hash_value: str) -> bool:
        """
        Remove a dictionary entry by hash value.
        
        args:
            hash_value: The hash value of the dictionary to remove
            
        returns:
            bool: True if deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM langda_dict WHERE hash = ?", (hash_value,))
        self.conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Removed hash: {hash_value}")
            return True
        else:
            logger.debug(f"Hash not found for removal: {hash_value}")
            return False

    def sync_with_dict(self, dict_data: Dict[str, Dict[str, str]]) -> Dict[str, int]:
        """
        Synchronize the database with the provided dictionary.
        - Add or update items that are in dict_data
        - Remove items that are in database but not in dict_data
        
        args:
            dict_data: Dictionary of {hash: content} to sync with

        returns:
            Dict[str, int]: Statistics of sync operation
        """
        stats = {
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "retained": 0
        }
        
        # Get existing hashes
        existing_hashes = set(self.list_all_hashes())
        new_hashes = set(dict_data.keys())
        
        # Hashes to add or update
        to_update = new_hashes
        
        # Hashes to delete
        to_delete = existing_hashes - new_hashes
        
        # Process updates
        for hash_value in to_update:
            content = dict_data[hash_value]
            
            if hash_value in existing_hashes:
                # Check if content is actually different before updating
                existing_content = self.get_item(hash_value)
                if existing_content != content:
                    self.add_or_update(hash_value, content)
                    stats["updated"] += 1
                else:
                    stats["retained"] += 1
            else:
                self.add_or_update(hash_value, content)
                stats["added"] += 1
        
        # Process deletions
        for hash_value in to_delete:
            self.remove(hash_value)
            stats["deleted"] += 1

        logger.info(
            f"Database sync completed: "
            f"added={stats['added']}, updated={stats['updated']}, "
            f"deleted={stats['deleted']}, retained={stats['retained']}"
        )

        return stats

    def cleanup(self, valid_hashes: List[str]) -> int:
        """
        Delete all entries whose hash values are not in the provided valid_hashes list.
        
        args:
            valid_hashes: List of hash values to keep
            
        returns:
            int: Number of entries removed
        """
        if not valid_hashes:
            # Remove all if no valid hashes provided
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM langda_dict")
            removed = cursor.rowcount
            self.conn.commit()
            return removed
            
        placeholders = ",".join("?" for _ in valid_hashes)
        query = f"DELETE FROM langda_dict WHERE hash NOT IN ({placeholders})"
        cursor = self.conn.cursor()
        cursor.execute(query, valid_hashes)
        removed = cursor.rowcount
        self.conn.commit()
        logger.info(f"Database cleanup: removed {removed} entries, kept {len(valid_hashes)} entries")
        return removed

    def close(self) -> None:
        """
        Close the database connection.
        """
        self.conn.close()
        logger.debug("Database connection closed")
