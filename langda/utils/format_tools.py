import re
import json
import uuid
import hashlib
from typing import Literal, List, Union, Tuple, Dict, Any

import logging
logger = logging.getLogger(__name__)

def _langda_list_to_dict(langda_dicts):
    """
    Just turn [{},{},...] to {"hash1":{},"hash2":{},...}
    """
    langda_hash_index = {}
    for langda_item in langda_dicts:
        if "HASH" in langda_item:
            langda_hash_index[langda_item["HASH"]] = langda_item
    return langda_hash_index

def _expand_nested_list(lists, max_depth=10, current_depth=0):
    """
    Expand nested list to a flat list.
    Includes depth detection to prevent infinite recursion.
    """
    if current_depth > max_depth:
        raise RecursionError(f"Maximum recursion depth {max_depth} exceeded!")

    flat_list = []
    for item in lists:
        if isinstance(item, list):
            nested_items = _expand_nested_list(item, max_depth, current_depth + 1)
            flat_list.extend(nested_items)
        else:
            flat_list.append(item)
    return flat_list


def _list_to_dict(listdict:List[dict]):
    dictdict:Dict[str,Any] = {}
    for dict in listdict:
        key, value = _parse_simple_dictonary(dict)
        dictdict[key] = value
    return dictdict

def _parse_simple_dictonary(code_item:dict) -> Tuple[str, Any]:
    """
    parse the dictonary only has one item, form like: {"hash":Any content here}
    """
    key, value = next(iter(code_item.items()))
    return key, value

def _compute_short_md5(len:int, content:Union[str,dict], upper:bool = False) -> str:
    """
    Computes a short MD5 hash of the given content with specified length.
    Converts to uppercase if upper=True.
    """
    if isinstance(content, dict):
        hash_str = hashlib.md5(json.dumps(content).encode('utf-8')).hexdigest()[:len]
    elif isinstance(content, str):
        hash_str = hashlib.md5(content.encode('utf-8')).hexdigest()[:len]
    else:
        logger.error("_compute_short_md5: the input should be string or dictonary")
        raise TypeError("_compute_short_md5: the input should be string or dictonary")
    return hash_str.upper() if upper else hash_str


def _compute_random_md5(len:int, upper:bool = False) -> str:
    """
    Generates a random MD5-style hash string by taking a UUID and slicing the hex.
    Converts to uppercase if upper=True.
    """
    hash_str = uuid.uuid4().hex[:len].upper()
    return hash_str.upper() if upper else hash_str


def _ordinal(n:int) -> str:
    """
    Simple function to convert an int number to an ordinal
    args:
        n: input number
    """
    # from int number generate ordinal: 1st,2nd,3rd,4th,5th,...
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

def _tokenize_problog(s:str) -> List[tuple]:
    # Tokenize Prolog code into units
    pattern = r":-|\w+|[^\w\s]"
    return [(m.group(), m.start(), m.end()) for m in re.finditer(pattern, s)]

def _merge_problog_preserve(s1:str, s2:str) -> str:

    # s1_lines = s1.rstrip('\n').split('\n')
    # s2_lines = s2.lstrip('\n').split('\n')
    # s1_clean = '\n'.join(s1_lines)
    # s2_clean = '\n'.join(s2_lines)

    tokens1 = _tokenize_problog(s1)
    tokens2 = _tokenize_problog(s2)

    texts1 = [t for t, _, _ in tokens1]
    texts2 = [t for t, _, _ in tokens2]
    
    # longest overlap
    max_k = min(len(texts1), len(texts2))
    for k in range(max_k, 0, -1):
        if texts1[-k:] == texts2[:k]: # we found the overlap!!!
            j_start = tokens2[k-1][2]
            return s1 + s2[j_start:]
    return s1 + s2

def _replace_placeholder(template:str, replacement_list:Union[List[str],List[dict]], placeholder="{{LANGDA}}") -> str:
    """
    Replaces placeholders in a template with items from a replacement list.
    
    args:
        template: template with placeholders
        replacement_list: the list of content that will fit into the placeholder.
        placeholder: default as {{LANGDA}}
        - if the value is None, the corresponding placeholder remains unchanged. 
        - valid input forms: List[str] or List[dict]
    """

    # Extract values from replacement items
    replace_str_list = []
    if replacement_list and all(isinstance(item, dict) for item in replacement_list):
        for item in replacement_list:
            _, value = next(iter(item.items()))
            replace_str_list.append(value)
    else:
        replace_str_list = replacement_list

    # Split the template by placeholder
    segments = template.split(placeholder)
    result = segments[0]
    
    # Process each segment after the first
    for i, seg in enumerate(segments[1:]):

        replace_text = replace_str_list[i]
        # Check if we have a replacement for this placeholder
        if i < len(replace_str_list) and replace_text is not None:
            # !!! SYNTAX FIX !!!
            # deal with overlap: segment[0] & "overlap text" + "overlap text" & replace_text
            result = _merge_problog_preserve(result, replace_text.strip("\n"))
        else:
            # No replacement available, keep the placeholder
            result += placeholder

        # !!! SYNTAX FIX !!!
        # deal with overlap: replace_text & "overlap text" + "overlap text" & segment[1]
        result = _merge_problog_preserve(result, seg)
        
    return result



