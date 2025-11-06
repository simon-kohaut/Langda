import re
from enum import Enum
from typing import List, Tuple
from typing_extensions import TypedDict
from .format_tools import _compute_short_md5

# from problog.program import PrologString
# from problog.logic import Term, Var, Constant, Clause, AnnotatedDisjunction, And, Or, Not, AggTerm, list2term, term2list, is_list
class LangdaDict(TypedDict):
    HEAD: str
    HASH: str

    LOT: str
    NET: str
    LLM: str
    FUP: bool

class PredicateState(Enum):
    """Enum class defines predicate state"""
    NONE = "NONE" # Not in langda predicate
    BODY = "BODY" # In the langda predicate body
    END  = "END." # At the end of the langda predicate

class Parser(object):
    """Parsing Prolog code, especially parsers for langda and lann predicates
    Attributes:
        result_text (str): processed text result
        lann_dicts:List[dict]: a list
        langda_dicts:List[dict]: a list
    """

    # =============================== CODE FOR PARSING ORIGINAL CODE =============================== #
    def clean_result_fields(self, result_dict:dict, keys:list, defaults:list=None):
        """
        args:
            result_dict: the dictionary that needs to be cleaned
            keys: a list of key value that need to be contained
            defaults: if cannot find the key, construct the key with corresponding default value
        """
        if defaults is None:
            defaults = [None] * len(keys)
        
        result = {}
        for i, key in enumerate(keys):
            default = defaults[i] if i < len(defaults) else ""
            result[key] = result_dict.get(key) or default

        return result

    def _map_state(self,state:bool):
        return PredicateState.BODY.value if state else PredicateState.NONE.value

    def get_dense_code_with_comments(self,text) -> Tuple[List[Tuple[str, str, str]], bool]:
        """
        process the code line by line and store code and comment separately,
        return with [(code_block, comment_block, in_langda),...] form

        args:
            text: The original unprocessed text in string
        It calls the function: self._find_original_line(), and self._map_state()
        returns:
            a List, each element is a Tuple of ("pure code block", "pure comment block", "in_langda")

        in_langda indicates if the code block belongs to a langda predicate, 
        it has three states: "BODY":contains langda, "NONE":has no langda, "END.":at the end of a langda
        """
        # ----------------------- normalize the code form ----------------------- #
        text = re.sub(r' +', ' ', text) # remove extra spaces from code only
        lines = text.split('\n')
        dense_code_with_comments = []

        # State Parameters
        in_quotes = False
        in_multiline_comment = False
        is_escaped = False
        current_comment = ""
        code_segment = ""

        # ----------------------- langda tracking parameters ----------------------- #
        has_query = False
        in_langda = False
        main_bracket_stack = []

        idl = 0  # index of line
        while idl < len(lines):
            line = lines[idl]  # cleaned line

            code_line_st = 0    # the first code char in line
            code_line_nd = None # the last code char in line
            idc = 0             # index of character

            # Flag to track if this line contains langda predicate

            while idc < len(line):

                # ------------------------------PART1------------------------------ #
                # ------------------------- check langda -------------------------- #
                if not in_quotes and not in_multiline_comment:
                    if line[idc] == '(':
                        main_bracket_stack.append("depth")
                    elif line[idc] == ')' and main_bracket_stack:
                        if len(main_bracket_stack) > 0:
                            main_bracket_stack.pop()

                    # <<<====================== EXTENDABLE AREA =========================>>> #
                    # ========================= EXTENDABLE: LANGDA ========================= #
                    # Check for langda predicate start
                    if (idc <= len(line) - 7 and line[idc:idc+7] == 'langda(') and not in_langda:
                        in_langda = True
                        main_bracket_stack.append("depth")

                        # If there's code before langda, we cut it as non-langda code in a single block
                        if code_line_st < idc:
                            code_segment = line[code_line_st:idc]
                            dense_code_with_comments.append((code_segment, "", PredicateState.NONE.value))

                        code_line_st = idc
                        idc += 7
                        continue
                    # ========================= EXTENDABLE: LANN =========================== #
                    # Check for lann predicate start
                    elif (idc <= len(line) - 5 and line[idc:idc+5] == 'lann(') and not in_langda:
                        in_langda = True
                        main_bracket_stack.append("depth")
                        
                        # If there's code before langda, we cut it as non-langda code in a single block
                        if code_line_st < idc:
                            code_segment = line[code_line_st:idc]
                            dense_code_with_comments.append((code_segment, "", PredicateState.NONE.value))

                        code_line_st = idc
                        idc += 5
                        continue
                    # ========================= EXTENDABLE: ??? ============================ #
                    # The new extend logic for detect other predicates could be inserted here!
                    elif (idc <= len(line) - 6 and line[idc:idc+6] == 'query(') and not in_langda:
                        has_query = True
                    # ......
                    # <<<====================== EXTENDABLE AREA =========================>>> #
                    # Tracking bracket matching for langda
                    elif in_langda:
                        if line[idc] == '(' and not in_quotes:
                            main_bracket_stack.append("depth")
                        elif line[idc] == ')' and not in_quotes:
                            if len(main_bracket_stack) > 0:
                                main_bracket_stack.pop()

                            # If bracket stack is empty, we've reached the end of langda
                            if not main_bracket_stack:
                                in_langda = False

                                # Add the langda code segment
                                code_line_nd = idc
                                code_segment = line[code_line_st:code_line_nd+1]

                                # ------------ check comment in remain line ------------- #
                                # ------------ there's a problem: when the pattern is not unique, it will cause some error.
                                comment_segment = "" # give a default value, prevent from none value error
                                comment_match = re.search(r'"\)\s*%', code_segment) # find the pattern: ") + optional spaces + %                                
                                if comment_match:
                                    comment_pos = line.find('%', comment_match.start())
                                    if comment_pos != -1:
                                        comment_segment = line[comment_pos:]
                                        dense_code_with_comments.append((code_segment, comment_segment, PredicateState.END.value)) # At the end of a langda, we use "END"!!!

                                dense_code_with_comments.append((code_segment, "", PredicateState.END.value)) # At the end of a langda, we use "END"!!!

                                # Set the start for any following non-langda code
                                code_line_st = idc + 1
                                code_line_nd = None
                                # if comment_segment:
                                #     break
                # ------------------------------PART2------------------------------ #
                # ------------------------- check comment ------------------------- #
                if not in_quotes:

                    ### 1.Single Line Comment -------------------------------- #
                    if line[idc] == '%' and not in_multiline_comment:
                        code_line_nd = idc
                        if code_line_st < code_line_nd: # ignore empty line
                            code_segment = line[code_line_st:code_line_nd]
                            comment_segment = line[idc:]  # store the comments
                            dense_code_with_comments.append((code_segment, comment_segment, self._map_state(in_langda)))
                        else:
                            # the whole block is a comment (why I do not say "line", because there's code_line_st)
                            comment = line[idc:]
                            dense_code_with_comments.append(("", comment, self._map_state(in_langda)))
                        break

                    ### 2.Start of Multiline Comment -------------------------------- #
                    if idc < len(line) - 1 and line[idc:idc+2] == '/*':
                        in_multiline_comment = True
                        code_line_nd = idc
                        comment_part = line[idc:]
                        if code_line_st < code_line_nd:  # ignore empty line
                            code_segment = line[code_line_st:code_line_nd]
                            dense_code_with_comments.append((code_segment, "", self._map_state(in_langda)))
                        current_comment = comment_part  # gather multiline comments 
                        idc += 2
                        continue

                    ### 3.End of Multiline Comment -------------------------------- #
                    elif idc < len(line) - 1 and line[idc:idc+2] == '*/':
                        in_multiline_comment = False
                        current_comment += "\n" + line[:idc+2]  # add */ to the comment

                        # add the comment together with the previous code
                        if len(dense_code_with_comments) > 0:
                            # we use is_langda_flag to seperate it from is_langda
                            last_code, last_comment, is_langda_flag = dense_code_with_comments[-1]
                            if last_comment:
                                dense_code_with_comments[-1] = (last_code, last_comment + "\n" + current_comment, is_langda_flag)
                            else:
                                dense_code_with_comments[-1] = (last_code, current_comment, is_langda_flag)
                        else:
                            # if there's no code before it
                            dense_code_with_comments.append(("", current_comment, self._map_state(in_langda)))

                        current_comment = ""  # reset comment
                        idc += 2
                        code_line_st = idc
                        continue

                    ### 4.Continuely processing -------------------------------- #
                    elif in_multiline_comment:
                        if idc == 0:  
                            end_pos = line.find('*/', idc)
                            if end_pos != -1:

                                idc += 1
                                continue
                            else:
                                current_comment += "\n" + line
                                break
                        idc += 1
                        continue

                    # ----------------------------PART3---------------------------- #
                    # ---------- line change after a parent predicate end --------- #
                    elif line[idc] == '.' and not main_bracket_stack:
                        if idc > 0 and not line[idc-1].isdigit() and (idc == len(line)-1 or not line[idc+1].isdigit()):
                            code_line_nd = idc
                            code_segment = line[code_line_st:code_line_nd+1]
                            dense_code_with_comments.append((code_segment, "", self._map_state(in_langda)))
                            if idc+1 <len(line): 
                                code_line_st = idc+1
                                code_line_nd = None

                # ------------------------------PART4------------------------------ #
                # --------------- process quotes and escape symbols --------------- #
                # Escaped state check
                if line[idc] == '\\' and not is_escaped:
                    is_escaped = True
                    idc += 1
                    continue
                
                # Quoted state check
                if line[idc] == '"' and not is_escaped:
                    in_quotes = not in_quotes

                # -----%---- # new char # -----%---- #
                is_escaped = False
                idc += 1

            # ------------------------------PART5------------------------------ #
            # --------- ---------- process end of the line -------------------- #
            # Reach the end of the line, if there is code and it is not in a multi-line comment, add it to the pure code
            if not in_multiline_comment and code_line_st < len(line) and code_line_nd is None: # ignore empty line
                code_segment = line[code_line_st:]
                dense_code_with_comments.append((code_segment, "", self._map_state(in_langda)))

            # -----%---- # new line # -----%---- #
            idl += 1

        dcwc_save = []
        for code, comment, is_langda in dense_code_with_comments:
                dcwc_save.append(f"LANGDA:{is_langda}||CODE:{code}|      COMMENT: {comment}")

        return dense_code_with_comments, has_query # [(code,comment,is_langda),...]


    # =============================== CODE FOR PARSING LAGNDA AND LANN =============================== #
    def _parse_lann_or_langda_content_to_dicts(self,content) -> dict:
        """
        Parse content in LANN or LANGDA format into a dictionary.
        Args:
            content: String content to parse, typically obtained from match.group(1)
        Returns:
            A dictionary where each key-value pair represents a parsed term
        """
        result_dict = {}
        term_start = 0
        
        # State variables
        in_quotes = False
        is_escaped = False
        in_brackets = 0
        current_part = ""  # Initialize current_part
        
        # ======================Part1: store terms in a list====================== #
        idc = 0  # index of content character
        while idc < len(content):
            # Handle quotes and escaping (with a state machine)
            if content[idc] == '"' and not is_escaped:
                in_quotes = not in_quotes
            elif content[idc] == '[' and not in_quotes:
                in_brackets += 1
                current_part += content[idc]
            elif content[idc] == ']' and not in_quotes:
                in_brackets -= 1
                current_part += content[idc]

            # Update escape state
            is_escaped = content[idc] == '\\' and not is_escaped

            # Separate into terms, when: not in quotes, not in bracket, and current char is ","
            if not in_quotes and in_brackets == 0 and (content[idc] == ',' or idc == len(content) - 1):
                end_idx = idc if content[idc] == ',' else idc + 1
                if not term_start < end_idx:
                    raise ValueError("Term not found, please check the definition of langda and lann.")
                term = content[term_start:end_idx].strip()

                # =================== Part2: find keys and value pairs =============== #
                idt = 0  # index of term character
                has_value = False  # Initialize has_value

                while idt < len(term):
                    if term[idt] == ':':
                        value_start = idt + 1
                        has_value = True
                        break

                    idt += 1

                # =================== Part3: parse each term as key,value pair =============== #
                # extract key and value
                if has_value:
                    key = term[0:idt].strip()
                    value = term[value_start:].strip()

                    # remove quotes 
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]

                    result_dict[key] = value
                else:
                    # in case there's no value, just a key
                    key = term.strip()
                    result_dict[key] = ""

                term_start = idc + 1  # next term...

            idc += 1

        if not result_dict:
            raise ValueError("Langda information not found, forgot to define langda parameters?")

        return result_dict


    def replace_langda_and_lann_terms(self,text_list:List[Tuple[str, str, str]], placeholder="{{LANGDA}}") -> Tuple[List[str],List[dict],List[LangdaDict]]:
        """
        Replace langda and lann predicates in the given text list.
        And store informations in dictonary
        Args:
            text_list: List of tuples (code, comment, predicate_status)
                    where predicate_status can be "NONE", "BODY", or "END."
        It calls the function: self._parse_lann_or_langda_content_to_dicts()
        Returns:
            Tuple of (modified text list, lann_dicts, langda_dicts)
        """
        # Initialize outputs
        text_list_copy = text_list.copy()  # Create a copy to avoid modifying the original
        lann_dicts:List[dict] = []
        langda_dicts:List[LangdaDict] = []
        result_text_list = []

        # State variables
        single_langda = []
        single_lann = []
        single_comment = []
        in_langda = False
        in_lann = False

        predicate_head = ""

        idl = 0
        while idl < len(text_list_copy):
            current_item:Tuple[str,str,str] = text_list_copy[idl]
            if len(current_item) != 3:
                raise ValueError(f"Warning: Position {idl} has a uncorrect form: {current_item}")

            # -------------------- #           PART0            # -------------------- #
            # -------------------- Prepare for parsing the langda ----------------- #
            (code, comment, predicate_status) = current_item
            if ":-" in code:
                predicate_head, _, _ = code.strip().partition(":-")
            if code and "." == code[-1]:
                predicate_head = ""

                # if code == ".":
                #     idl += 1
                #     continue # ignore the pure "." line ==> this is actually for the llm code to prevent from generate double "."

            in_lan = not(predicate_status==PredicateState.NONE.value)

            has_lann = code.startswith("lann(")
            # Start of lann predicate
            if has_lann and in_lan:
                in_lann = True
                single_lann = []
                single_comment = []

                if not idl + 1 < len(text_list_copy):
                    raise ValueError("The code is incomplete, please check your lann predicates.")

            has_langda = code.startswith("langda(")
            # Start of langda predicate
            if has_langda and in_lan:
                in_langda = True
                single_langda = []
                single_comment = []

            # -------------------- #           PART1            # -------------------- #
            # -------------------- Process single lann predicates -------------------- #
            if in_lann:
                # Middle of lann predicate
                if predicate_status == PredicateState.BODY.value:
                    single_lann.append(code)
                    single_comment.append(comment)

                # End of lann predicate
                elif predicate_status == PredicateState.END.value:
                    # Add the current segment
                    single_lann.append(code)
                    single_comment.append(comment)
                    # Create the full lann term and its dict representation
                    full_lann_term = "".join(single_lann)
                    full_lann_content = full_lann_term[5:-1]
                    lann_dict_content = self._parse_lann_or_langda_content_to_dicts(full_lann_content)

                    # Replace the lann segments with nn(net_name,[X],Y,[1,2,3])::digit(X,Y).
                    nn_term = f"nn({','.join([k for k in lann_dict_content.keys()])})"
                    lann_dict_content['nn'] = nn_term

                    lann_dicts.append(lann_dict_content)

                    # Filter out empty comments before joining (optional, same as langda)
                    filtered_comments = [c for c in single_comment if c]
                    joined_comments = "\n".join(filtered_comments) + "\n" + nn_term

                    result_text_list.append(joined_comments)

                    # Reset state
                    lann_dict_content = {}
                    in_lann = False

            # -------------------- #            PART2             # -------------------- #
            # -------------------- Process single langda predicates -------------------- #
            elif in_langda:
                # Middle of langda predicate
                if predicate_status == PredicateState.BODY.value:
                    single_langda.append(code)
                    single_comment.append(comment)

                # End of langda predicate
                elif predicate_status == PredicateState.END.value:
                    # Add the current segment
                    single_langda.append(code)
                    single_comment.append(comment)
                    # Create the full langda term and its dict representation
                    full_langda_term = "\n".join(single_langda)

                    full_langda_content = full_langda_term[7:-1]
                    langda_dict_content = self._parse_lann_or_langda_content_to_dicts(full_langda_content)
                    langda_dict_content = self.clean_result_fields(
                        langda_dict_content, 
                        ["LOT", "NET", "LLM", "FUP"],
                        [None,None,None,"True"])
                    langda_dict_content["HEAD"] = predicate_head

                    langda_dict_content_for_hash = self.clean_result_fields(
                        langda_dict_content, 
                        ["HEAD", "LOT", "NET", "LLM"])
                    langda_md5_digits = _compute_short_md5(8,langda_dict_content_for_hash, upper=True)

                    langda_dict_content["HASH"] = langda_md5_digits
                    langda_dicts.append(langda_dict_content)

                    # Filter out empty comments before joining
                    filtered_comments = [c for c in single_comment if c]
                    joined_comments = "\n".join(filtered_comments) + placeholder
                    
                    # Replace all items from langda_start to idl with a single item containing our joined comments
                    # text_list_copy[langda_start:idl+1] = [(joined_comments, "", "NONE")]
                    result_text_list.append(joined_comments)
                    
                    # Reset state
                    langda_dict_content = {}
                    in_langda = False

            else:
                result_text_list.append(code + comment)
            
            idl += 1
        return result_text_list, lann_dicts, langda_dicts
        # return [item[0] for item in text_list_copy], lann_dict, langda_dicts

# =============================== FINAL PARSER API =============================== #
def integrated_code_parser(text:str, placeholder) -> Tuple[str, List[dict], List[LangdaDict], bool]:
    parser = Parser()
    text_list, has_query = parser.get_dense_code_with_comments(text)
    result_text, lann_dicts, langda_dicts = parser.replace_langda_and_lann_terms(text_list, placeholder)
    return "\n".join(result_text), lann_dicts, langda_dicts, has_query