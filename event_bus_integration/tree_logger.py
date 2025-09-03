"""
2025-09-03 
original version with complete git history, comments, etc. in karl-1 branch (unpublished) of talking-treebot
"""

import logging
import logging.config
import json
import time
from datetime import datetime
import functools
from typing import Optional, Callable


#MARK: setup_logging
def setup_logging(
    config_file: Optional[str] = "tree_logger_config.json", 
    config_dict: Optional[dict] = None, 
    logger_name="root", 
    log_per_session=True):
    """
    Tries to create a logger from config file (json) or dict
    
    Default: combine logs per session
    Optional: dump it all in one big file
    """
    # Priority: config_dict > config_file > fallback
    try:
        import os
        os.makedirs("logs", exist_ok=True)
    except Exception as e:
        print(f"Failed to find or set up logs directory ({e})")

    # try config_dict first
    if config_dict:
        try:
            logging.config.dictConfig(config_dict)
            print(f"Success: Loaded config from dict.")  # Debug
            return logging.getLogger(logger_name)
        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Could not load config from dict ({e}). Trying config file.")

    # then config_file
    if config_file:
        try:
            with open(config_file) as conf:
                config = json.load(conf)
            if log_per_session and "handlers" in config and "file" in config["handlers"]:
                session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_filename = f"logs/treebot_{session_time}.log"
                config["handlers"]["file"]["filename"] = log_filename
            logging.config.dictConfig(config)
            print(f"Success: Loaded config from {config_file}")  # Debug
            return logging.getLogger(logger_name)
        except (FileNotFoundError, ValueError, ImportError, KeyError) as e:
            print(f"Warning: Could not load config from file ({e}). Using fallback.")

    # if all fails, fallback to simple console logger
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - (line: %(lineno)d) [%(filename)s] [FALLBACK]",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        print(f"Fallback config for logger: {logger.name}")
    return logger



