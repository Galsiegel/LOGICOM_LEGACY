import os
import sys
import argparse
import pandas as pd
from tqdm import tqdm
from typing import Dict, Any, Optional, Tuple
import logging
import json
import logging.config

# --- Direct Imports ---
from utils.log_main import logger as debate_logger, setup_logging 
from utils.set_api_keys import set_environment_variables_from_file, API_KEYS_PATH
from config.loader import load_app_config
from core.orchestrator import DebateOrchestrator
from core.debate_setup import DebateInstanceSetup

# Use colorama for terminal colors
from colorama import init, Fore, Style
init(autoreset=True)

# Use our custom debate logger instead of creating a new one
logger = debate_logger

# --- Argument Parsing --- 
def define_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI Debates with Reworked Architecture")
    parser.add_argument("--config_run_name", default="Default_NoHelper", 
                        help="Name of the agent configuration section in settings.yaml to use.")
    parser.add_argument("--claim_index", type=int, default=None, 
                        help="Index of the specific claim in the dataset to run (0-based). Runs all if not specified.")
    parser.add_argument("--settings_path", default="./config/settings.yaml", 
                        help="Path to the main settings configuration file.")
    parser.add_argument("--models_path", default="./config/models.yaml", 
                        help="Path to the LLM models configuration file.")
    parser.add_argument("--max_rounds", type=int, default=None,
                        help="Override the maximum number of debate rounds (default is from settings.yaml)")
    args = parser.parse_args()
    return args

