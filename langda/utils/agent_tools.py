from pydantic import BaseModel, Field
from typing import Any, List, Optional, Type, ClassVar, Dict

from langchain.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun

# from config import paths
from .vector_store_v4 import LangdaVectorStore

import logging
logger = logging.getLogger(__name__)

# ======================================================================== #
#                                 BaseTools                                #
# ======================================================================== #

class SearchInput(BaseModel):
    query: str = Field(description="The search query to retrieve information.")

class CustomSearchTool(BaseTool):
    name:ClassVar[str] = "search_tool"
    description:ClassVar[str] = "Useful for searching additional information related to the current problem."
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, 
             query: str, 
             run_manager: Optional[CallbackManagerForToolRun] = None) -> Optional[list[dict[str, Any]]]:
        """Use the search tool."""
        logger.info(" Running search tool...")
        wrapped = TavilySearchResults(max_results=3)
        result = wrapped.invoke({"query": query})
        return result

    async def _arun(self, 
                    query: str, 
                    run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> Optional[list[dict[str, Any]]]:
        """Use the search tool asynchronously."""
        logger.info(" Running search tool asynchronously...")
        wrapped = TavilySearchResults(max_results=3)
        result = await wrapped.ainvoke({"query": query})
        return result


class RetrieverInput(BaseModel):
    query: str = Field(
        description=(
            "The query string to search for in the local ProbLog documentation knowledge base. "
            "Queries should be about ProbLog syntax, built-in predicates, libraries, or example models "
            "covered in the provided KB. Do not use this tool for questions outside the scope of the KB."
        )
    )

class RetrieverTool(BaseTool):
    name: ClassVar[str] = "retriever_tool"
    description: ClassVar[str] = (
        "Use this tool only to retrieve information that exists in the local ProbLog documentation KB. "
        "It can answer questions about ProbLog syntax, probabilistic facts, annotated disjunctions, "
        "built-in predicates, libraries (e.g., lists, apply, aggregate, etc.), and the example models "
        "provided. Do not attempt to answer or ask about topics not present in that KB."
    )
    args_schema: Type[BaseModel] = RetrieverInput

    def _run(
        self, 
        query: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[dict]:
        """
        Run the retriever tool to get relevant documents from the vector store.
        Only returns items that match the content of the KB.
        """
        logger.info("Running retriever tool...")
        try:
            vector_store = LangdaVectorStore()
            return vector_store.similarity_search_with_scores(query, k=1)
        except Exception as e:
            return {"error": f"Source not found: {e}"}



class FinishToolInput(BaseModel):
    output: str = Field(description="The full completed problog model string to output")

class FinishTool(BaseTool):
    name: ClassVar[str] = "finish_tool"
    description: ClassVar[str] = "Once you get the completed code, use this tool to return the final answer and end the chain"
    args_schema: Type[BaseModel] = FinishToolInput
    # return_direct: ClassVar[bool] = True  # End loop once called!!!

    def _run(self, 
             output:str,
             run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return output


# Dictionary mapping tool names to their respective classes
TOOL_REGISTRY:Dict[str, BaseTool] = {
    "search_tool": CustomSearchTool,
    "retriever_tool": RetrieverTool,
}
