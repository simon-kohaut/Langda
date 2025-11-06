# utils/__init__.py
import inspect
from typing import Union, List, Literal
from langchain.tools import BaseTool, Tool
from .models import LangdaAgentExecutor
from .parser_v2 import integrated_code_parser, LangdaDict
from .format_tools import (
    _ordinal,
    _list_to_dict, 
    _expand_nested_list,
    _replace_placeholder, 
    _find_all_blocks, 
    _compute_short_md5, 
    _compute_random_md5, 
    _parse_simple_dictonary, 
    _langda_list_to_dict,
    _deep2normal,
)
from .agent_tools import TOOL_REGISTRY
from .test_tools import with_timeout, _problog_test
__all__ = [
    'LangdaDict',
    'invoke_agent',
    'get_tools',
    '_ordinal',
    '_list_to_dict',
    '_compute_short_md5',
    '_compute_random_md5',
    '_langda_list_to_dict',
    '_expand_nested_list',
    '_parse_simple_dictonary',
    'integrated_code_parser',
    '_find_all_blocks',
    '_replace_placeholder',
    'with_timeout',
    'problog_test_tool',
    '_deep2normal',
]

import logging
logger = logging.getLogger(__name__)

def problog_test_tool(model, file_basename,timeout=120):
    try:
        return with_timeout(_problog_test,file_basename,timeout, model)
    except Exception as e:
        logger.error(f"Error in problog_test_tool: {e}")
        return f"ERROR: {str(e)}"

def invoke_agent(agent_type:Literal["simple","doublechain"], model_name:str, tools:List[str], prompt_type:Literal["evaluate", "generate", "regenerate"], input:dict, config:dict) -> tuple[str,str]:
    """
    Returns the corresponding LangdaAgentExecutor instance or its react version based on the parameters passed in when calling.
    Args:
        model_name: name of llm model
        prompt_type: One of ["evaluate", "generate", "regenerate"]
        input: dictonary to fill all the placeholders in prompt
        config: configs of agent for example: {"configurable": {"thread_id": "2"}}
    """
    executor = LangdaAgentExecutor(model_name=model_name,tools=get_tools(tools, input["test_analysis"]))

    if agent_type == "simple":
        return executor.invoke_simple_agent(prompt_type,input,config)
    elif agent_type == "doublechain":
        return executor.invoke_doublechain_agent(prompt_type,input,config)

def get_tools(tool_list: List[str], test_analysis:List[str]) -> List[BaseTool]:
    """
    Get tool instances based on the list of tool names.
    args:
        tool_list: List of tool names to load, currently we have "search_tool", "retriever_tool", "problog_test_tool"
    returns:
        List of instantiated tool objects
    """
    tools:List[BaseTool] = []
    if test_analysis: # This is a independent tool, it's only job is to offer the syntax rules and REPORTS from previous rounds.
        get_report_tool = Tool(
            name="get_report_tool",
            func=lambda _: "\n\n".join(test_analysis),
            description="Get a historical analysis report to help you regenerate your code. This tool receives a single string 'learn from history' as input.",
        )
        tools.append(get_report_tool)
    if not tool_list:
        return tools
    for tool_name in tool_list:
        entry = TOOL_REGISTRY.get(tool_name)
        if entry is None:
            logger.error(f"Tool '{tool_name}' not found")
            continue
        if inspect.isclass(entry) and issubclass(entry,BaseTool): # if is class -> Instantiate
            tools.append(entry())
        elif isinstance(entry,BaseTool): # if already Instantiated
            tools.append(entry)
        else:
            logger.error(f"Tool '{tool_name}' is neither a BaseTool subclass nor an instance")
            raise ModuleNotFoundError(f"Tool '{tool_name}' not found in registry")
    return tools