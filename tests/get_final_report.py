
import os
import json
import statistics  # For calculating statistical data
from pathlib import Path

from collections import defaultdict

def generate_final_report_from_json(json_directory, output_final_path=None):
    """
    Generate a final statistical report from JSON result files in specified directory
    
    Args:
        json_directory: Path to directory containing result JSON files
        output_final_path: Path to save final report (defaults to _final_result.json in json_directory)
    
    Returns:
        Dictionary containing the final summary report
    """
    
    # Initialize counters
    total_files = 0
    total_runs = 0
    success_form_count = 0
    success_result_count = 0
    invalid_form_count = 0
    invalid_result_count = 0
    error_count = 0
    total_process_time = 0
    
    # Group all runs by file name
    file_results = defaultdict(list)
    file_summaries = []
    
    # Find all result files
    result_files = [os.path.join(json_directory, f) for f in os.listdir(json_directory) 
                    if f.endswith("_result.json") and not f.startswith("_final")]
    
    # Process all result files
    for result_file in result_files:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                
            file_name = result.get("file_name")
            if file_name:
                file_results[file_name].append(result)
                total_runs += 1
                
                # Count validity forms
                validity_form = str(result.get("Validity_form", "")).lower()
                validity_result = str(result.get("Validity_result", "")).lower()
                
                if validity_form == "true":
                    success_form_count += 1
                elif validity_form == "false":
                    invalid_form_count += 1
                elif validity_form in ["error", "timeout"]:
                    error_count += 1
                    
                if validity_result == "true":
                    success_result_count += 1
                elif validity_result == "false":
                    invalid_result_count += 1
                
                # Sum process time
                process_time = result.get("process_time", 0)
                if isinstance(process_time, (int, float)):
                    total_process_time += process_time
                
        except Exception as e:
            print(f"Error processing file {result_file}: {str(e)}")
    
    # Calculate statistics for each file
    unique_files = set(file_results.keys())
    total_files = len(unique_files)
    
    for file_name, results in file_results.items():
        repeat_count = len(results)
        
        # Calculate file-specific statistics
        file_success_form_count = sum(1 for r in results if str(r.get("Validity_form", "")).lower() == "true")
        file_success_result_count = sum(1 for r in results if str(r.get("Validity_result", "")).lower() == "true")
        file_invalid_form_count = sum(1 for r in results if str(r.get("Validity_form", "")).lower() == "false")
        file_invalid_result_count = sum(1 for r in results if str(r.get("Validity_result", "")).lower() == "false")
        file_error_count = sum(1 for r in results if str(r.get("Validity_form", "")).lower() in ["error", "timeout"])
        
        # Calculate time statistics
        file_process_times = [r.get("process_time", 0) for r in results 
                             if isinstance(r.get("process_time", 0), (int, float))]
        
        if file_process_times:
            file_summary = {
                "file_name": file_name,
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
            
            file_summaries.append(file_summary)

    # Set output path
    if output_final_path is None:
        output_final_path = os.path.join(json_directory, "_final_result.json")
    
    # Calculate overall summary
    summary = {
        "total_files": total_files, "repeat_count": repeat_count, "total_runs": total_runs,
        "total_process_time": total_process_time,
        "average_process_time": total_process_time / total_runs if total_runs else 0,
        "success_form_count": success_form_count, "success_result_count": success_result_count,
        "invalid_form_count": invalid_form_count, "invalid_result_count": invalid_result_count,
        "error_count": error_count,
        "overall_success_form_rate": success_form_count / total_runs if total_runs else 0,
        "overall_success_result_rate": success_result_count / total_runs if total_runs else 0,
    }
    
    # Add file success rates
    if repeat_count > 1:
        file_rates = {
            s["file_name"]: {
                "success_form_rate": s["success_form_rate"],
                "success_result_rate": s["success_result_rate"]
            }
            for s in file_summaries
        }
        summary["file_success_rates"] = file_rates
    
    # Create final result
    final_result = {
        "summary": summary,
        "file_summaries": file_summaries
    }
    
    # Save final result
    with open(output_final_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    print("file saved to:",output_final_path)
    if repeat_count > 1:
        print(f"- Overall success form rate: {summary['overall_success_form_rate']*100:.1f}%")
        print(f"- Overall success result rate: {summary['overall_success_result_rate']*100:.1f}%")
    
    return final_result

if __name__ == "__main__":

    output_json_dir = Path("history/json")

    final_result = generate_final_report_from_json(output_json_dir, os.path.join(output_json_dir,"_final_result.json"))
