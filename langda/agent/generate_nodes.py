from typing import List
from .requirements_builder import RequirementsBuilder
from ..utils import (
    _find_all_blocks, 
    _replace_placeholder, 
    invoke_agent,
    _parse_simple_dictonary,
    _list_to_dict
)
from .state import BasicState, TaskStatus
from ..config import paths

import logging
logger = logging.getLogger(__name__)

class GenerateNodes:

    @staticmethod
    def generate_node(state:BasicState):
        """
        Regenerate specific code blocks based on evaluation.
        """
        logger.info(f"\n### ====================== ### current round: {state['iter_count']} ### ====================== ###")
        logger.info("\n### ====================== processing generate_node ====================== ###")
        state["status"] = TaskStatus.GNRT
        new_iter_count = state["iter_count"] + 1

        targeted_codes:List[dict] = []
        raw_prompt_template = _replace_placeholder(state["prompt_template"], state["fest_codes"], state["placeholder"])

        if new_iter_count == 1:  # first round
            prompt_type = "generate"
            prompt_template = _replace_placeholder(raw_prompt_template, state["langda_reqs"], state["placeholder"])
            input={
                "prompt_template": prompt_template,
                "test_analysis": [], # analysis
            }
        elif new_iter_count > 1:
            prompt_type = "regenerate"
            prompt_template = _replace_placeholder(raw_prompt_template, state["langda_reqs"], state["placeholder"])
            # constructed_code = _replace_placeholder(state["prompt_template"],state["temp_full_codes"])
            # prompt_template = RequirementsBuilder.build_regenerate_prompt(constructed_code, state["test_analysis"], raw_prompt_template_constructed)
            input={
                "prompt_template": prompt_template,   # code with <langda>
                # "constructed_code": constructed_code, # full code
                "test_analysis": state["test_analysis"], # analysis
            }
            
        else:
            raise ValueError(f"iter_count has a invalid value: {state['iter_count']}")

        generated_result, formatted_prompt, _ = invoke_agent(
            agent_type=state["agent_type"]["generate"], 
            model_name=state["model_name"], 
            # tools=tools, #### !!!!!!!!!!!! CHANGDED FOR TESTING
            tools=state["tools"], 
            prompt_type=prompt_type, 
            input=input, 
            config=state["config"])
 
        paths.save_as_file(formatted_prompt,"prompt",f"steps/{state['prefix']}/formatted_gnrtprompt_{state['iter_count']}",save_dir=state["save_dir"])
        paths.save_as_file(generated_result,"result",f"steps/{state['prefix']}/#gnrt_result_{state['iter_count']}",save_dir=state["save_dir"])

        generated_codes = _find_all_blocks('code',generated_result)     # [{"hash":"generated code"},{"hash":"generated code"},..]
        generated_dict = _list_to_dict(generated_codes)

        origin_fest_codes = state["fest_codes"]
        temp_full_codes = []
        iter = 0
        for i, fest_item in enumerate(origin_fest_codes):
            key, value = _parse_simple_dictonary(fest_item)
            if not value: 
                if key not in generated_dict:
                    logger.warning(f"generate_node: key '{key}' does not exist in generated_codes[{iter}]")
                    temp_full_codes.append({key:None})
                else:
                    targeted_codes.append({key:generated_dict[key]})
                    temp_full_codes.append({key:generated_dict[key]})
                iter += 1
            else:
                temp_full_codes.append(fest_item)

        paths.save_as_file(targeted_codes,"codes",f"steps/{state['prefix']}/#gnrt_{state['iter_count']}",save_dir=state["save_dir"])

        if generated_codes:
            return {
                "temp_full_codes":temp_full_codes,
                "generated_codes":targeted_codes,           # [{"hash1":"code block1"}, {"hash2":"code block2"}, ...]
                "iter_count":new_iter_count,
            }
        else:
            logger.warning(f"generate_node: Generated Code no found...")
            return {
                "generated_codes":[{"FAKEHASH":None}],
                "iter_count":new_iter_count,
            }
    @staticmethod
    def _decide_next_gnrt(state:BasicState):
        logger.info("processing _decide_next_gnrt... #current round:",state["iter_count"])
        generate_error = False
        for temp_full_codes in state["temp_full_codes"]:
            _, value = _parse_simple_dictonary(temp_full_codes)
            if value == None:
                generate_error = True

        if generate_error:
            state["iter_count"] -= 1
            logger.warning(f"_decide_next_gnrt: Number of generated code does not match, regenerating...")
            return "generate_node"
        else:
            return "evaluate_node"