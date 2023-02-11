import yaml
import argparse
import os
import json
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
from pytube.cli import on_progress
from youtube_transcript_api import YouTubeTranscriptApi


def get_args():
    parser = argparse.ArgumentParser("Youtube Video Scraper")
    parser.add_argument("--query", type=str,
                        default="", help="Search query.")
    parser.add_argument("--credentials_file", type=str,
                        default="credentials.yaml", help="Path to the credentials file.")
    parser.add_argument("--dest_folder", type=str,
                        default="videos/", help="Path to the output folder.")
    parser.add_argument("--max_results", type=int,
                        default=2, help="Maximum number of results.")
    parser.add_argument("--download_captions", type=bool,
                        default=True, help="Download captions, if any, for the videos.")
    args = parser.parse_args()
    return args


def get_creds(args):
    with open(args.credentials_file, "r") as file:
        creds = yaml.safe_load(file)

    api_key = creds["api_key"]
    return api_key


def get_video_listings(api_key, args):
    try:
        query = args.query
        max_results = args.max_results
        youtube = build('youtube', 'v3', developerKey=api_key)

        search_response = youtube.search().list(
            part='snippet',
            type='video',
            q=query,
            maxResults=max_results
        ).execute()

        print(yaml.dump(search_response["items"]))
        video_ids = list(
            map(lambda x: x["id"]["videoId"], search_response["items"])
        )
        return video_ids

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return []


def form_youtube_url(video_id):
    return "http://youtu.be/" + video_id


def download_video(video_url, args):
    dest_folder = args.dest_folder
    yt = YouTube(video_url, on_progress_callback=on_progress)
    yt = yt.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first()
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    yt.download(dest_folder)

def download_captions(video_id, args): 
    dest_folder = args.dest_folder
    srt = YouTubeTranscriptApi.get_transcript(video_id)
    with open(f'{dest_folder}/{video_id}.json', 'w') as fp:
        json.dump(srt, fp)

if __name__ == '__main__':
    args = get_args()
    api_key = get_creds(args)
    video_ids = get_video_listings(api_key, args)
    video_urls = [form_youtube_url(video_id) for video_id in video_ids]
    for index, video_url in enumerate(tqdm(video_urls)):
        download_video(video_url, args)
        download_captions(video_ids[index], args)