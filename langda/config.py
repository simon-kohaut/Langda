from pydantic import BaseModel, Field
import os
import json
from typing import Dict, Optional, Union, Any
from pathlib import Path
from dotenv import load_dotenv
import logging

class ProjectPaths(BaseModel):
    """Configuration for project paths using Pydantic.
        load_my_env: load env parameters

        get_absproj_path: path from the project root
        get_abscase_path: path from the example path

        get_data_path: data path
        get_prompt_path: 
        load_prompt: 
        load_data: 
        save_as_file: 

        ensure_directories_exist: 
    """
    
    # Project directory:
    # base_dir: Path = os.path.dirname(__file__)
    base_dir: Path = os.getcwd()

    # Relative path configurations:
    rel_paths: Dict[str, str] = Field(default={
        "rules": "rules",
        "models": "models",
        "history": "history",
        "prompts": "prompts"
    })
    
    workflow_files: Dict[str, str] = Field(default={
        "result": "result.txt",
        "codes": "codes.txt",
        "final_code": "final_code.pl",
        "prompt": "prompt.txt",
        "mermaid": "mermaid.mmd",
        "promis": "promis.pkl",
        "image": "image.png",
    })
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True  # Enable Path objects

    def get_abscase_path(self, rel_path: Union[str, Path]) -> Path:
        """
        Get absolute path from the directory of current example.
        Args:
            rel_path: Relative path
        """
        return self.base_dir / Path(rel_path)
    

    def _get_path(self, category: str, file_name: Optional[str] = None) -> Path:
        """
        Get path for a specific category and optional file name of the example.
        Args:
            category: Specific folder from rel_paths
            file_name: Optional file name
        """
        if category not in self.rel_paths:
            raise ValueError(f"Unknown category: {category}. Available categories: {list(self.rel_paths.keys())}")
        
        path = self.get_abscase_path(self.rel_paths[category])
        
        # Create directory if it doesn't exist
        if not file_name:
            path.mkdir(parents=True, exist_ok=True)
            return path
            
        # Ensure parent directory exists before returning file path
        path.mkdir(parents=True, exist_ok=True)
        return path / file_name

    def save_as_file(self, content: Union[list, str, Any], filetype: str, prefix: str = "", mode: str = "w", save_dir=""):
        """
        Save the content as a file (with optional prefix).
        Args:
            content: Content to save (list, string, or other convertible object)
            filetype: Type of file to create, one of workflow_files keys or custom path, one of [generated_result,evaluated_result,generated_codes,evaluated_codes]
                - "result": "result.txt",  -> result from llm
                - "codes": "codes.txt", -> output code blocks of llm
                - "final_code": "final_code.pl", -> final deepproblog code
                - "prompt": "prompt.txt", -> prompt template related
                - "mermaid": "mermaid.mmd", -> mermaid file
                - "promis": "promis.pkl", -> pkl file
                - "image": "image.png", -> png file
            prefix: Optional prefix for the filename
            mode: default as write mode: "w"
        """
        # Convert content to string
        if isinstance(content, list):
            contentstr = json.dumps(content, indent=0, ensure_ascii=False)
        else:
            contentstr = str(content)

        if save_dir:
            # FIX: Convert save_dir to Path object if it's a string
            if isinstance(save_dir, str):
                save_dir = Path(save_dir)
            
            # Determine the save path
            if filetype in self.workflow_files:
                filename = f"{prefix}_{self.workflow_files[filetype]}" if prefix else self.workflow_files[filetype]
                path = save_dir / filename
            else:
                # Use custom path within save_dir
                path = save_dir / filetype
                logging.info(f"Using custom file path: {path}")
        else:
            # Determine the save path
            if filetype in self.workflow_files:
                # Use predefined workflow file path
                filename = f"{prefix}_{self.workflow_files[filetype]}" if prefix else self.workflow_files[filetype]
                path = self._get_path("history", filename)
            else:
                # Use custom path
                path = self.get_abscase_path(filetype)
                logging.info(f"Using custom file path: {path}")

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        try:
            with open(path, mode, encoding="utf-8") as f:
                f.write(contentstr)
            logging.info(f"File saved successfully: {path}")
            return path
        except Exception as e:
            logging.error(f"Failed to save file {path}: {str(e)}")
            raise

    def ensure_directories_exist(self) -> None:
        """Create all directories defined in rel_paths if they don't exist."""
        for category in self.rel_paths:
            path = self.get_abscase_path(self.rel_paths[category])
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Ensured directory exists: {path}")

# Create a singleton instance
paths = ProjectPaths() 