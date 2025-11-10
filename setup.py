"""Sets up the Langda package for installation."""

#
# This file is part of Langda and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

import re

import setuptools

# Find Langda version and author strings
with open("promis/__init__.py", encoding="utf8") as fd:
    content = fd.read()
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE).group(1)
    author = re.search(r'^__author__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE).group(1)

# Import readme
with open("README.md", encoding="utf8") as readme:
    long_description = readme.read()

setup(
    # ===== Basic Information =====
    name="langda",    
    version=version,
    author=author,
    author_email="simon-kohaut@cs.tu-darmstadt.de",
    description="A Python package for semi-formal modeling in neuro-symbolic systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={
        "langda": [
            "py.typed",  # https://www.python.org/dev/peps/pep-0561/
            "prompts/*.txt",
            "utils/*.json",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
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
    extras_require={
        # Faiss (local vector store)
        "faiss": [
            "faiss-cpu>=1.7.4",
        ],
        "faiss-gpu": [
            "faiss-gpu>=1.7.4",
        ],
        # Development
        "dev": [
            "tqdm>=4.65.0",
        ],
        # Chatbot
        "telegram": [
            "python-telegram-bot>=22.0",
        ],
    },
)
