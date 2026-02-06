import logging
import sys

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('app.log')

# Create formatters and add them to the handlers
console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Set level for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.ERROR)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Set the default logging level
def set_log_level(level):
    logger.setLevel(level)

# Example usage
if __name__ == '__main__':
    logger.info('This is an info message')
    logger.error('This is an error message')
