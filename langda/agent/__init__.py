# agent/__init__.py
from .langda_agent import (
    AgentConfig,
    LangdaAgentBase,
    LangdaAgentSingleSimple, 
    LangdaAgentDoubleSimple,
    LangdaAgentSingleDC,
    LangdaAgentDoubleDC,
)
from .state import LangdaAgentProtocol
# from .generate_nodes import GenerateNodes
# from .evaluate_nodes import EvaluateNodes
# from .general_nodes import GeneralNodes
__all__ = [
    "AgentConfig",
    "LangdaAgentProtocol",
    "LangdaAgentBase",

    # GenerateNodes:simple_agent, GeneralNodes
    'LangdaAgentSingleSimple',
    # GenerateNodes:double_chain_agent, GeneralNodes
    "LangdaAgentSingleDC",

    # GenerateNodes:simple_agent, EvaluateNodes:simple_agent, GeneralNodes
    'LangdaAgentDoubleSimple',
    # GenerateNodes:double_chain_agent, EvaluateNodes:double_chain_agent, GeneralNodes
    "LangdaAgentDoubleDC",

]
