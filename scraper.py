import yaml
import argparse
import os
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube


def get_args():
    parser = argparse.ArgumentParser("Youtube Video Scraper")
    parser.add_argument("--query", type=str,
                        default="", help="Query")
    parser.add_argument("--credentials_file", type=str,
                        default="credentials.yaml", help="Path to the credentials file.")
    parser.add_argument("--dest_folder", type=str,
                        default="videos/", help="Path to the output folder.")
    parser.add_argument("--max_results", type=int,
                        default=2, help="Maximum number of results.")
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
    yt = YouTube(video_url)
    yt = yt.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first()
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    yt.download(dest_folder)


if __name__ == '__main__':
    args = get_args()
    api_key = get_creds(args)
    video_ids = get_video_listings(api_key, args)
    video_urls = [form_youtube_url(video_id) for video_id in video_ids]
    for video_url in tqdm(video_urls):
        download_video(video_url, args)