#MARK: TreeLogger
class TreeLogger():
    """
    Encapsulates logging functionality and config for treebot. Previously known as performance_logger
    
    Optionally pass in own config_file (json), or config_dict. Remember to include logger_name!
    
    Current version automatically sets up logging and includes time_function method.
    
    Todo: 
        - ensure that only either a file or a dict can be included? (currently handled via priority: dict>file)
        - add more special logging methods? -> http requests, etc. 
    
    """

    def __init__(self, 
                 logger_name: str = "treelogger", # from tree_logger_config.json
                 enable_console_output: bool = True,
                 config_file: Optional[str] = "tree_logger_config.json",
                 config_dict: Optional[dict] = None):
        self.logger = logging.getLogger(logger_name)
        self.enable_console_output = enable_console_output
        #self._setup_logging(config_file, config_dict)
        # removed this, as it just messed with things! 

    def time_function(self, func_or_custom = None, category: str = "GENERAL"):
        """
        Decorator to log function execution time
        
        Usage:
            @time_function  # now also supported!
            @time_function()
            @time_function("custom_name")
            @time_function("custom_name", "category")
        """
        # now able to work without parantheses (I forgot them too many times)
        if callable(func_or_custom):
            func = func_or_custom
            return self._create_wrapper(func, None, "GENERAL")
        
        # when used properly
        def decorator(func):
            return self._create_wrapper(func, func_or_custom, category)
        return decorator
    
    def _create_wrapper(self, func: Callable, custom_name: Optional[str], category: str):
        """(private) the actual wrapper"""
        # basically exists to make time_function's ability to handle no parantheses code cleaner
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = custom_name or func.__name__
            
            start_time = time.perf_counter() # start measuring
            
            try:                
                result = func(*args, **kwargs)  # actually runs the function to be timed
                end_time = time.perf_counter()
                execution_time = end_time - start_time 
                
                # log the result
                self.logger.info(
                    f"TIMING [{category}] {name}: {execution_time:.3f}s",
                    extra = {
                        "function_name": name,
                        "category": category,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                
                # also log to console 
                # might have to remove this, to avoid duplicate logs to console, as my config.json might include it
                #MARK: remove this? 
                if self.enable_console_output:
                    print(f"{name}() took {execution_time:.3f} seconds")
                
                return result
                
            except Exception as e:
                # if function call failed, log that it, too 
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                
                self.logger.error(
                    f"TIMING [{category}] {name}: {execution_time:.3f}s - FAILED: {str(e)}",
                    extra={
                        "function_name": name,
                        "category": category,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    }
                )
                
                # same thing as in try
                #MARK: remove this?
                if self.enable_console_output:
                    print(f"{name}() took {execution_time:.3f} seconds - FAILED")
                
                # send the exception up
                raise 
                
        return wrapper




# #MARK: simple_time_function
# # not part of class, able to be imported on its own
# # should work standalone
# def simple_time_function(func):
#     """
#     Simple alternative to fancy time_function, prints result to console (and logs)
    
#     ```
#     @simple_time_function
#     def some_function(): ...
#     ```
#     """
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.perf_counter()
        
#         # actually executes the wrapped function
#         result = func(*args, **kwargs)
        
#         end_time = time.perf_counter()
#         total_time = round(end_time - start_time, 3)
#         print(f"{func.__name__}() took {total_time} seconds")
        
#         # using custom logger (why does it suddenly work?)
#         logger.info(f"{func.__name__}() took {total_time} seconds")
        
#         return result
#     return wrapper


#=============================================================================================



# #MARK: Testing
# # some copilot-generated testing stuff


# # Global instance for convenience
# _default_logger = TreeLogger(logger_name="treelogger") # treelogger in config

# # Convenience functions that use the default instance
# def time_function(func_or_name=None, category: str = "GENERAL"):
#     """Convenience function using default logger"""
#     return _default_logger.time_function(func_or_name, category)

# def simple_time_function(func: Callable) -> Callable:
#     """Simple timing decorator with minimal setup"""
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.perf_counter()
#         result = func(*args, **kwargs)
#         end_time = time.perf_counter()
#         execution_time = end_time - start_time
        
#         print(f"{func.__name__}() took {execution_time:.3f} seconds")
#         return result
#     return wrapper

# def configure_performance_logging(logger_name: str = "treelogger",
#                                 enable_console_output: bool = True,
#                                 config_file: Optional[str] = None,
#                                 config_dict: Optional[dict] = None) -> TreeLogger:
#     """Configure and return a new performance logger instance"""
#     return TreeLogger(logger_name, enable_console_output, config_file, config_dict)

# # For backward compatibility, try to load config if it exists
# try:
#     config_path = pathlib.Path("tree_logger_config.json")
#     if config_path.exists():
#         _default_logger = TreeLogger(config_file=str(config_path))
# except Exception:
#     pass  # Use default setup if config loading fails

# def main() -> None:
#     """Test the performance logging functionality"""
    
#     # Create logs directory if it doesn't exist
#     import os
#     os.makedirs("logs", exist_ok=True)
#     # Test custom inline config
#     inline_config = {
#         "version": 1,
#         "disable_existing_loggers": False,
#         "formatters": {
#             "custom_format": {
#                 "format": "[CUSTOM] %(asctime)s - %(levelname)s - %(message)s",
#                 "datefmt": "%H:%M:%S"
#             }
#         },
#         "handlers": {
#             "console": {
#                 "class": "logging.StreamHandler",
#                 "level": "INFO",
#                 "formatter": "custom_format"
#             },
#             "file": {
#                 "class": "logging.FileHandler",  # Use simple FileHandler first
#                 "level": "DEBUG",
#                 "formatter": "custom_format",
#                 "filename": "logs/inline_config_test.log"
#             }            
#         },
#         "loggers": {
#             "custom": {
#                 "level": "INFO",
#                 "handlers": ["console", "file"],
#                 "propagate": False
#             }
#         }
#     }
    
#     # Test custom logger with inline config - NOW PASSING config_dict!
#     custom_logger = configure_performance_logging(
#         logger_name="custom", 
#         enable_console_output=False,
#         config_dict=inline_config  # This was missing!
#     )
    
#     @custom_logger.time_function("inline_config_test", "CUSTOM")
#     def test_inline_config(a, b):
#         time.sleep(0.1)
#         return a * b
    
#     # ... existing test functions ...
    
#     print("Testing performance logging...")
    
#     # Run tests including the new inline config test
#     # ... existing test calls ...
 
    
#     # Test simple decorator
#     @simple_time_function
#     def test_simple(a, b):
#         time.sleep(0.1)
#         return a + b
    
#     # Test advanced decorator - all variations
#     @time_function
#     def test_no_params(a, b):
#         time.sleep(0.1)
#         return a * b
        
#     @time_function()
#     def test_empty_params(a, b):
#         time.sleep(0.1)
#         return a * b
    
#     @time_function("custom_name")
#     def test_custom_name(a, b):
#         time.sleep(0.1)
#         return a * b
        
#     @time_function("api_call", "API")
#     def test_full_params(a, b):
#         time.sleep(0.1)
#         return a * b
    
#     print("Testing performance logging...")
    
#     # Run tests
#     print(f"Simple: {test_simple(1, 2)}")
#     print(f"No params: {test_no_params(3, 4)}")
#     print(f"Empty params: {test_empty_params(5, 6)}")
#     print(f"Custom name: {test_custom_name(7, 8)}")
#     print(f"Full params: {test_full_params(9, 10)}")

#     # Run inline config with file writing
#     print(f"Inline config: {test_inline_config(13, 14)}")
    
#     # Check if file was created
#     if os.path.exists("logs/inline_config_test.log"):
#         print("✅ Log file created successfully!")
#         with open("logs/inline_config_test.log", "r") as f:
#             content = f.read()
#             print(f"Log file content:\n{content}")
#     else:
#         print("❌ Log file was not created")
#         # Debug: check what loggers exist
#         print("Debug: Available loggers:")
#         for name in logging.Logger.manager.loggerDict:
#             logger_obj = logging.getLogger(name)
#             print(f"  {name}: {len(logger_obj.handlers)} handlers")
#             for handler in logger_obj.handlers:
#                 print(f"    - {type(handler).__name__}: {getattr(handler, 'baseFilename', 'no file')}")

# if __name__ == "__main__":
#     main()

