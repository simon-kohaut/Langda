import signal
from problog.program import PrologString
from problog import get_evaluatable, evaluator
from typing import Any, Type, Tuple, Callable
import traceback
import multiprocessing as mp

import logging
logger = logging.getLogger(__name__)

def with_timeout(func, file_basename, timeout=120, *args, **kwargs):
    """
    timeout mechanism...
    args:
        func: input main workflow function: agent.call_langda_workflow
        file_basename: current file name
        timeout: timeout for timeout_handler
        flexible args for called function
    return:
        result of the called function
    """

    def timeout_handler(signum, frame):
        # Define the alarm handler function
        logger.error(f"Function timed out while processing file: {file_basename}")
        raise TimeoutError(f"Function timed out while processing file: {file_basename}")
    
    # Setting up the signal processor:
    signal.signal(signal.SIGALRM, timeout_handler) # TSIGALRM: imer signal from alarm(2).  
    signal.alarm(timeout)  # Set timeout

    try:
        result = func(*args, **kwargs)
        return result
    except TimeoutError as e:
        logger.error(f"ERROR: Execution timed out after {timeout} seconds")
        return f"ERROR: Execution timed out after {timeout} seconds"
    finally:
        signal.alarm(0)  # Ensure to close the alarm
  
def _problog_test(model: str) -> Tuple[str,bool]:
    """Run the Problog evaluation tool."""
    logger.info("""Running problog_test_tool...""")
    try:
        result = []
        evaluatable:Type[evaluator.Evaluatable] = get_evaluatable().create_from(PrologString(model))
        results:(dict | Any) = evaluatable.evaluate()

        for query_key, probability in results.items():
            result_line = f"{query_key} = {probability:.4f}"
            result.append(result_line)
            
        if len(result) > 20:
            result_lines = "% Problog Inference Result：\n" + "\n".join(result[:20]) + "\n ...<other results>... "
        else:
            result_lines = "% Problog Inference Result：\n" + "\n".join(result)
        logger.info("\n# -------------------------- result_lines -------------------------- #\n" + "\n".join(result[:5]))
        return result_lines
    except Exception:
        tb_lines = traceback.format_exc().splitlines()
        last_five = tb_lines[-5:]
        error_message = "Error evaluating Problog model:\n" + "\n".join(last_five)
        logger.error(error_message)
        return error_message
    finally:
        logger.info("\n# -------------------------- End of problog_test_tool -------------------------- #")
