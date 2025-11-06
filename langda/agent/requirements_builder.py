from typing import List, Dict, Tuple
from ..utils import (
    _parse_simple_dictonary,
    _langda_list_to_dict,
)
class RequirementsBuilder:
    """
    build the requirements for langda and lann based on their dictonaries.
    IF you want to expand the terms that langda could use, add them in the LANGDATERMS
    """
    NETWORK_HEADER = "The Information of Networks:"
    LANGDA_HEADER = "The Information for Generating Code of {} Placeholder"
    REPORT_HEADER = "The {} Code Block That You Should Analyse:"
    REGENERATE_HEADER = "The {} Code Block That You Should Regenerate:"

    # LANGDATERMS = [
    #     ("HASH", "Hash tag of code, please use it actually for generation"),
    #     ("LOT", "Tools that you could use"),
    #     ("NET", "Network Requirements"),
    #     ("LLM", "Requirements of Rules"),
    #     ] # FUP term is not used for prompting, so it doesn't show here
    
    LANGDATERMS = [
        ("HASH", "<HASH> Hash tag of code: {} </HASH>"),
        ("LOT", "<Tool>Tool that you should use for this task: {} </Tool>"),
        # ("NET", "Network Requirements"),
        ("LLM", "<Requirements>{} </Requirements>"),
        ] # FUP term is not used for prompting, so it doesn't show here

    @staticmethod
    def build_langda_info(idx:int, langda_dict: Dict[str, str]) -> str:
        item_lines = []

        item_lines.append("<Langda> Information:")
        for term, description in (RequirementsBuilder.LANGDATERMS):
            if langda_dict.get(term):
                item_lines.append(description.format(langda_dict[term]))
        item_lines[-1] += "</Langda>"
        return "\n".join(item_lines)

    @staticmethod
    def build_all_langda_info(langda_dicts: List[Dict[str, str]]) -> List[str]:
        langda_infos: List[str] = []
        for idx, langda in enumerate(langda_dicts, start=1):
            item_lines = RequirementsBuilder.build_langda_info(idx, langda)
            langda_infos.append({langda["HASH"]:item_lines})
        return langda_infos # each one corresponds to a langda term

    @staticmethod
    def build_all_report_info(code_list: List[dict], langda_dicts: List[Dict[str, str]], test_result:str="") -> Tuple[str,List[str]]:
        """
        Format:
        """
        langda_dict = _langda_list_to_dict(langda_dicts)
        test_result_info = ""
        report_info:List[str] = []
        if test_result:
            test_result_info = "<Result>\n Here are the testing result of code:\n {}\n</Result>".format(test_result)

        for idx, code_item in enumerate(code_list, start=1):
            key, value = _parse_simple_dictonary(code_item)
            # if not(key == langda_dict["HASH"]):
            #     raise ValueError(f"build_report_info: Key:{key} does not exist in langda_dicts")
            if key not in langda_dict:
                raise ValueError(f"build_report_info: Key:{key} does not exist in langda_dicts")

            report_info.append(RequirementsBuilder.build_report_info(idx, value, langda_dict[key]))

        return test_result_info, report_info

    @staticmethod
    def build_report_info(idx, code_item:str, langda_reqs_dict:dict) -> str:
        item_lines = []
        item_lines.append("<Langda>")
        item_lines.append("<Code_Block>{}</Code_Block>".format(code_item))
        for term, description in (RequirementsBuilder.LANGDATERMS):
            if langda_reqs_dict.get(term):
                item_lines.append(description.format(langda_reqs_dict[term]))
        item_lines[-1] += "</Langda>"
        return "\n".join(item_lines)


    @staticmethod
    def build_all_regenerate_info(code_list:List[dict], report_list:List[dict],langda_dicts:List[List[str]]) -> Tuple[List[dict], List[str]]:
        """
        args:
            code_list: list of codes
            report_list: list of reports in json form
        return:
            fest_code_list: fest_code_list only contains the 
            regenerate_info:
            regenerate_indices:
        """
        regenerate_info:List[str] = []
        fest_code_list:List[dict] = []
        need_regenerate_list:List[Tuple[str,str]] = []
        langda_dict = _langda_list_to_dict(langda_dicts)
        iter = 1

        for idx, (code_item, report_item) in enumerate(zip(code_list,report_list),start=1):

            key, value = _parse_simple_dictonary(code_item)
            report_content = report_item[key]
            need_regenerate = str(report_content["NeedRegenerate"]).strip('"').strip("'")

            if not report_content: # check if the code and report matches
                raise ValueError(f"build_regenerate_info: key:{key} the report: {report_content}")
            if not key in langda_dict: # check if the code has corresponding requirements
                raise ValueError(f"build_regenerate_info: key:{key} not in langda_reqs: {langda_dict}")

            if need_regenerate == 'True' or need_regenerate == 'true':
                # need_regenerate_list.append((code_item, report_item))
                fest_code_list.append({key:None})
                regenerate_info.append({key:RequirementsBuilder.build_langda_info(idx, langda_dict[key])})    
                # regenerate_info.append(RequirementsBuilder.build_regenerate_info(
                #     iter, value, report_item[key]["ErrorSummary"], report_item[key]["SuggestedFix"], langda_dict[key]))
                iter += 1
            elif need_regenerate == 'False' or need_regenerate == 'false':
                fest_code_list.append(code_item)
            else:
                raise ValueError(f"Need_regenerate has invalid value: {report_content['NeedRegenerate']}")
        
        return fest_code_list, regenerate_info

    # @staticmethod
    # def build_regenerate_prompt(constructed_code:str, test_analysis:str, raw_prompt_template_constructed:str) -> List[str]:
    #     item_lines = []
    #     item_lines.append("// Get information from generated code and its reports:")
    #     item_lines.append("<Generated_Code>")
    #     item_lines.append(constructed_code)
    #     item_lines.append(test_analysis)
    #     item_lines.append("</Generated_Code>")
    #     item_lines.append("\n")
    #     item_lines.append("// Regenerate the complete code based on the user's requirements in each <langda> block:")
    #     item_lines.append(raw_prompt_template_constructed)
    #     return "\n".join(item_lines)

    # @staticmethod
    # def build_regenerate_info(idx, code_value:str, error_summary:str, suggested_fix:str, langda_reqs_dict:dict) -> str:
    #     item_lines = []
    #     item_lines.append("<Langda>")
    #     # item_lines.append("<Code_Block>{}</Code_Block>".format(code_value))
    #     for term, description in (RequirementsBuilder.LANGDATERMS):
    #         if langda_reqs_dict.get(term):
    #             item_lines.append(description.format(langda_reqs_dict[term]))
    #     item_lines.append("<ErrorSummary>{}</ErrorSummary>".format(error_summary))
    #     item_lines.append("<SuggestedFix>{}</SuggestedFix>".format(suggested_fix))
    #     item_lines[-1] += "</Langda>"
    #     return "\n".join(item_lines)
    