from typing import Literal, Dict, List, Tuple, Optional
from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import time
import re

from langchain.tools import BaseTool
from langchain.schema import BaseOutputParser
from langchain.schema.runnable import Runnable
from langchain.chat_models.base import BaseChatModel
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.agents import (
    create_tool_calling_agent,
    AgentExecutor,
)
from dotenv import find_dotenv

import logging
from langchain_logger.callback import ChainOfThoughtCallbackHandler
logger = logging.getLogger(__name__)

def retry_agent(max_attempts):
    # Allow the agent retry 2 times
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "Authentication failed" in str(e) or "401" in str(e):
                        logger.error(f"Fatal authentication error: {e}")
                        raise
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
                        time.sleep(1)
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
                        raise
        return wrapper
    return decorator

class NoOpOutputParser(BaseOutputParser[str]):
    def parse(self, text: str) -> str:
        return text

    def get_format_instructions(self) -> str:
        return ""

class LLMConfig(BaseModel):
    model: str = "your_model_name"
    api_key: str = "your_api_key"
    api_typ: str = "Bearer"
    api_ver: str = "2024-01-01"
    temperature: float = 0.2

class AgentSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        # env_prefix="gnrt_",
        env_nested_delimiter="_",
        env_nested_max_split = 1,
        extra="ignore",
    )
    deepseek: LLMConfig  = {} # 1. subconfig：DeepSeek
    openai: LLMConfig  = {} # 2. subconfig：OpenAI
    groq: LLMConfig  = {} # 3. subconfig：GroqCloud

