import os
import shutil
import json
import pandas as pd
from openpyxl import load_workbook
import openpyxl
from filelock import FileLock
from utils.log_main import logger

def create_debate_directory(topic_id, chat_id, helper_type, debates_base_dir="debates"):
    """
    Creates directory structure for debate logs with given topic_id, chat_id, and helper_type.
    
    Args:
        topic_id: Identifier for the debate topic
        chat_id: Unique identifier for this specific chat instance
        helper_type: Type of helper used (no_helper, vanilla, fallacy)
        debates_base_dir: Base directory for debates (default: "debates")
    
    Returns:
        str: Path to the created directory
    """
    # Define base debates directory
    debates_dir = debates_base_dir
    
    # Create general debates folder if it doesn't exist
    if not os.path.exists(debates_dir):
        os.makedirs(debates_dir)
    
    # Create topic directory if it doesn't exist
    topic_dir = os.path.join(debates_dir, str(topic_id)) # Creates debates/topic_id
    if not os.path.exists(topic_dir):
        os.makedirs(topic_dir)
    
    # Create helper-type subdirectory if it doesn't exist
    helper_dir = os.path.join(topic_dir, helper_type)
    if not os.path.exists(helper_dir):
        os.makedirs(helper_dir)
    
    # Saving current debate:
    chat_dir = os.path.join(topic_dir, helper_type, str(chat_id))
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)
    
    return chat_dir

# save_debate_logs function removed - logs are now written directly to the correct location

def save_debate_in_excel(topic_id, claim_data, helper_type, chat_id, result, rounds):
    """
    Save debate results to a central Excel file. Creates the file if it doesn't exist,
    otherwise appends to the existing file.
    
    Args:
        topic_id: Identifier for the debate topic
        claim_data: Dictionary with claim information including the claim text
        helper_type: Type of helper used (no_helper, vanilla_helper, fallacy_helper)
        chat_id: Unique identifier for this specific chat instance
        result: Integer result status (1=convinced, 0=not convinced, 2=other)
        rounds: Number of rounds the debate lasted
        
    Returns:
        bool: True if successful, False otherwise
    """
    excel_file = "all_debates_summary.xlsx"
    lock_file = "all_debates_summary.xlsx.lock"
    
    # Use file lock to ensure only one process writes at a time
    lock = FileLock(lock_file, timeout=30)
    
    try:
        with lock:
            # Get the claim text from the claim data
            claim = claim_data.get('claim', 'Unknown claim')
            
            # Prepare the new row data with rounds after result and before chat_id
            new_row = {
                'topic_id': topic_id,
                'claim': claim,
                'helper_type': helper_type,
                'result': result,
                'rounds': rounds,
                'chat_id': chat_id
            }
            
            # Check if the file already exists
            if os.path.exists(excel_file):
                # Load existing file
                try:
                    df = pd.read_excel(excel_file)
                    # Append new row
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                except Exception as e:
                    logger.error(f"Error reading existing Excel file: {e}", extra={"msg_type": "system"})
                    # If there's an error with the file, create a new one
                    df = pd.DataFrame([new_row])
            else:
                # Create new dataframe with headers
                df = pd.DataFrame([new_row])
            
            # Save dataframe to Excel
            df.to_excel(excel_file, index=False)
                
            logger.info(f"Successfully updated debate summary in {excel_file}", 
                       extra={"msg_type": "system"})
            return True
        
    except Exception as e:
        logger.error(f"Error saving debate to Excel: {e}", 
                   extra={"msg_type": "system"})
        return False



