import xml.etree.ElementTree
from urllib import request
import json
import frontmatter
import sys
import os
import shutil
from io import BytesIO
import glob
import csv
from PyPDF2 import PdfFileReader
import re 
import argparse
from urllib.parse import urlparse
import subprocess

from youtube_video_manager import YouTubeVideoManager

class TermColours:
    """
        Class which holds the Term Colours for outputting pretty text
    """

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKCYAN = '\033[36m'
    WARNING = '\033[93m'
    LIGHT_GREY = '\033[37m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ConnectVideoManager:
    """
        This class handles the syncing of Connect videos with YouTube (LinaroOrg) and AWS S3 Static resources bucket
    """

    def __init__(self):

        # Instantiate a new ArgumentParser Object
        self.parser = argparse.ArgumentParser(description="Connect Video Manager")
        # Setup the argument parser
        self.setup_parser()
        # Get the args
        self.args = self.parser.parse_args()
        
        # Check to see if script is executing as verbose
        if self.args.verbose:
            self._verbose = True
        else:
            self._verbose = False
        
        # Get passed in params
        self.connect_code = self.args.connect_code.lower()
        self.video_directory = self.args.video_directory

        if self._verbose:
            print(self.output_ok_cyan("ConnectVideoManager is now executing..."))

        # Instantiate a new video manager object
        self.video_manager = YouTubeVideoManager()

        # Get current videos contain YVR18 from YouTube
        self.main()



    def setup_parser(self):
        """
            Method which sets up the argument parser
        """

        # Required Positional Arguments
        required_arguments_group = self.parser.add_argument_group('Required Arguments')
        required_arguments_group.add_argument(
            "video_directory", help="The path to the directory the Connect videos are stored in.")
        required_arguments_group.add_argument(
            "connect_code", help="The short code for the current connect e.g. YVR18")

        # Flags
        flag_arguments_group = self.parser.add_argument_group('Flags')
        flag_arguments_group.add_argument(
            "-V", "--verbose", action="store_true", help="Verbose output of the script")

    def main(self):
        """
            Main method for syncing videos with S3 and YouTube
        """

        # Get Current videos on youtube
        current_videos_on_youtube = self.video_manager.get_current_youtube_videos_based_on_string(self.connect_code)

        if self._verbose:
            print(self.output_ok_cyan("Looking for videos in {0}".format(self.video_directory)))

        # Get videos in directory
        videos_in_directory = self.get_videos_from_directory(self.video_directory)
    
        print(videos_in_directory)

        # Run S3 Command to sync videos to private folder
        synced_with_s3 = self.sync_with_s3(self.video_directory)

        # Sync vidoes with YouTube
        synced_with_youtube = self.sync_with_youtube(current_videos_on_youtube, videos_in_directory)


        if self._verbose:
            print(self.output_ok_blue("{0} video(s) found.".format(len(videos_in_directory))))

        # Sync list of current videos on YouTube with those in directory
        # sync_with_youtube = self.sync_with_youtube(current_videos_on_youtube, videos_in_directory)

    
    def get_videos_from_directory(self, directory):
        """
            Takes a directory as input and returns a list of the video files found
        """
        types = [".mp4"]
        
        # Loop through and find all markdown files
        videos = []
        # For each type in types
        for type in types:
            # For each file in directory find matched files
            for video_file in glob.iglob('{0}/**/*{1}'.format(directory,type), recursive=True):
                videos.append(video_file)
        return videos

    def sync_with_youtube(self, current_videos_on_youtube, videos_in_directory):
        """
            Upload videos to youtube that are not currently uploaded.
        """
        if current_videos_on_youtube != False:
            print(current_videos_on_youtube)
            # For each video in Directory
            for video in videos_in_directory:
                # Check if the video is currently on YouTube
                video_session_id = self.get_session_id_from_video(video)
                if self._verbose:
                    print(self.output_ok_blue("Checking if the {0} video is on YouTube...".format(video_session_id)))
                for current_video in current_videos_on_youtube:
                    if current_video[0] == video_session_id.lower():
                        if self._verbose:
                            print(self.warning("Video for {0} already on the LinaroOrg YouTube...".format(video_session_id)))
                        pass
                    else:
                        if self._verbose:
                            print(self.warning("Uploading {0} to the LinaroOrg YouTube...".format(video_session_id)))
                        video_upload_request = {
                            "file":video,
                            "title": video_session_id,
                            "description": video_session_id,
                            "keywords": video_session_id,
                            "category": "28",
                            "privacyStatus": "private"
                        }
                        self.video_manager.upload_video(video_upload_request)
        else:
            # Upload the videos supplied
            for video in videos_in_directory:
                video_session_id = self.get_session_id_from_video(video)
                if self._verbose:
                        print(self.warning("Uploading {0} to YouTube...".format(video)))
                # Craft the Request Dictionary
                video_upload_request = {
                        "file":video,
                        "title": video_session_id,
                        "description": video_session_id,
                        "keywords": video_session_id,
                        "category": "28",
                        "privacyStatus": "private"
                    }
                self.video_manager.upload_video(video_upload_request)
        



    def get_session_id_from_video(self, video):
        """
            Extract the session id from a path to a video
        """
        video_file  = video.split("/")[-1]
        video_session_id = video_file.rsplit(".mp4")
        return video_session_id[0]

    def sync_with_s3(self, video_directory):
        """
            Sync videos with the S3 private folder
        """
        print(self.output_lg("$ aws s3 --profile ConnectAutomation sync {0} s3://connect.linaro.org/private/yvr18/".format(video_directory)))

    def output_lg(self, message):
        return(TermColours.LIGHT_GREY + message + TermColours.ENDC)

    def output_fail(self, message):
        return(TermColours.FAIL + message + TermColours.ENDC)

    def output_ok_green(self, message):
        return(TermColours.OKGREEN + message + TermColours.ENDC)

    def output_ok_blue(self, message):
        return(TermColours.OKBLUE + message + TermColours.ENDC)

    def output_ok_cyan(self, message):
        return(TermColours.OKCYAN + message + TermColours.ENDC)

    def success(self, message):
        return(TermColours.OKGREEN + "SUCCESS: " + message + TermColours.ENDC)

    def warning(self, message):
        return(TermColours.OKCYAN + "WARNING: " + message + TermColours.ENDC)

    def failed(self, message):
        return(TermColours.FAIL + "FAILED: " + message + TermColours.ENDC)

    def status(self, message):
        return(TermColours.OKCYAN + "STATUS: " + message + TermColours.ENDC)


# Check to see if script is being executed as opposed to being imported
if __name__ == "__main__":
    video_manager = ConnectVideoManager()