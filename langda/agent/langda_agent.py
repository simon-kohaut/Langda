import time
import json
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any, Literal, Dict

from .state import BasicState
from .generate_nodes import GenerateNodes
from .evaluate_nodes import EvaluateNodes
from .general_nodes import GeneralNodes
from pathlib import Path
from uuid import uuid4
from ..config import paths

DEFAULT_CONFIGURABLE = {
    "thread_id": lambda: str(uuid4()),
    "checkpoint_ns": "langda",
    "checkpoint_id": None,
}

def _draw_mermaid_png(graph: StateGraph, graph_str: str):
    """Generate mermaid file for the graph visualization"""
    graph_mermaid = graph.get_graph().draw_mermaid()
    paths.save_as_file(graph_mermaid, "mermaid", graph_str)

class AgentConfig(BaseModel):
    # Necessary user inputs
    agent_type: Literal["single_simple", "double_simple", "single_dc", "double_dc"] = "single_dc"
    rule_string: str
    model_name: str = "deepseek-chat"

    # Optional user inputs
    prefix: str = ""
    save_dir: Optional[Path] = None
    load: bool = False
    langda_ext: dict[str, Any] = Field(default_factory=dict)
    query_ext: str = ""
    log_path: str = "langda_run.log"
    api_key: Optional[str] = None

    # Session configuration
    """ Metadata and configurable settings, shape like:
    {
        "configurable": {
            "thread_id": str(uuid4()),
            "checkpoint_ns": "langda",
            "checkpoint_id": None,
        },
        "metadata": {
            "x_auth": {
                "api_key": str,
                "provider": str,
                "model_name": str,
                "temperature": float,
            }
        }
    }
    """
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_config_(self)-> "AgentConfig":
        cfg:dict = self.config.get("configurable", {})
        md:dict = self.config.get("metadata", {})
        xauth:dict = md.get("x_auth", {})
        for k, default in DEFAULT_CONFIGURABLE.items():
            if k not in cfg or cfg[k] in (None, ""):
                cfg[k] = default() if callable(default) else default

        self.config["configurable"] = cfg
        if not xauth.get("api_key") and self.api_key:
            xauth["api_key"] = self.api_key
        self.config["metadata"] = md

        return self

class LangdaAgentBase:
    """Base class for all Langda agents with common initialization"""
    
    def __init__(self, cfgs: AgentConfig):
        self.cfgs:AgentConfig = cfgs
        self.state = BasicState()
        self.state.update(cfgs.model_dump())
        # Initialize test analysis with syntax notes
        self.state["test_analysis"] = []
        with open(Path(__file__).parent.parent / "prompts"/ "Problog_Syntax.txt", "r") as f_s:
            self.state["test_analysis"].append(f_s.read())
        
        # Static parameters
        self.state["tools"] = ["retriever_tool", "search_tool"]
        self.state["placeholder"] = "{{LANGDA}}"
        
        self.checkpointer = MemorySaver()

    def _create_workflow(self, workflow_type: str) -> StateGraph:
        """Create workflow based on type"""
        self.state["srttime"] = time.time()
        self.state["iter_count"] = 0

        workflow = StateGraph(BasicState)
        workflow.set_entry_point("init_node")
        workflow.add_node("init_node", GeneralNodes.init_node)
        workflow.add_node("generate_node", GenerateNodes.generate_node)
        workflow.add_node("summary_node", GeneralNodes.summary_node)
        workflow.add_node("evaluate_node", EvaluateNodes.evaluate_node)
        # Add conditional edges from init_node
        workflow.add_conditional_edges("init_node", GeneralNodes._decide_next_init, 
            {
                "generate_node": "generate_node",
                "summary_node": "summary_node",
            })

        if workflow_type == "single":
            # Simple workflow: generate -> summary
            workflow.add_edge("generate_node", "summary_node")
        else:
            # Double workflow: generate -> test -> generate/summary
            workflow.add_conditional_edges("generate_node", GenerateNodes._decide_next_gnrt, 
                {
                    "generate_node": "generate_node",
                    "evaluate_node": "evaluate_node"
                })
            workflow.add_conditional_edges("evaluate_node", EvaluateNodes._decide_next_eval, 
                {
                    "generate_node": "generate_node",
                    "summary_node": "summary_node"
                })

        workflow.set_finish_point("summary_node")
        return workflow

    def call_langda_workflow(self) -> dict:
        """Execute the workflow and return results"""
        workflow_type = "double" if "evaluate" in self.state["agent_type"] else "single"
        langda_workflow = self._create_workflow(workflow_type)
        
        langda_agent = langda_workflow.compile(checkpointer=self.checkpointer)
        self.state = langda_agent.invoke(self.state, config=self.state["config"])
        
        graph_name = f"langda_agent_{workflow_type}"
        _draw_mermaid_png(langda_agent, graph_name)
        
        return self.state["final_result"]

# Specific agent implementations
class LangdaAgentSingleSimple(LangdaAgentBase):
    """Single workflow with simple agent"""
    def __init__(self, cfgs: AgentConfig):
        super().__init__(cfgs)
        self.state["agent_type"] = {"generate": "simple"}
class LangdaAgentSingleDC(LangdaAgentBase):
    """Single workflow with doublechain agent"""
    def __init__(self, cfgs: AgentConfig):
        super().__init__(cfgs)
        self.state["agent_type"] = {"generate": "doublechain"}

class LangdaAgentDoubleSimple(LangdaAgentBase):
    """Double workflow with simple agents"""
    def __init__(self, cfgs: AgentConfig):
        super().__init__(cfgs)
        self.state["agent_type"] = {
            "generate": "simple",
            "evaluate": "simple"
        }

class LangdaAgentDoubleDC(LangdaAgentBase):
    """Double workflow with doublechain agents"""
    def __init__(self, cfgs: AgentConfig):
        super().__init__(cfgs)
        self.state["agent_type"] = {
            "generate": "doublechain",
            "evaluate": "doublechain"
        }