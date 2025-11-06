# Langda

Language-Driven Agent for Probabilistic Logic Programming

Automatically generate ProbLog code from natural language using LLM agents.

## Installation

```bash
# From GitHub
pip install git+https://github.com/Symbolic-Intelligence-Org/langda-project.git

# Or clone and install locally
git clone https://github.com/Symbolic-Intelligence-Org/langda-project.git
cd langda-project
pip install -e .
```

To enable LangChain logging integration, you need to install
langchain-logger manually:

```bash
pip install --no-deps langchain-logger==0.1.0
```

!We use --no-deps here to avoid pulling in incompatible dependencies.

To enable retrieve function, you could also install faiss cpu or faiss gpu, this is optional.

## Update

```bash
pip install --upgrade git+https://github.com/Symbolic-Intelligence-Org/langda-project.git
```

If you feel you are unable to update, use:

```bash
pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/Symbolic-Intelligence-Org/langda-project.git
```

## Quick Start

```python
from langda import langda_solve

rules = """
langda(LLM:"Define factorial predicate").
query(factorial(5, X)).
"""

result = langda_solve(
    agent_type="double_dc",
    rule_string=rules,
    model_name="deepseek-chat"
)

print(result)
```

---

## `langda_solve` — Unified Entry for LangDa Execution

This is the **central API** for executing LangDa workflows.
It dynamically selects the appropriate agent architecture and runs the full generation–evaluation–refinement process.

### Function Signature

```python
langda_solve(
    rule_string: str,
    **overrides: Unpack[SolveOverrides]
) -> str
```

### Parameters

**rule_string** (`str`, *required*)  
: ProbLog or hybrid LangDa rules to process. Must be provided.

**agent_type** (`Literal["single_simple","double_simple","single_dc","double_dc"]`, default=`"single_dc"`)  
: Select the agent architecture:  
  – `single_*`: generate-only  
  – `double_*`: generate–evaluate–refine  
  – `_simple`: simple agent  
  – `_dc`: double-chain *(recommended)*

**model_name** (`str`, default=`"deepseek-chat"`)  
: The model name used by your API key.

**prefix** (`str`, default=`""`)  
: Optional prefix to differentiate output files or database entries.

**save_dir** (`str` | `Path`, default=current directory)  
: Folder for outputs and cached results.

**load** (`bool`, default=`False`)  
: If `True`, directly load from database, skipping generation when available.

**langda_ext** (`dict`, default=`{}`)  
: Dynamic content mapping for placeholders.  
  Example: `langda(LLM:"/* City */ weather")` → `{"City": "Berlin"}`

**query_ext** (`str`, default=`""`)  
: For DeepProbLog tasks, add extra facts or queries if needed.

**log_path** (`str`, default=`"langda.log"`)  
: Log file name; combined with prefix if set.

**config** (`dict`, optional)  
: Optional session configuration.

**api_key** (`str`, optional)  
: Optional override for model API key.


### Default Configuration Example

```python
config = {
    "configurable": {
        "thread_id": str(uuid4()),
        "checkpoint_ns": "langda",
        "checkpoint_id": None,
    },
    "metadata": {}
}
```

### Agent Map

| Key               | Class                     |
| ----------------- | ------------------------- |
| `"single_simple"` | `LangdaAgentSingleSimple` |
| `"double_simple"` | `LangdaAgentDoubleSimple` |
| `"single_dc"`     | `LangdaAgentSingleDC`     |
| `"double_dc"`     | `LangdaAgentDoubleDC`     |

### Return

`str` — The final executable code or result from the LangDa workflow.

### Example

```python
rules = """
% Simple example
langda(LLM:"Describe today's weather in Paris", LOT:"search").
weather(paris, sunny, 25).
"""

result = langda_solve(
    rule_string=rules,
    agent_type="double_dc",
    model_name="deepseek-chat",
    prefix="weather_demo",
    save_dir="./outputs",
    log_path="demo.log"
)
print(result)
```

### Notes

* `langda_solve` automatically sets up logging and prints start/finish markers for each run.
* The **double-chain agent** (`double_dc`) is the most capable and recommended mode.

---

## Configuration

Create `.env` file:

```env
# DeepSeek (recommended)
GNRT_DEEPSEEK_PROVIDER=deepseek
GNRT_DEEPSEEK_MODEL=deepseek-chat
GNRT_DEEPSEEK_API_KEY=your-api-key
GNRT_DEEPSEEK_API_TYP=Bearer
GNRT_DEEPSEEK_API_VER=2025-03-15

# Optional: for web search function
TAVILY_API_KEY=your-tavily-api-key
```

For OpenAI or Groq, replace `DEEPSEEK` with `OPENAI` or `GROQ`.

## Agent Types

* `single_simple` - Basic generation
* `double_simple` - Generation with evaluation
* `single_dc` - Dual-phase generation ⭐ (recommended)
* `double_dc` - Dual-phase with evaluation

## Langda Syntax

```prolog
% Basic
langda(LLM:"Your instructions").

% With tools
langda(LOT:"search_tool,retriever_tool", LLM:"Instructions", FUP:"true").

% Dynamic content
langda(LLM:"Rules for /* City */ weather").
```

## Examples

### Dynamic Content

```python
rules = """
langda(LLM:"Define rules for /* City */").
"""

result = langda_solve(
    rule_string=rules,
    agent_type="double_dc",
    model_name="deepseek-chat",
    langda_ext={"City": "Tokyo"}
)
print(result)
```

### EXT Usage (langda_ext / query_ext)

```python
from langda import langda_solve

# 1) Use langda_ext to inject dynamic placeholders into LLM prompts
rules_dynamic = r"""
% The placeholders /* City */ and /* Task */ will be replaced by langda_ext
langda(LLM:"Create /* Task */ rules for /* City */, include base facts and a query example.").
"""

result_dynamic = langda_solve(
    rule_string=rules_dynamic,
    agent_type="double_dc",
    model_name="deepseek-chat",
    prefix="dynamic_ext_demo",
    save_dir="./outputs",
    langda_ext={
        "City": "Berlin",
        "Task": "weather"
    },
    log_path="dynamic_ext.log"
)
print(result_dynamic)

# 2) For DeepProbLog, use query_ext to append extra facts/queries at the end
rules_dpl = r"""
% Generate a probabilistic model and leave space for external queries
langda(LLM:"Define a simple coin model with probabilities and an observation.").
"""

extra_queries = r"""
% --- query_ext appended content ---
evidence(coin, heads).
query(coin).
"""

result_dpl = langda_solve(
    rule_string=rules_dpl,
    agent_type="double_dc",
    model_name="deepseek-chat",
    prefix="deepproblog_ext_demo",
    save_dir="./outputs",
    query_ext=extra_queries,
    log_path="deepproblog_ext.log"
)
print(result_dpl)
```

## Knowledge Base (Optional)

For retriever tool, create `langda/utils/problog_docs.json`:

```json
[
  {
    "id": "example_1",
    "title": "Title",
    "content": "Content here...",
    "tags": ["tag1"],
    "keywords": ["keyword1", "keyword2"]
  }
]
```
