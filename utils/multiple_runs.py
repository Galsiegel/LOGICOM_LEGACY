#!/usr/bin/env python3
"""
Multiple Runs Script for LOGICOM

This script allows running multiple debates with different combinations of:
- Claim indexes 
- Helper types

It calls the existing main.py for each combination, making minimal changes to existing code.
"""

import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import time
import yaml

def load_config(settings_path: str = "./config/settings.yaml") -> dict:
    """Load settings to get available helper types"""
    try:
        with open(settings_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def get_available_helper_types(settings_path: str = "./config/settings.yaml") -> List[str]:
    """Get list of available helper types from settings"""
    config = load_config(settings_path)
    agent_configs = config.get('agent_configurations', {})
    return list(agent_configs.keys())

def run_single_debate(helper_type: str, claim_index: Optional[int] = None, 
                     settings_path: str = "./config/settings.yaml",
                     models_path: str = "./config/models.yaml") -> bool:
    """
    Run a single debate by calling main.py
    
    Returns True if successful, False if failed
    """
    cmd = [sys.executable, "main.py", "--helper_type", helper_type]
    
    if claim_index is not None:
        cmd.extend(["--claim_index", str(claim_index)])
    
    if settings_path != "./config/settings.yaml":
        cmd.extend(["--settings_path", settings_path])
        
    if models_path != "./config/models.yaml":
        cmd.extend(["--models_path", models_path])
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            print(f"✓ Success: {helper_type}" + (f" claim {claim_index}" if claim_index is not None else " all claims"))
            return True
        else:
            print(f"✗ Failed: {helper_type}" + (f" claim {claim_index}" if claim_index is not None else " all claims"))
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Exception running {helper_type}" + (f" claim {claim_index}" if claim_index is not None else " all claims") + f": {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run multiple LOGICOM debates with different configurations")
    
    # Helper types
    parser.add_argument("--helper_types", nargs="+", 
                       help="List of helper types to run (default: all available)")
    parser.add_argument("--claim_indexes", nargs="+", type=int,
                       help="List of claim indexes to run (default: all claims)")
    parser.add_argument("--settings_path", default="./config/settings.yaml",
                       help="Path to settings YAML file")
    parser.add_argument("--models_path", default="./config/models.yaml", 
                       help="Path to models YAML file")
    parser.add_argument("--list_helpers", action="store_true",
                       help="List available helper types and exit")
    parser.add_argument("--sequential", action="store_true",
                       help="Run claim indexes sequentially for each helper type (default: run all claims per helper)")
    
    args = parser.parse_args()
    
    # List available helpers if requested
    if args.list_helpers:
        available_helpers = get_available_helper_types(args.settings_path)
        print("Available helper types:")
        for helper in available_helpers:
            print(f"  - {helper}")
        return
    
    # Get helper types to run
    if args.helper_types:
        helper_types = args.helper_types
    else:
        helper_types = get_available_helper_types(args.settings_path)
        print(f"No helper types specified, using all available: {helper_types}")
    
    if not helper_types:
        print("No helper types found or specified!")
        return
    
    # Validate helper types exist
    available_helpers = get_available_helper_types(args.settings_path)
    invalid_helpers = [h for h in helper_types if h not in available_helpers]
    if invalid_helpers:
        print(f"Invalid helper types: {invalid_helpers}")
        print(f"Available helpers: {available_helpers}")
        return
    
    # Prepare runs
    runs = []
    total_runs = 0
    
    for helper_type in helper_types:
        if args.sequential and args.claim_indexes:
            # Run specific claim indexes sequentially
            for claim_index in args.claim_indexes:
                runs.append((helper_type, claim_index))
                total_runs += 1
        else:
            # Run all claims for this helper type (or no specific claims)
            claim_index = args.claim_indexes[0] if args.claim_indexes and len(args.claim_indexes) == 1 else None
            runs.append((helper_type, claim_index))
            total_runs += 1
    
    print(f"\nPlanning to run {total_runs} debate configurations:")
    for i, (helper_type, claim_index) in enumerate(runs, 1):
        claim_desc = f"claim {claim_index}" if claim_index is not None else "all claims"
        print(f"  {i}. {helper_type} - {claim_desc}")
    
    print(f"\nStarting runs...")
    
    # Execute runs
    successful_runs = 0
    failed_runs = 0
    start_time = time.time()
    
    for i, (helper_type, claim_index) in enumerate(runs, 1):
        print(f"\n[{i}/{total_runs}] Running {helper_type}" + (f" claim {claim_index}" if claim_index is not None else " all claims"))
        
        success = run_single_debate(
            helper_type=helper_type,
            claim_index=claim_index,
            settings_path=args.settings_path,
            models_path=args.models_path
        )
        
        if success:
            successful_runs += 1
        else:
            failed_runs += 1
    
    # Summary
    elapsed_time = time.time() - start_time
    print(f"\n" + "="*50)
    print(f"SUMMARY")
    print(f"="*50)
    print(f"Total runs: {total_runs}")
    print(f"Successful: {successful_runs}")
    print(f"Failed: {failed_runs}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds")
    
    if failed_runs > 0:
        sys.exit(1)
    else:
        print("All runs completed successfully!")

if __name__ == "__main__":
    main() 