from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = "Language-Driven Agent for Probabilistic Logic Programming"

setup(
    # ===== Basic Information =====
    name="langda",
    version="6.5.0",
    author="GaiaWorld",
    author_email="myemail@example.com",
    description="LangDa: Language-Driven Agent for Probabilistic Logic Programming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="...",
    
    # ===== Package Discovery =====
    packages=find_packages(include=["langda", "langda.*"]),
    
    # ===== Include Non-Python Files =====
    include_package_data=True,
    package_data={
        "langda": [
            "prompts/*.txt",
            "utils/*.json",
        ],
    },
    
    # ===== Dependencies =====
    install_requires=[
        "langgraph>=0.4.3",
        "pydantic>=2.11.4",
        "pydantic-settings>=2.9.1",
        "problog",
        "langchain>=0.3.25",
        "langchain-community>=0.3.24",
        "langchain-core>=0.3.59",
        "langchain-deepseek>=0.1.3",
        "langchain-groq>=0.3.2",
        "langchain-openai>=0.3.16",
        "python-dotenv>=1.1.0"
    ],
    
    # ===== Optional Dependencies =====
    extras_require={
        # Faiss dependencies(local vector store)
        "faiss": [
            "faiss-cpu>=1.7.4",
        ],
        "faiss-gpu": [
            "faiss-gpu>=1.7.4",
        ],
        # Development dependencies
        "dev": [
            "tqdm>=4.65.0",
        ],
        # Example dependencies
        "telegram": [
            "python-telegram-bot>=22.0",
        ],
    },
    
    # ===== Python Version Requirement =====
    python_requires=">=3.8",
    
    # ===== PyPI Classifiers =====
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # ===== Keywords for PyPI Search =====
    keywords="problog llm agent ai probabilistic-programming langchain deepseek",
    
    # ===== Project URLs =====
    project_urls={
        "Bug Reports": "https://github.com/yourusername/langda/issues",
        "Source": "https://github.com/yourusername/langda",
        "Documentation": "https://github.com/yourusername/langda#readme",
    },
    
    # ===== License =====
    license="MIT",
)