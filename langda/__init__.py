from .agent import (
    LangdaAgentSingleSimple,
    LangdaAgentDoubleSimple,
    LangdaAgentDoubleDC,
    LangdaAgentSingleDC,
    LangdaAgentProtocol,
    AgentConfig,
)
from typing import Literal, TypedDict, Unpack
from pathlib import Path
from .utils.test_tools import _problog_test
from .utils import invoke_agent
from .logger import setup_logging

import logging
logger = logging.getLogger(__name__)

__all__ = [
    'langda_solve',
    'invoke_agent',
    '_problog_test',

    # As type:
    'LangdaAgentSingleSimple',
    'LangdaAgentDoubleSimple', 
    'LangdaAgentSingleDC',
    'LangdaAgentDoubleDC',
    'LangdaAgentProtocol'
]

agent_map = {
        "single_simple": LangdaAgentSingleSimple,
        "double_simple": LangdaAgentDoubleSimple,
        "single_dc": LangdaAgentSingleDC,
        "double_dc": LangdaAgentDoubleDC,
    }

class SolveOverrides(TypedDict, total=False):
    agent_type: Literal["single_simple","double_simple","single_dc","double_dc"]
    model_name: str
    prefix: str
    save_dir: str | Path
    load: bool
    langda_ext: dict
    query_ext: str
    log_path: str
    config: dict
    api_key: str


def langda_solve(
    rule_string: str,
    **overrides: Unpack[SolveOverrides]
) -> str:
    """
    Create a Langda agent of the specified type.
    Args:
        agent_type: One of "single_simple", "double_simple", "single_dc", "double_dc". Default as "single_dc".
            - single: use generate-only-mode(single workflow); double: use generate-evaluate-refinement-loop(double workflow).
            - dc: double-chain agent(recommended); simple: simple agent.
        rules_string: The Problog rules to generate code for. Must be provided!!!
        model_name: Real llm model name of your api key. Default as "deepseek-chat"
        config: session configuration. Default as: 
        {"configurable": {"thread_id": str(uuid4()),"checkpoint_ns": "langda","checkpoint_id": None,}
            "metadata": {}}
        prefix: changable prefix, only for differentiate files and database. Default as "".
        save_dir: choose saving folder, default as current working folder. Default as None.
        load: When it's true, regardless of whether there is continuously updated code(FUP flag is false), read directly from database. Default as False.
        query_ext: for deepproblog file, you need to add facts and query yourself if you want langda test properly. Default as "".
        langda_ext: dynamic content api. Default as {}:
            1. you could use langda(LLM:"/* Mark */"). to accept dynamic prompt words as 'port'
            2. Then you could give all the dynamic prompts in form of {"Mark":"your real prompt",...}
            3. The agent will check all the ports and replace with corresponding prompts

    Returns:
        The executable files created from rules_string
    """
    try:
        safe_overrides = {k: v for k, v in overrides.items() if v is not None}
        cfgs = AgentConfig(
            rule_string=rule_string,
            **safe_overrides
        )
        setup_logging(f"{cfgs.prefix}_{cfgs.log_path}" if cfgs.prefix else f"{cfgs.log_path}")  # Ensure logging is set up
        logger.info(f"\n### ================================= Starting langda_solve with {cfgs.agent_type} ================================= ###\nAll heils to Langda!")

        # Validate agent_type
        if cfgs.agent_type not in agent_map:
            raise ValueError(f"Unknown agent type: {cfgs.agent_type}. Available types: {list(agent_map.keys())}")

        agent_class = agent_map[cfgs.agent_type]
        agent:LangdaAgentProtocol = agent_class(cfgs)
        result = agent.call_langda_workflow()
        return result.get("final_result", "")
    finally:
        logger.info(f"\n### ================================= Finished langda_solve with {cfgs.agent_type} ================================= ###\nAll heils to Langda!")
