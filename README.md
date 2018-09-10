# Connect Video Manager

This repo handles the uploading/modifications of Connect session videos. Running the script will check the passed in directory of videos
against the LinaroOrg YouTube channel and upload / make any neccessary modifications.

## YouTube
Python script checks for new videos in passed in directory and uploads the videos to YouTube. Any titles/descriptions that have changed are also updated based on the pathable export.

## S3 
Script outputs the command needed to snyc the passed in directory of videos with the connect.linaro.org static resources bucket.

## Required Python Libraries

- pip install --upgrade google-api-python-client
- pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2


