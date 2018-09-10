#!/usr/bin/python3

try:
    import httplib
except ImportError:  # python3 compatibility
    from http import client
    httplib = client

import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import file
from oauth2client import tools

class cmd_flags(object):
    """
        Used to provide command-line level authentication rather than
        working through a web browser.
    """
    def __init__(self):
        self.auth_host_name = 'localhost'
        self.auth_host_port = [8080, 8090]
        self.logging_level = 'ERROR'
        self.noauth_local_webserver = True

class YouTubeVideoManager:
    """ 
        This class interacts with Google's YouTube Data API
    """

    def __init__(self):

        # Explicitly tell the underlying HTTP transport library not to retry, since
        # we are handling retry logic ourselves.
        httplib2.RETRIES = 1

        # Always retry when these exceptions are raised.
        self.RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
        httplib.IncompleteRead, httplib.ImproperConnectionState,
        httplib.CannotSendRequest, httplib.CannotSendHeader,
        httplib.ResponseNotReady, httplib.BadStatusLine)

        # Always retry when an apiclient.errors.HttpError with one of these status
        # codes is raised.
        self.RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


        # Maximum number of times to retry before giving up.
        self.MAX_RETRIES = 10

        # The clients secrets file to use when authenticating our requests to the YouTube Data API
        self.CLIENT_SECRETS_FILE = 'client_secret_384596001461-09jpm4o0m6ghp4sd2v6nu9l3s1u7ll2f.apps.googleusercontent.com.json'
       
        # This variable defines a message to display if the CLIENT_SECRETS_FILE is
        # missing.
        self.MISSING_CLIENT_SECRETS_MESSAGE = ""
        # WARNING: Please configure OAuth 2.0
        # To make this sample run you will need to populate the client_secrets.json file
        # found at:
        # %s
        # with information from the {{ Cloud Console }}
        # {{ https://cloud.google.com/console }}
        # For more information about the client_secrets.json file format, please visit:
        # https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
        # """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
        #                                 self.CLIENT_SECRETS_FILE))

        # This OAuth 2.0 access scope allows an application to upload files to the
        # authenticated user's YouTube channel, but doesn't allow other types of access.
        self.YOUTUBE_UPLOAD_SCOPE = ['https://www.googleapis.com/auth/youtube']

        # Name of the API service
        self.YOUTUBE_API_SERVICE_NAME = 'youtube'

        # Version of the YouTube API
        self.YOUTUBE_API_VERSION = 'v3'

        # Privacy statuses we can use to set on YouTube videos
        self.VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')


        # The ID of the playlist for the current Connect
        # In the future this playlist ID should be retrieved dynamically based on the 
        # connect code
        self.playlist_id = "PLKZSArYQptsMGIqYAJhCfyDvcUXCBna9u"

        # Get the authenticated service to use in requests to the API
        self.service = self.get_authenticated_service()


    # Authorize the request and store authorization credentials.
    def get_authenticated_service(self):
        """ 
            Gets an authenticated service object for requests to the 
            YouTube Data API
        """

        store = file.Storage("youtube_video_manager-oauth2.json")

        creds = store.get()

        if creds is None or creds.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRETS_FILE,
                scope=self.YOUTUBE_UPLOAD_SCOPE,
                message=self.MISSING_CLIENT_SECRETS_MESSAGE)
            creds = tools.run_flow(flow, store, cmd_flags())
            

        return build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION,
                        http=creds.authorize(httplib2.Http()))


    def get_video_id_based_on_session_id(self, session_id):
        """
            Retrieve a video id of a YouTube video based on a session_id
        """
        current_videos = self.get_current_youtube_videos_based_on_string(session_id)
        if len(current_videos) == 1:
            return current_videos[0][1]
        else:
            return False

    def update_video_status(self, video_id, status):
        """
            This method updates the status of a video based on the video_id and status provided.
        """
        # Call the API's videos.list method to retrieve the video resource.
        # Get the current video details
        videos_list_response = self.service.videos().list(
            id=video_id,
            part='status'
        ).execute()

        # If the response does not contain an array of 'items' then the video was
        # not found.
        if not videos_list_response['items']:
            return False

        # Since the request specified a video ID, the response only contains one
        # video resource. This code extracts the snippet from that resource.
        video_list_status = videos_list_response['items'][0]['status']
        print(video_list_status)
        input()

        # Set the privacy status of the video
        if status:
            video_list_status['privacyStatus'] = status

        # Update the video resource by calling the videos.update() method.
        videos_update_response = self.service.videos().update(
            part='status',
            body=dict(
            status=video_list_status,
            id=video_id
            )).execute()

        return True


    def get_current_youtube_videos_based_on_string(self, string):
        """
            Gets the current videos on YouTube that contain the specified string in
            in the title or description
        """
        channels_response = self.service.channels().list(
            mine=True,
            part="contentDetails"
            ).execute()


        for channel in channels_response["items"]:
            # From the API response, extract the playlist ID that identifies the list
            # of videos uploaded to the authenticated user's channel.
            playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
            # print("ID: {0}".format(playlist_id))

            # print("Videos in list %s" % playlist_id)

            # Retrieve the list of videos uploaded to the authenticated user's channel.
            playlistitems_list_request = self.service.playlistItems().list(
                playlistId=playlist_id,
                part="snippet",
                maxResults=50
            )

            videos = []
            while playlistitems_list_request:
                playlistitems_list_response = playlistitems_list_request.execute()

                # Print information about each video.
                for playlist_item in playlistitems_list_response["items"]:
                    title = playlist_item["snippet"]["title"]
                    video_id = playlist_item["snippet"]["resourceId"]["videoId"]
                    if string.lower() in title:
                        print("%s (%s)" % (title, video_id))
                        videos.append([title,video_id])

                playlistitems_list_request = self.service.playlistItems().list_next(
                playlistitems_list_request, playlistitems_list_response)
                
            if len(videos) > 0:
                return videos
            else:
                return False

    def upload_video(self, options):
        """
            Takes a dictionary of all video details e.g
            {
                "file":"/home/kyle.kirkby/Documents/Marketing/Connect/YVR18/videos/yvr18-100k.mp4",
                "title": "YVR18-100k: Opening Keynote by George Grey",
                "description": "The Opening Keynote by George Grey at Linaro Connect Vancouver 2018",
                "keywords": "Keynote,yvr18,Open Source,Arm, Vancouver",
                "category": "28",
                "privacyStatus": "private"
            }
        """
        request  = self.get_upload_request(options)
        # Output Details while uploading
        self.resumable_upload(request, options["title"])

    def get_upload_request(self, options):
        """
            Create the request to initialize the upload of a video.
            Takes a service and a dictionary containing the various options
        """

        # Get the Youtube Tags from the keywords
        tags = None
        try:
            if options["keywords"]:
                tags = options["keywords"].split(',')
        except AttributeError:
            tags = [options["keywords"]]



        # Create the body of the request
        body=dict(
            snippet=dict(
                title=options["title"],
                description=options["description"],
                tags=tags,
                categoryId=28
            ),
            status=dict(
                privacyStatus=options["privacyStatus"]
            )
        )

        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.service.videos().insert(
        part=','.join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting 'chunksize' equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options["file"], chunksize=-1, resumable=True)
        )

        return insert_request

    def resumable_upload(self, request, title):
        """
            Creates a resumable upload
        """
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print("Uploading {0} file...".format(title))
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print("Video id '%s' was successfully uploaded." % response['id'])
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                            e.content)
                else:
                    raise
            except self.RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                print(error)
                retry += 1
                if retry > self.MAX_RETRIES:
                    exit("No longer attempting to retry.")

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print("Sleeping %f seconds and then retrying..." % sleep_seconds)
                time.sleep(sleep_seconds)

if __name__ == "__main__":
    video_manager = YouTubeVideoManager()
    # current_videos_on_youtube = video_manager.get_current_youtube_videos_based_on_string("yvr18")
    # print(current_videos_on_youtube)

    # video_manager.upload_video({
    #         "file":"/home/kyle.kirkby/Documents/Marketing/Connect/YVR18/videos/yvr18-100k.mp4",
    #         "title": "YVR18-100k: Opening Keynote by George Grey",
    #         "description": "The Opening Keynote by George Grey at Linaro Connect Vancouver 2018",
    #         "keywords": "Keynote,yvr18,Open Source,Arm, Vancouver",
    #         "category": "28",
    #         "privacyStatus": "private"
    #     })
    # updated = video_manager.update_video_status("cDgI_ov_w5Q", "unlisted")
    updated = video_manager.get_video_id_based_on_session_id("yvr18-100k")
    print(updated)