import os
import json
import time
import traceback
import statistics  # For calculating statistical data
from pathlib import Path
from tqdm import tqdm
from langda import langda_solve
from langda.utils.test_tools import _problog_test
from langda.utils import invoke_agent, _find_all_blocks

def process_all(test_directory_path, answer_directory_path, output_json_dir, output_pl_dir,
                agent_type, model_name, repeat_count):
    
    # Convert string paths to Path objects
    test_directory_path = Path(test_directory_path)
    answer_directory_path = Path(answer_directory_path)
    output_json_dir = Path(output_json_dir)
    output_pl_dir = Path(output_pl_dir)
    
    # Create output directories
    output_json_dir.mkdir(parents=True, exist_ok=True)
    output_pl_dir.mkdir(parents=True, exist_ok=True)
    
    # Track summary statistics without storing all results in memory
    file_summaries = []
    success_form_count = 0
    success_result_count = 0
    invalid_form_count = 0
    invalid_result_count = 0
    error_count = 0
    total_process_time = 0
    total_runs = 0
    
    final_result_path = output_json_dir / "_final_result.json"
    
    # Find all prompt files
    prompt_files = []
    for root, _, files in os.walk(test_directory_path):
        for file in files:
            prompt_files.append(Path(root) / file)

    total_files = len(prompt_files)
    print(f"*** Found {total_files} files to process ***")
    print(f"*** Each file will be processed {repeat_count} times ***")
    total_iterations = total_files * repeat_count
    pbar = tqdm(total=total_iterations, desc="Processing files")
    overall_start_time = time.time()
    
    # Process each prompt file
    for idx, prompt_file in enumerate(prompt_files, start=1):
        # This is for skipping:
        if idx < 20:
            continue
        file_basename = (prompt_file.name).split(".")[0]
        part1, part2 = file_basename.split(":")
        file_basename = f"{part1}_{part2}"
        file_results = []  # Store results for this file only
        
        # Find corresponding answer file
        answer_file = None
        for root, _, files in os.walk(answer_directory_path):
            for file in files:
                if file.startswith(file_basename[:10]):
                    answer_file = Path(root) / file
                    break
            if answer_file:
                break

        if not answer_file:
            print(f"Warning: No matching answer file found for answer_file: {file_basename[:10]}, skipping")
            pbar.update(repeat_count)  # Update progress bar, skip all repeats
            continue

        # Read answer file for comparison (true_string)
        try:
            with open(answer_file, "r", encoding='utf-8') as f:
                true_string = f.read()
        except Exception as e:
            print(f"Error reading answer file {answer_file}: {str(e)}")
            pbar.update(repeat_count)  # Update progress bar, skip all repeats
            continue

        # Read the rules from the prompt file
        try:
            with open(prompt_file, "r", encoding='utf-8') as f:
                rules_string = f.read()
        except Exception as e:
            print(f"Error reading prompt file {prompt_file}: {str(e)}")
            pbar.update(repeat_count)  # Update progress bar, skip all repeats
            continue
        
        # Local counters for this file
        file_success_form_count = 0
        file_success_result_count = 0
        file_invalid_form_count = 0
        file_invalid_result_count = 0
        file_error_count = 0
        file_process_times = []
        
        # Repeat execution n times
        for repeat_idx in range(repeat_count):
            total_runs += 1
            process_time = 0
            repeat_suffix = f"[{repeat_idx+1}/{repeat_count}]" if repeat_count > 1 else ""
            pbar.set_description(f"*** Processing {file_basename} [{idx}/{total_files}] {repeat_suffix} ***")
            file_name = f"{file_basename}_run{repeat_idx+1}"
            
            # Initialize result dict
            result = {
                "file_name": file_basename,
                "Validity_form": "ERROR", 
                "Validity_result": "ERROR",
                "running_time": "None",
                "process_time": 0,
                "final_result": "",
                "final_report": "",
                "run_index": repeat_idx+1
            }
            
            try:
                # File process start time
                start_time = time.time()
                print(f"\nStarting Langda_Agent for {file_basename} (Run {repeat_idx+1}/{repeat_count})...")
                
                # Generate code using langda_solve
                result_rule = langda_solve(
                    agent_type=agent_type,
                    rule_string=rules_string,
                    model_name=model_name,
                    prefix=file_name,
                )
                
                process_time = time.time() - start_time
                
                # Prepare input for final evaluation
                input_data = {
                    "original_ruleset": true_string,
                    "original_result": _problog_test(true_string),
                    "generated_ruleset": result_rule,
                    "generated_result": _problog_test(result_rule),
                    "test_analysis": [], # no need to analysis any detailed rules
                }
                
                # Get final evaluation
                final_result, _, _ = invoke_agent(
                    agent_type="simple", 
                    model_name=model_name, 
                    tools=[], 
                    prompt_type="final_test", 
                    input=input_data,
                )
                    
                # Parse final result
                final_blocks = _find_all_blocks("final", final_result)
                if final_blocks:
                    final_dict = final_blocks[0]
                    Validity_form = final_dict.get("Validity_form", "false")
                    Validity_result = final_dict.get("Validity_result", "false") 
                    final_report = final_dict.get("Report", "No report generated")
                else:
                    Validity_form = "false"
                    Validity_result = "false"
                    final_report = "Failed to parse evaluation result"
                
                # Update result dict
                result.update({
                    "Validity_form": Validity_form,
                    "Validity_result": Validity_result,
                    "running_time": f"{process_time:.2f}s",
                    "process_time": process_time,
                    "final_result": result_rule,
                    "final_report": final_report
                })

                # Save PL file
                pl_output_path = output_pl_dir / f"{file_basename}_run{repeat_idx+1}_result.pl"
                with open(pl_output_path, 'w', encoding='utf-8') as pl_file:
                    pl_file.write(f"{result_rule}\n\n/* Result Report:\nValidity_form: {Validity_form}\nValidity_result: {Validity_result}\nReport: {final_report}\n*/")
                
                print(f"Workflow completed for {file_basename} (Run {repeat_idx+1})")
                
                # Count successes and failures
                if str(Validity_form).lower() == "true":
                    file_success_form_count += 1
                    success_form_count += 1
                elif str(Validity_form).lower() == "false":
                    file_invalid_form_count += 1
                    invalid_form_count += 1
                else:
                    file_error_count += 1
                    error_count += 1
                        
                if str(Validity_result).lower() == "true":
                    file_success_result_count += 1
                    success_result_count += 1
                elif str(Validity_result).lower() == "false":
                    file_invalid_result_count += 1
                    invalid_result_count += 1

            except Exception as e:
                print(f"Critical error in agent execution for {file_basename} (Run {repeat_idx+1}): {str(e)}")
                traceback.print_exc()
                
                # Calculate processing time even on error
                process_time = time.time() - start_time if 'start_time' in locals() else 0
                
                result.update({
                    "Validity_form": "ERROR",
                    "Validity_result": "ERROR", 
                    "running_time": "None",
                    "process_time": process_time,
                    "final_result": f"Agent execution error: {str(e)}",
                    "final_report": f"Stack trace: {traceback.format_exc()}"
                })
                
                file_error_count += 1
                error_count += 1

            # Track timing
            total_process_time += process_time
            file_process_times.append(process_time)
            
            # Extract and format result entry
            try:
                entry = {
                    "file_name": file_basename, 
                    "run_index": repeat_idx+1,
                    "Validity_form": result.get("Validity_form", "N/A"),
                    "Validity_result": result.get("Validity_result", "N/A"),
                    "running_time": result.get("running_time", "None"),
                    "process_time": process_time
                }
                
                # Add to file results list
                file_results.append(entry)

                # Save individual run result to a separate JSON file
                json_output_path = output_json_dir / f"{file_basename}_run{repeat_idx+1}_result.json"
                with open(json_output_path, 'w', encoding='utf-8') as json_file:
                    # Save the full result including final_result/final_report to the individual file
                    full_entry = entry.copy()
                    full_entry["final_result"] = result.get("final_result", "")
                    full_entry["final_report"] = result.get("final_report", "")
                    json.dump(full_entry, json_file, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Error processing results for {file_basename} (Run {repeat_idx+1}): {str(e)}")
                
                # Update counters even on error
                file_error_count += 1
                error_count += 1

            # Update progress bar
            pbar.update(1)
            pbar.set_postfix(
                validity=str(result.get("Validity_result", "N/A")), 
                time=f"{process_time:.1f}s", 
                run=f"{repeat_idx+1}/{repeat_count}"
            )

        # Calculate and save summary statistics for this file
        if file_process_times:
            file_summary = {
                "file_name": file_basename,
                "runs": repeat_count,
                "avg_process_time": statistics.mean(file_process_times),
                "min_process_time": min(file_process_times),
                "max_process_time": max(file_process_times),
                "std_dev_time": statistics.stdev(file_process_times) if len(file_process_times) > 1 else 0,
                "success_form_count": file_success_form_count,
                "success_result_count": file_success_result_count,
                "invalid_form_count": file_invalid_form_count,
                "invalid_result_count": file_invalid_result_count,
                "error_count": file_error_count,
                "success_form_rate": file_success_form_count / repeat_count if repeat_count > 0 else 0,
                "success_result_rate": file_success_result_count / repeat_count if repeat_count > 0 else 0
            }
            
            # Add to global file summaries list (without individual results)
            file_summaries.append(file_summary)
            
            # Save file summary to separate JSON
            summary_output_path = output_json_dir / f"{file_basename}_summary.json"
            with open(summary_output_path, 'w', encoding='utf-8') as json_file:
                # Include individual results only in the per-file summary
                summary_with_details = file_summary.copy()
                summary_with_details["individual_results"] = file_results
                json.dump(summary_with_details, json_file, indent=2, ensure_ascii=False)
                
            print(f"\nSummary for {file_basename}:")
            print(f"- Success form rate: {file_summary['success_form_rate']*100:.1f}%")
            print(f"- Success result rate: {file_summary['success_result_rate']*100:.1f}%")
            print(f"- Avg process time: {file_summary['avg_process_time']:.1f}s")
            
        # Save intermediate results without storing all individual run details
        with open(str(final_result_path) + ".temp", 'w', encoding='utf-8') as f:
            intermediate_summary = {
                "files_processed": idx,
                "total_files": total_files,
                "repeat_count": repeat_count,
                "total_runs_completed": total_runs,
                "success_form_count": success_form_count,
                "success_result_count": success_result_count,
                "invalid_form_count": invalid_form_count,
                "invalid_result_count": invalid_result_count,
                "error_count": error_count,
                "file_summaries": file_summaries
            }
            json.dump(intermediate_summary, f, indent=2, ensure_ascii=False)
    
    pbar.close()
    
    # =============== Final Summary =============== #
    overall_process_time = time.time() - overall_start_time
    
    final_summary = {
        "test_completed": True,
        "total_files": total_files,
        "repeat_count": repeat_count,
        "total_runs": total_runs,
        "overall_process_time": overall_process_time,
        "avg_time_per_run": total_process_time / total_runs if total_runs > 0 else 0,
        "success_form_count": success_form_count,
        "success_result_count": success_result_count,
        "invalid_form_count": invalid_form_count,
        "invalid_result_count": invalid_result_count,
        "error_count": error_count,
        "success_form_rate": success_form_count / total_runs if total_runs > 0 else 0,
        "success_result_rate": success_result_count / total_runs if total_runs > 0 else 0,
        "file_summaries": file_summaries
    }
    
    # Save final summary
    with open(final_result_path, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"Total execution time: {overall_process_time:.2f}s")
    print(f"Total runs: {total_runs}")
    print(f"Success form rate: {final_summary['success_form_rate']*100:.1f}%")
    print(f"Success result rate: {final_summary['success_result_rate']*100:.1f}%")
    print(f"Average time per run: {final_summary['avg_time_per_run']:.2f}s")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)  # Change working directory to script directory
    print(f"Current working directory: {os.getcwd()}")
    test_path = "rules/test_prompt"
    answer_path = "rules/test_answer"
    output_json_dir = "history/json"
    output_pl_dir = "history/result"
    
    # Set repeat count
    repeat_count = 5  # Default 5 times, can be adjusted as needed
    
    process_all(
        test_directory_path=test_path, 
        answer_directory_path=answer_path, 
        output_json_dir=output_json_dir, 
        output_pl_dir=output_pl_dir, 
        agent_type="double_dc",
        model_name="deepseek-chat", 
        repeat_count=repeat_count  
    )
    print(f"JSON results saved to {output_json_dir}")
    
    # Generate final report
    final_result_path = Path(output_json_dir) / "_final_result.json"
    