def _robust_find_block(text:str, block_type:str="report") -> List[str]:
    """Manually find all ``` blocks, this is essential, because we need to ignore ``` blocks in quote"""
    blocks = []
    i = 0
    while i < len(text):
        # Find Start pattern:
        start_pattern = f"```{block_type}"
        start_pos = text.find(start_pattern, i)
        if start_pos == -1:
            break

        start_content = start_pos + len(start_pattern)

        # Find REAL End pattern:
        j = start_content
        in_quotes = False
        while j < len(text):
            char = text[j]

            # Escaped state check
            if char == '\\' and j + 1 < len(text):
                j += 2
                continue
            # Quoted state check
            if char == '"':
                in_quotes = not in_quotes

            if not in_quotes and text[j:j+3] == '```':
                block_content = text[start_content:j].strip()
                blocks.append(block_content)
                i = j + 3
                break
            j += 1
        else:
            break
            
    return blocks

def _find_all_blocks(type: Literal["report", "code", "final"], text: str) -> List[dict]:
    """
    Find and parse code blocks in the text according to the specified type.
    
    Args:
        type: The type of blocks to find ("report", "code", or "final")
        text: The text to search for blocks
        ext_mark: Optional mark for "final" type blocks
        
    Returns:
        List of dictionaries containing the parsed blocks
    """
    blocks: List[dict] = []
    # Select pattern based on purpose
    if type == "report" or type == "final":
        matches = _robust_find_block(text, "report")
        if not matches:
            matches = _robust_find_block(text, "json")
    elif type == "code":
        pattern = r"```(?:problog|[a-z]*)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if not matches:
            pattern = r"```(?:json|[a-z]*)?\n(.*?)```"
            matches = re.findall(pattern, text, re.DOTALL)
    else:
        raise ValueError("you must choose from ['report','code','final']")
    
    for match in matches:
        match_str = match.strip()
        
        try:
            # Try to parse the JSON directly
            match_json = json.loads(match_str)
            # When it succeed...
            if type == "final":
                blocks.append(match_json)
            elif type == "code":
                if isinstance(match_json, dict) and "HASH" in match_json and "Code" in match_json:
                    blocks.append({match_json["HASH"]: match_json["Code"]})
                else:
                    raise TypeError("could not parse code, retry with manually construction")
            elif type == "report":
                if isinstance(match_json, dict) and "HASH" in match_json:
                    blocks.append({match_json["HASH"]: match_json})
                else:
                    raise TypeError("could not parse report, retry with manually construction")

        except json.JSONDecodeError:
            # If JSON parsing fails, try manually constructing a dictionary
            try:
                if type == "code":
                    hash_value = re.search(r'"HASH":\s*"([^"]+)"', match_str).group(1)
                    code_value = re.search(r'"Code":\s*"((?:\\.|[^"])*)"', match_str).group(1)
                    
                    # Unescape the code
                    code_value = code_value.replace('\\\\', '\\').replace('\\"', '"').replace('\\n', '\n')
                    blocks.append({hash_value: code_value})

                elif type == "report":
                    hash_value = re.search(r'"HASH":\s*"([^"]+)"', match_str).group(1)
                    error_summary = re.search(r'"ErrorSummary":\s*"((?:[^"\\]|\\.)*)"', match_str).group(1)
                    suggested_fix = re.search(r'"SuggestedFix":\s*"((?:[^"\\]|\\.)*)"', match_str).group(1)

                    need_regen = re.search(r'"NeedRegenerate":\s*(true|false)', match_str).group(1)

                    # Unescape the report
                    error_summary = error_summary.replace('\\"', '"').replace('\\\\', '\\')
                    suggested_fix = suggested_fix.replace('\\"', '"').replace('\\\\', '\\')
                    blocks.append({hash_value: {
                        "HASH":hash_value,
                        "ErrorSummary": error_summary,
                        "SuggestedFix": suggested_fix,
                        "NeedRegenerate": need_regen
                    }})

                elif type == "final":
                    # {{"Report": "Fill in your analysis here...", "Validity_form": true|false,"Validity_result": true|false}}
                    report_value = re.search(r'"Report":\s*"((?:\\.|[^"])*)"', match_str).group(1)
                    validity_form_value = re.search(r'"Validity_form":\s*(true|false)', match_str).group(1)
                    validity_result_value = re.search(r'"Validity_result":\s*(true|false)', match_str).group(1)

                    # Unescape the report
                    report_value = report_value.replace('\\"', '"').replace('\\\\', '\\')
                    blocks.append({
                        "Report": report_value,
                        "Validity_form": validity_form_value,
                        "Validity_result": validity_result_value,
                    })

            except Exception as e:
                logger.error(f"Parsing failed: {e}")
                logger.error(f"Original content: {repr(match_str)}")
                continue

    return blocks

def _deep2normal(problog_code: str, user_query:str) -> str:
    """
    remove nn term and add query and facts from user.
    """
    lines = problog_code.split('\n')
    filtered_lines = []
    
    for line in lines:
        if re.match(r'^\s*nn\s*\(.*\)\s*::\s*\w+.*\.\s*$', line):
            continue
        filtered_lines.append(line)
    filtered_lines.append(user_query)
    
    return '\n'.join(filtered_lines)