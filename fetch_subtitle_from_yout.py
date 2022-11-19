from youtube_transcript_api import YouTubeTranscriptApi


def fetch(code):
    srt = YouTubeTranscriptApi.get_transcript(code)
    text = ""
    for i in srt:
        text += i["text"] + " "
    return text
