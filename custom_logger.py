"""Common logger object to maintain logs"""
import logging

class Logger:
    """
    Initalize a logger file with logFileName
    """
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name
        self.log_file_path = 'logs/' + log_file_name

    def get_logger(self):
        """
        Get a logger
        :return: logger object
        """
        # Initialize logger
        logging.basicConfig(filename=self.log_file_path,
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d]'
                                   ' %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=logging.DEBUG)
        return logging.getLogger(self.log_file_name.split('.')[0])
