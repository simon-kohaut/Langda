from typing import List
from .requirements_builder import RequirementsBuilder
from ..utils import (
    _find_all_blocks, 
    _replace_placeholder, 
    invoke_agent,
    _parse_simple_dictonary,
    problog_test_tool,
    _deep2normal,
)
from .state import BasicState, TaskStatus
from ..config import paths

import logging
logger = logging.getLogger(__name__)

class EvaluateNodes:
    """
    The nodes that are used for testing results
    """

    @staticmethod
    def evaluate_node(state:BasicState):
        logger.info(f"\n### ====================== ### current round: {state['iter_count']} ### ====================== ###")
        logger.info("\n### ====================== processing evaluate_node ====================== ###")
        state["status"] = TaskStatus.TEST
        test_result:str = ""
        constructed_code = _replace_placeholder(state["prompt_template"],state["temp_full_codes"])
        raw_prompt_template = _replace_placeholder(state["prompt_template"], state["fest_codes"], state["placeholder"])
        # problog_test_tool:
        if state["has_query"]: # need to do a test first
            test_result = problog_test_tool(constructed_code,state["prefix"],timeout=120)
            paths.save_as_file(test_result, "result", f"steps/{state['prefix']}/#test_results", mode="a",save_dir=state["save_dir"])
        elif state["query_ext"]:
            test_result = problog_test_tool(_deep2normal(constructed_code, state["query_ext"]),state["prefix"],timeout=120)
            paths.save_as_file(test_result, "result", f"steps/{state['prefix']}/#test_results", mode="a",save_dir=state["save_dir"])
        else:
            logger.warning("Warning, evaluate without test result. Maybe you should set query_ext first.")
        # TEST:
        test_result_info, report_info = RequirementsBuilder.build_all_report_info(state["generated_codes"],state["langda_dicts"], test_result)
        test_prompt_template = _replace_placeholder(raw_prompt_template, report_info) + "\n" + test_result_info

        input={
            "prompt_template": test_prompt_template,
            "test_analysis":[], #### Changed for test!!!
        }
        evaluated_result, formatted_prompt, evaluated_middle_result = invoke_agent(
            agent_type=state["agent_type"]["evaluate"], 
            model_name=state["model_name"], 
            tools=state["tools"], 
            prompt_type="evaluate", 
            input=input, 
            config=state["config"])

        paths.save_as_file(formatted_prompt,"prompt",f"steps/{state['prefix']}/formatted_evalprompt_{state['iter_count']}",save_dir=state["save_dir"])
        paths.save_as_file(evaluated_result, "result",f"steps/{state['prefix']}/#eval_result_{state['iter_count']}",save_dir=state["save_dir"])
        if evaluated_middle_result:
            paths.save_as_file(evaluated_middle_result, "result",f"steps/{state['prefix']}/#test_analysis_{state['iter_count']}",save_dir=state["save_dir"])

        origin_fest_codes = state["fest_codes"]
        evaluated_codes = _find_all_blocks("report",evaluated_result) # [{report:"",need_regenerate:"True"},...]

        new_fest_codes, langda_reqs = RequirementsBuilder.build_all_regenerate_info(
            state["generated_codes"],
            evaluated_codes, 
            state["langda_dicts"],
        )

        iter = 0
        for i, fest_item in enumerate(origin_fest_codes):
            key, value = _parse_simple_dictonary(fest_item)
            if not value:
                key_new, value_new = _parse_simple_dictonary(new_fest_codes[iter])
                if not key == key_new:
                    logger.warning(f"evaluate_node: Key '{key}' doesn't match in {new_fest_codes[iter]}, set as none")
                    # raise ValueError
                    origin_fest_codes[i][key] = None
                else:
                    origin_fest_codes[i][key] = value_new
                iter += 1

        test_analysis:List[str] = state["test_analysis"]
        test_analysis.append(evaluated_middle_result)

        if evaluated_codes:
            return {
                "fest_codes":origin_fest_codes,
                "langda_reqs":langda_reqs,
                "test_analysis":test_analysis,
            }
        else:
            logger.warning(f"evaluate_node: Generated report no found...")
            return {
                "fest_codes":origin_fest_codes,
                "langda_reqs":langda_reqs,
            }

    @staticmethod
    def _decide_next_eval(state:BasicState):
        logger.info("processing _decide_next_eval... #current round:",state["iter_count"])

        to_end = True
        for fest_code in state["fest_codes"]:
            _, value = _parse_simple_dictonary(fest_code)
            if value == None:
                to_end = False
        if to_end:
            return "summary_node"
        elif state["iter_count"] >= 3:
            logger.warning("Exceed the maximum iterate limitation.")
            return "summary_node"
        else:
            return "generate_node"
        