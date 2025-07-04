import os
import shutil
import json
import pandas as pd
from openpyxl import load_workbook
import openpyxl
from utils.log_main import logger

def create_debate_directory(topic_id, chat_id, helper_type):
    """
    Creates directory structure for debate logs with given topic_id, chat_id, and helper_type.
    
    Args:
        topic_id: Identifier for the debate topic
        chat_id: Unique identifier for this specific chat instance
        helper_type: Type of helper used (no_helper, vanilla, fallacy)
    
    Returns:
        str: Path to the created directory
    """
    # Define base debates directory
    debates_dir = "debates"
    
    # Create general debates folder if it doesn't exist
    if not os.path.exists(debates_dir):
        os.makedirs(debates_dir)
        logger.info(f"Created debates directory: {debates_dir}", extra={"msg_type": "system"})
    
    # Create topic directory if it doesn't exist
    topic_dir = os.path.join(debates_dir, str(topic_id)) # Creates debates/topic_id
    if not os.path.exists(topic_dir):
        os.makedirs(topic_dir)
        logger.info(f"Created topic directory: {topic_dir}", extra={"msg_type": "system"})
    
    # Create helper-type subdirectory if it doesn't exist
    helper_dir = os.path.join(topic_dir, helper_type)
    if not os.path.exists(helper_dir):
        os.makedirs(helper_dir)
        logger.info(f"Created helper directory: {helper_dir}", extra={"msg_type": "system"})
    
    # Saving current debate:
    chat_dir = os.path.join(topic_dir, helper_type, str(chat_id))
    if os.path.exists(chat_dir): #Shouldnt happen, because chat_id is random
        logger.warning(f"Chat directory already exists: {chat_dir}", extra={"msg_type": "system"})
    else:
        os.makedirs(chat_dir)
        logger.info(f"Created chat directory: {chat_dir}", extra={"msg_type": "system"})
    
    return chat_dir

def save_debate_logs(chat_dir, remove_originals=True):
    """
    Copy all logs from the logs directory to the debate directory.
    
    Args:
        chat_dir: Path to the debate directory
        remove_originals: Whether to delete the original log files after copying

    Returns:
        bool: True if successful, False otherwise
    """
    # Source logs directory
    logs_dir = "logs"
    
    # Check if source logs directory exists
    if not os.path.exists(logs_dir) or not os.path.isdir(logs_dir):
        logger.warning(f"Source logs directory not found: {logs_dir}", 
                     extra={"msg_type": "system"})
        return False
    
    try:
        # Get all log files from logs directory
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        
        if not log_files:
            logger.warning(f"No log files found in {logs_dir}", 
                         extra={"msg_type": "system"})
            return False
        
        # Track if we successfully processed at least one file
        success = False
        
        # Process each log file
        for log_filename in log_files:
            source_path = os.path.join(logs_dir, log_filename)
            
            try:
                # Simply copy the entire file to the chat directory
                dest_path = os.path.join(chat_dir, log_filename)
                shutil.copy2(source_path, dest_path)
                
                # If requested, delete the original after copying
                if remove_originals:
                    # Create empty file to replace the original
                    with open(source_path, 'w') as f:
                        pass  # Just create an empty file
                
                success = True
                logger.info(f"Copied log file {log_filename} to {dest_path}", 
                           extra={"msg_type": "system"})
            
            except Exception as e:
                logger.error(f"Error processing log file {log_filename}: {e}", 
                           extra={"msg_type": "system"})
        
        if success:
            logger.info(f"Successfully saved all log files to {chat_dir}", 
                       extra={"msg_type": "system"})
            return True
        else:
            logger.warning(f"Failed to copy any log files to {chat_dir}", 
                         extra={"msg_type": "system"})
            return False
            
    except Exception as e:
        logger.error(f"Error saving debate logs: {e}", 
                   extra={"msg_type": "system"})
        return False

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
    
    try:
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



