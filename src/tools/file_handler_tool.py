# file_handler_tool.py

import os
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

def create_file_handler_tool():
    """
    Creates a basic, sandboxed tool for reading the content of local files,
    typically used to retrieve the HTML/JS content of generated plots.
    """
    logger.info("Initializing File Handler Tool.")

    @tool
    def read_file_content(file_path: str) -> str:
        """
        Reads the content of a local file (e.g., an HTML chart file) specified by the absolute path.
        
        Input MUST be the full, absolute path to the file.
        Returns the entire content of the file as a single string.
        """
        try:
            # We use 'r' for reading and ensure 'utf-8' encoding for HTML content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"File content successfully read from: {file_path}")
            
            # Simple content check before returning massive string
            # if len(content) < 50:
            #     logger.warning(f"File {file_path} content is unusually small ({len(content)} chars).")
            
            return content
        
        except FileNotFoundError:
            logger.error(f"File not found at path: {file_path}")
            return f"Error: File not found at path {file_path}. Ensure the path is absolute."
        except OSError as e:
            logger.error(f"OS error during file read: {e}")
            return f"Error: Cannot access file at path {file_path}. Permission denied or path invalid."
        except Exception as e:
            logger.error(f"Unexpected error reading file: {e}")
            return f"Error reading file content: {str(e)}"

    return read_file_content


# --- DEBUGGING BLOCK ---
if __name__ == "__main__":
    import shutil
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # MOCK SETUP: Create a temporary file and directory for testing
    TEST_DIR = Path("./temp_handler_test")
    TEST_DIR.mkdir(exist_ok=True)
    TEST_FILE_PATH = TEST_DIR / "temp_chart.html"
    MOCK_HTML_CONTENT = "<html><body><h1>Mock Chart Content</h1></body></html>"
    
    try:
        # Write mock content
        with open(TEST_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(MOCK_HTML_CONTENT)
            
        handler_tool = create_file_handler_tool()
        
        print("\n--- Running File Handler Debug Test ---")
        
        # Test 1: Successful read (requires absolute path)
        absolute_path = str(TEST_FILE_PATH.resolve())
        print(f"Testing absolute path: {absolute_path}")
        result_success = handler_tool.invoke(absolute_path)
        print(f"\nResult 1 (Success - Content): {result_success[:50]}...")
        
        # Test 2: File Not Found
        result_failure = handler_tool.invoke("/path/to/nonexistent/file.html")
        print(f"\nResult 2 (Failure - Error Message): {result_failure}")
        
    except Exception as e:
        logger.error(f"Test setup failed: {e}")
        
    # finally:
    #     # Clean up the temporary file and directory
    #     if TEST_DIR.exists():
    #         shutil.rmtree(TEST_DIR)
    #         logger.info(f"Cleaned up temporary directory: {TEST_DIR}")