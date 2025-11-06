from typing import List, Dict, Protocol, Optional, runtime_checkable, Any
from typing_extensions import TypedDict
from enum import Enum
from ..utils import LangdaDict
class TaskStatus(str, Enum):
    INIT = "init" # Initial state
    GNRT = "code_generating" # Generate new code
    TEST = "code_testing" # Test the newly generated code
    CMPL = "completed" # Task completed

class Mode(str, Enum):
    PURE_PAR = "normal" # langda(X:"str"), langda(X,Y,...), langda():no parameter
    PURE_NET = "pure net" # langda(NET:"[mnist_net1(0,1), mnist_net2(2,3)]")
    PURE_LLM = "pure llm" # langda(LLM:"str")
    PARA_LLM = "llm with actions" # langda(X:"str",LLM:"str...") # the answer will stored in parameter and return as a parameter
    # langda(X:"return", T:"time", NET:"[mnist_net1(0,1), mnist_net2(2,3)], LLM:"str...") # 
    # langda(X:"str", NET:"[mnist_net1(0,1)]") # call llm with no description -> # PARAM_WITH_NET
    FULL_LLM = "full parts" 
    ELSE = "else case" # langda(NET:[net(0,1)],LLM:"")

class BasicState(TypedDict):
    # User inputs:
    model_name: str # actual model from api
    rule_string: str # User-provided context
    agent_type:dict # agent type

    config: dict # session configs
    prefix: str  # the name of current file
    save_dir: str # the path to database
    load:bool    # load from previous snapshots
    langda_ext: dict # User-provided context
    query_ext:str # Dynamic content

    # Prompting static parameters:
    tools: list # list of available tools
    has_query: bool # Problog or Deepproblog
    placeholder: str # use {{LANGDA}} as default
    prompt_template: str # the string that only leave "{LLM}" slot for prompting
    langda_dicts: List[LangdaDict] # the dict that contains detail informations about langda
    lann_dicts: List[Dict[str,str]] # the dict that contains detail informations about network
    langda_reqs: str # Prompt part reconstructed from langda_dicts
    lann_reqs: str # Prompt part reconstructed from lann_dicts
    
    # Dynamic parameters:
    srttime: float = 0.0 # time of workflow start
    endtime: float  = 0.0 # time of workflow end
    iter_count: int = 0 # Current number of iterations
    status: TaskStatus # Current task status
    fest_codes: List[dict] # The Code that doesn't need further generate
    temp_full_codes: list # New code generated
    generated_codes: list # New code generated (does not include fest code)
    final_result: dict # Final result
    test_analysis: list # Reports

@runtime_checkable
class LangdaAgentProtocol(Protocol):
    """The interface protocol of LangdaAgent"""
    
    def __init__(self, 
                rule_string: str, 
                model_name: str, 
                addition_input: Optional[Dict[str, Any]] = None) -> None:
        ...
    
    def call_langda_workflow(self) -> Dict[str, Any]:
        ...