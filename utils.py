"""This is a DubberStudio"""
#!/usr/bin/python3
import sys
import os
import shutil
import subprocess
import glob
import shlex
import custom_logger

LOGGER = custom_logger.Logger('app.log')
logger = LOGGER.get_logger()

def execute_command(cmd):
    """
    Execute subprocess command
    :param cmd:
    :return:
    """
    try:
        logger.info("Executing: %s", cmd)
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, encoding='utf8')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())
    except KeyboardInterrupt:
        logger.error("Exception occured!", exc_info=True)
        sys.exit("Keyboard Interrupt Termination Initiated")
    except Exception as ex:
        logger.error("Exception occured!", exc_info=True)
        raise Exception from ex

def copy_file_from_src_to_dest(source_path, dest_path):
    logger.info("Copying file from %s to %s", source_path, dest_path)
    CMD_TO_EXECUTE = "cp '{}' '{}'".format(source_path, dest_path)
    execute_command(CMD_TO_EXECUTE)
    logger.info("Copied file successfully")

def extract_hardcoded_subs(video_path):
    CMD_TO_EXECUTE = './do-all.sh video.mp4'.format(video_path)
    execute_command(CMD_TO_EXECUTE)
    logger.info("Extraction completed successfully")
    logger.info("Copying final srt to input dir")
    CMD_TO_EXECUTE = 'cp video.mp4.ocr.srt output/video.srt'
    execute_command(CMD_TO_EXECUTE)
    logger.info("Copied final srt successfully")


def run_cleanup():
    logger.info("Executing cleanup")

    # Path pattern for files and directories starting with "video."
    video_pattern = "video.*"

    # Remove files and directories matching the pattern
    for item in glob.glob(video_pattern):
        try:
            if os.path.isfile(item):
                os.remove(item)
                logger.info("Deleted file: %s", item)
            elif os.path.isdir(item):
                shutil.rmtree(item)  # Remove the directory and its contents
                logger.info("Deleted directory: %s", item)
        except Exception as e:
            logger.error("Failed to delete %s: %s", item, e)

    # Removing JSON files
    json_files = glob.glob("*.json")
    for json_file in json_files:
        try:
            os.remove(json_file)
            logger.info("Deleted JSON file: %s", json_file)
        except Exception as e:
            logger.error("Failed to delete JSON file %s: %s", json_file, e)

    logger.info("Cleaned up successfully")