# --- Main Execution Logic --- 
def main():
    # Print statement to verify the script is running
    print("Starting application - initializing logging...")
    
    # --- Central Logging Configuration ---
    # Use our custom setup_logging function instead of manual configuration
    setup_logging()
    
    
    # --- Suppress noisy logs from underlying libraries ---
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("google.api_core").setLevel(logging.WARNING)
    # --------------------------------
    logger.info("Application starting...", extra={"msg_type": "system"})
    # -----------------------------------

    args = define_arguments()
    
    # Set API Keys from file  
    set_environment_variables_from_file(API_KEYS_PATH)

    try:
        # Load Configs
        config = load_app_config(args.settings_path, args.models_path)
        debate_settings = config['settings']['debate_settings']
        run_config_name = args.config_run_name or "Default_NoHelper"
        logger.info(f"Using agent run configuration: {run_config_name}", extra={"msg_type": "system"})
        agent_configs_for_run = config['settings']['agent_configurations'].get(run_config_name)
        if not agent_configs_for_run:
            logger.error(f"Run configuration '{run_config_name}' not found in settings.", extra={"msg_type": "system"})
            sys.exit(1)
        helper_type_name = agent_configs_for_run.get('helper_type_name', run_config_name)

        # Load dataset
        data_path = debate_settings['data_path']
        logger.info(f"Loading data from: {data_path}", extra={"msg_type": "system"})
        
        # Check if the configured path exists directly
        if not os.path.exists(data_path):
             # If not, try resolving it relative to the project root (assuming main.py is in the root)
             project_root = os.path.dirname(os.path.abspath(__file__))
             alt_path_from_root = os.path.join(project_root, data_path.lstrip('./')) 
             logger.info(f"Configured data path '{data_path}' not found. Trying relative to project root: '{alt_path_from_root}'")
             if os.path.exists(alt_path_from_root):
                  data_path = alt_path_from_root
                  logger.info(f"Using alternative data path: {data_path}")
             else:
                  # Use f-string for clarity
                  logger.error(f"Data file not found at specified path '{debate_settings['data_path']}' or relative to project root '{alt_path_from_root}'")
                  sys.exit(1)
        
        # Proceed with loading now data_path is confirmed
        data = pd.read_csv(data_path)
        logger.debug(f"Loaded {len(data)} claims.")

        # Determine claims to run
        claim_indices_to_run = []
        if args.claim_index is not None:
            if 0 <= args.claim_index < len(data):
                claim_indices_to_run = [args.claim_index]
            else:
                logger.error(f"Error: Invalid claim_index {args.claim_index}. Must be between 0 and {len(data)-1}.")
                sys.exit(1)
        else:
            claim_indices_to_run = list(range(len(data)))
            logger.debug(f"Running for all {len(claim_indices_to_run)} claims.")

        # Load Initial Prompt Template
        initial_prompt_path = debate_settings.get('initial_prompt_path')
        if not initial_prompt_path: raise ValueError("initial_prompt_path missing in debate_settings.")
        try:
            with open(initial_prompt_path, 'r', encoding='utf-8') as f:
                initial_prompt_template_content = f.read()
            logger.debug(f"Loaded initial prompt template from: {initial_prompt_path}")
        except FileNotFoundError:
             logger.critical(f"Initial prompt template file not found: {initial_prompt_path}. Exiting."); sys.exit(1)
        except Exception as e:
             logger.critical(f"Error reading initial prompt template {initial_prompt_path}: {e}", exc_info=True); sys.exit(1)

        # --- Run Debates Loop --- 
        topic_id_col = debate_settings.get('topic_id_column', 'id')
        claim_col = debate_settings.get('claim_column', 'claim')

        for index, claim_data in tqdm(data.iloc[claim_indices_to_run].iterrows(), total=len(claim_indices_to_run), desc="Running Debates"):
            topic_id = str(claim_data.get(topic_id_col, index))
            claim_text = str(claim_data.get(claim_col, ''))
            if not claim_text: 
                logger.warning(f"Skipping {topic_id} (Index {index}): empty claim.", 
                              extra={"msg_type": "system"})
                continue

            logger.info(f"\n===== Preparing Claim Index: {index}, Topic ID: {topic_id} ====", 
                       extra={"msg_type": "system"})
            run_result = {}
            try:
                # Instantiate setup class for this claim
                setup = DebateInstanceSetup(
                    agents_configuration=agent_configs_for_run,
                    debate_settings=debate_settings,
                    initial_prompt_template=initial_prompt_template_content, 
                    claim_data=claim_data
                    # Removed resolved_llm_providers/summarizer args
                )
                logger.debug(f"Debater setup complete")

                # Instantiate orchestrator 
                orchestrator = DebateOrchestrator(
                    persuader=setup.persuader, 
                    debater=setup.debater,
                    moderator_terminator=setup.moderator_terminator,
                    moderator_topic_checker=setup.moderator_topic_checker,
                    max_rounds=args.max_rounds if args.max_rounds is not None else int(debate_settings.get('max_rounds', 12))
                )
                logger.debug(f"Orchestrator setup complete")
                
                # Run debate
                run_result = orchestrator.run_debate(
                    topic_id=topic_id, claim=claim_text,
                    log_config=debate_settings,
                    helper_type_name=helper_type_name
                )
                logger.debug(f"Debate run complete")
                run_result['status'] = 'Success'

            except Exception as e:
                # Handle setup or runtime errors 
                logger.error(f"!!!!! Error running debate for Topic ID {topic_id} (Index {index}): {e} !!!!!", 
                           extra={"msg_type": "system"})
                run_result = {
                    "topic_id": topic_id,
                    "claim_index": index,
                    "status": "ERROR",
                    "error_message": str(e)
                }
            
            # Log run completion
            logger.info(f"Debate run complete", extra={"msg_type": "main debate", 
                        "topic_id": topic_id, "claim_index": index, "status": "Success",
                        "result": run_result.get("result"), "rounds": run_result.get("rounds")})

        # At the end, instead of processing in-memory results:
        logger.info(f"All debates completed", extra={"msg_type": "system"})

    except Exception as e:
        logger.critical(f"\nAn unexpected error occurred in main execution: {e}", 
                       extra={"msg_type": "system"})
        sys.exit(1)

if __name__ == '__main__':
    main() 