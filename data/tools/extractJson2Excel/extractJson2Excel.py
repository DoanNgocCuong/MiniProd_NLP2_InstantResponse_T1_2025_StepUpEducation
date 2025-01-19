import pandas as pd
import json
from pathlib import Path
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_json_string(text):
    """Clean and extract JSON from markdown or plain text."""
    if not isinstance(text, str):
        return text
        
    # Remove markdown code blocks if present
    if '```json' in text:
        pattern = r'```json\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0]
    
    # If no markdown, return original text
    return text

def process_response(row):
    """Process a single row and extract JSON data."""
    if 'assistant_response' not in row:
        logger.warning("Column 'assistant_response' not found in row")
        return []
        
    try:
        # Get and clean the response text
        response_text = clean_json_string(row['assistant_response'])
        logger.debug(f"Cleaned text: {response_text[:100]}...")  # Log first 100 chars
        
        # Parse JSON
        response = json.loads(response_text)
        
        # Ensure response is a list
        if not isinstance(response, list):
            response = [response]
        
        # Extract all fields
        processed = []
        for item in response:
            if isinstance(item, dict):
                # Add all fields from the dictionary
                processed.append(item)
            else:
                logger.warning(f"Skipping non-dictionary item: {item}")
        
        return processed
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error processing JSON: {e}")
        logger.error(f"Raw text: {row['assistant_response'][:200]}")  # Log first 200 chars
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Raw text: {row['assistant_response'][:200]}")
        return []

def main():
    # Define the base paths
    SCRIPTS_FOLDER = Path(__file__).parent
    INPUT_FILE = SCRIPTS_FOLDER / 'preprocess_prepare_Prompting_smallTrainsetv7_positive_neutral_learnmore.xlsx'
    OUTPUT_FILE = SCRIPTS_FOLDER / 'processed_prepare_Prompting_smallTrainsetv7_positive_neutral_learnmore.xlsx'

    # Validate input file
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    try:
        # Read input data
        data = pd.read_excel(INPUT_FILE, sheet_name='Sheet1')
        logger.info(f"Loaded input data shape: {data.shape}")
        
        if 'assistant_response' not in data.columns:
            raise ValueError("Column 'assistant_response' not found in input file")
            
        logger.info("Sample of input data:")
        logger.info(data['assistant_response'].head())

        # Process each row
        processed_data = []
        for idx, row in data.iterrows():
            processed_responses = process_response(row)
            if not processed_responses:
                logger.warning(f"No data processed for row {idx}")
            else:
                logger.info(f"Processed {len(processed_responses)} items from row {idx}")
            processed_data.extend(processed_responses)

        # Check processed data
        logger.info(f"Total processed items: {len(processed_data)}")
        if not processed_data:
            logger.warning("No data was processed successfully!")
            return

        # Convert to DataFrame and save
        processed_df = pd.DataFrame(processed_data)
        logger.info(f"Output DataFrame shape: {processed_df.shape}")
        
        # Save with error handling
        try:
            processed_df.to_excel(OUTPUT_FILE, index=False)
            logger.info(f"Successfully saved to: {OUTPUT_FILE}")
        except PermissionError:
            logger.error("Permission denied when writing output file")
            raise
        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            raise

    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