class LangdaAgentExecutor(BaseModel):
    """
    when creating, you should give the model_name and tools
    invoke_agent:       regular agent
    """
    cfgs: AgentSettings = Field(default_factory=AgentSettings)
    tools: List[BaseTool]
    model_name:str
    # File name configurations:
    prompt_format: Dict[str, str] = Field(default={
        "generate": "generate_prompt_{}.txt",
        "evaluate": "evaluate_prompt_{}.txt",
        "regenerate": "regenerate_prompt_{}.txt",
        "final_test": "zfinaltest_prompt_simple.txt",
    })

    def _detect_provider(self) -> str:
        """
        Detect the LLM provider based on model_name.
        """
        name = (self.model_name or "").lower()
        if "deepseek" in name:
            return "deepseek"
        if "gpt" in name or "openai" in name:
            return "openai"
        if "groq" in name:
            return "groq"
        raise TypeError(f"unsupported model: {self.model_name}")

    def get_callbacks(self) -> Optional[List]:
        """
        Get callbacks for LLM logging if enabled.
        """
        return [ChainOfThoughtCallbackHandler(logger=logger)]

    def get_prompt_path(self, prompt_type: str, agent_type:str) -> Path:
        """
        Get path for prompt files.
        Args:
            prompt_type: One of ["evaluate", "generate", "regenerate"]
        """
        if prompt_type not in self.prompt_format:
            raise FileExistsError(f"Unknown prompt: {prompt_type}.")
        return Path(__file__).parent.parent / "prompts" / self.prompt_format[prompt_type].format(agent_type)

    def load_prompt(self, prompt: Literal["evaluate", "generate", "regenerate", "final_test"], agent_type:str) -> str:
        """
        Load prompt content from file.
        Args:
            prompt: One of ["evaluate", "generate", "regenerate", "final_test"]
            agent_type: One of ["simple", "doublechain"]
        """
        path = self.get_prompt_path(prompt, agent_type)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            raise FileExistsError(f"Prompt file not found: {path}")
        
    def get_model(self, config: Optional[dict] = None) -> BaseChatModel:
        """
        Get the LLM model based on model_name.
        Supports DeepSeek, OpenAI, and GroqCloud.
        """
        cfg = (config or {})
        md:dict = cfg.get("metadata", {})
        xauth:dict = md.get("x_auth", {})
        source = xauth.get("source", "local")

        # Determine provider first (before we need final_model)
        provider = xauth.get("provider") or self._detect_provider()

        # Get base configurations based on provider
        if provider == "deepseek":
            base_model = self.cfgs.deepseek.model
            base_temp  = self.cfgs.deepseek.temperature
            env_key    = self.cfgs.deepseek.api_key
        elif provider == "openai":
            base_model = self.cfgs.openai.model
            base_temp  = self.cfgs.openai.temperature
            env_key    = self.cfgs.openai.api_key
        elif provider == "groq":
            base_model = self.cfgs.groq.model
            base_temp  = self.cfgs.groq.temperature
            env_key    = self.cfgs.groq.api_key
        else:
            raise TypeError(f"unsupported provider: {provider}")

        # Apply overrides from config
        override_api_key = xauth.get("api_key")
        override_model = xauth.get("model") 
        override_temp = xauth.get("temperature")

        final_model = override_model or base_model
        final_temp  = float(override_temp) if override_temp is not None else base_temp
        # Determine final API key (BYOK support)
        if override_api_key:
            final_key = override_api_key
        else:
            if source == "api":
                raise RuntimeError("API call requires api_key in config (BYOK).")
            final_key = env_key
            
        if not final_key:
            raise RuntimeError(f"No API key available for provider={provider} (source={source}).")

        # Instantiate the model
        if provider == "openai":
            return ChatOpenAI(
                model_name=final_model,
                temperature=final_temp,
                openai_api_key=final_key,
                callbacks=self.get_callbacks(),
            )
        if provider == "deepseek":
            return ChatDeepSeek(
                model=final_model,
                temperature=final_temp,
                api_key=final_key,
                callbacks=self.get_callbacks(),
            )
        if provider == "groq":
            return ChatGroq(
                model=final_model,
                temperature=final_temp,
                api_key=final_key,
                callbacks=self.get_callbacks(),
            )
        
        raise TypeError(f"unsupported provider: {provider}")

    # ========================= SIMPLE AGRNT ========================= #
    @retry_agent(max_attempts=3)
    def invoke_simple_agent(self, prompt_type:str, input:Dict[str,str], config:Dict[str,str], ext_prompt=False) -> str:
        """
        invoke a regular agent
        args:
            prompt_type: One of ["evaluate", "generate", "regenerate","final_test"], if ext_prompt = True, you should fill your own prompt here
            input: dictonary to fill all the placeholders in prompt
            config: configs of agent for example: {"configurable": {"thread_id": "2"}}
            ext_prompt: when using other prompt --> True, in this case, prompt_type = prompt_string
        """
        logger.info("\n### ====================== processing simple_agent ====================== ###")
        if not ext_prompt:
            raw_prompt_template = self.load_prompt(prompt_type, "simple")
        else:
            raw_prompt_template = prompt_type
        chatprompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert programmer proficient in Problog and DeepProbLog. You could complete the task with your knowledge."),
            ("human", raw_prompt_template)
        ])
        if not(prompt_type == "final_test"):
            simple_input = {"input":input["prompt_template"]}
        else:
            simple_input = input

        formatted_prompt = chatprompt_template.format_prompt(**simple_input).to_string()

        new_llm = self.get_model(config)
        chain:Runnable = chatprompt_template | new_llm | StrOutputParser()
        result = chain.invoke(input=simple_input, config=config)
        logger.info("### ====================== End of simple_agent ====================== ###")
        return result, formatted_prompt, ""
    

    # ========================= DOUBLECHAIN AGRNT ========================= #
    def split_doublechain_prompt(self,prompt_template:str):
        lines = prompt_template.split("*** split ***")
        return lines[0], lines[1]
    
    @retry_agent(max_attempts=3)
    def invoke_doublechain_agent(self, prompt_type: str, input: Dict[str, str], config: Dict[str, str], ext_prompt=False) -> Tuple[str, str]:
        """
        Invoke a double-chain agent that separates code generation and formatting
        
        args:
            prompt_type: One of ["evaluate", "generate", "regenerate"], if ext_prompt = True, you should fill your own prompt here
            input: dictionary to fill all the placeholders in prompt
            config: configs of agent for example: {"configurable": {"thread_id": "2"}}
            ext_prompt: when using other prompt --> True, in this case, prompt_type = prompt_string

        returns:
            Tuple of (resulting output, formatted prompt, result from first chain)
        """
        logger.info("\n### ====================== processing doublechain_agent ====================== ###")
        # Get the appropriate prompt template
        if not ext_prompt:
            raw_prompt_template = self.load_prompt(prompt_type, "doublechain")
        else:
            raw_prompt_template = prompt_type

        new_llm = self.get_model(config)


        # *** First chain: Generate the Problog code with tools *** 
        # TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK
        first_chain_prompt_template, second_chain_prompt_template = self.split_doublechain_prompt(raw_prompt_template)
        if prompt_type == "generate":
            system_prompt = ("system", "You are an expert programmer proficient in Problog and DeepProbLog. You could use the available tools to complete the task.")
        elif prompt_type == "evaluate":
            system_prompt = ("system", "You are an expert code evaluator specialized in ProbLog and DeepProbLog. You could use the available tools to complete the task.")
        elif prompt_type == "regenerate":
            system_prompt = ("system", "You are an expert programmer proficient in Problog and DeepProbLog. You could use the available tools to complete the task. You should always use 'get_report_tool' first to gain more information.")

        # *** Test double chain without tools: *** #
        # first_chain_prompt_template, second_chain_prompt_template = self.split_doublechain_prompt(raw_prompt_template)
        # if prompt_type == "generate":
        #     system_prompt = ("system", "You are an expert programmer proficient in Problog and DeepProbLog. You should complete the task.")
        # elif prompt_type == "evaluate":
        #     system_prompt = ("system", "You are an expert code evaluator specialized in ProbLog and DeepProbLog. You should complete the task.")
        # elif prompt_type == "regenerate":
        #     system_prompt = ("system", "You are an expert programmer proficient in Problog and DeepProbLog. You should always use 'get_report_tool' first to gain more information.")
        # TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK

        first_input = {
            "input": input["prompt_template"],
            "agent_scratchpad": ""
        }

        prompt_msgs = [
            system_prompt,
            ("human", first_chain_prompt_template),
            ("assistant", "{agent_scratchpad}")  # where tool outputs and thoughts will appear
        ]
        first_chain_prompt = ChatPromptTemplate.from_messages(prompt_msgs)
        first_formatted_prompt = first_chain_prompt.format_prompt(**first_input).to_string()
        # Create the model for generation

        # TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK
        # *** CASE1: Test double chain without tools: *** # 
        logger.info("Executing first chain: Code generation with tools...")
        if prompt_type == "evaluate":
            format_chain_first = first_chain_prompt | new_llm | StrOutputParser()
            first_result = format_chain_first.invoke(input=first_input, config=config)
        elif prompt_type == "generate" or prompt_type == "regenerate":
            agent = create_tool_calling_agent(new_llm, self.tools, first_chain_prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            # Execute the first chain
            first_result_raw = agent_executor.invoke(input=first_input, config=config)
            first_result = first_result_raw.get("output", "")
        # *** CASE2: Test double chain with tools: *** #
        # agent = create_tool_calling_agent(new_llm, self.tools, first_chain_prompt)
        # agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        # TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK ====== TEST BLOCK

        # *** Second chain: Format the code output correctly ***
        extracted_result = ""
        if prompt_type == "evaluate":
            extracted_result = first_result
        elif prompt_type == "generate" or prompt_type == "regenerate":
            pattern = r"```(?:problog|[a-z]*)?\n(.*?)```"
            matches = re.findall(pattern, first_result, re.DOTALL)
            extracted_result = matches[-1]
        second_input = {
            "template_code": input["prompt_template"],
            "first_chain_output": extracted_result.strip()
        }
        second_chain_prompt = PromptTemplate.from_template(second_chain_prompt_template)
        second_formatted_prompt = second_chain_prompt.format_prompt(**second_input).to_string()
        # Execute the second chain
        logger.info("Executing second chain: Code formatting...")
        format_chain = second_chain_prompt | new_llm | StrOutputParser()
        second_result = format_chain.invoke(input=second_input, config=config)
        logger.info(f"*** Generated New Code ***\n{second_result}")
        logger.info("### ====================== End of doublechain_agent ====================== ###")
        return second_result, first_formatted_prompt + "\n\n**split**\n\n" + second_formatted_prompt, extracted_result


