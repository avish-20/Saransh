import os
import telebot
import openai
import wget
import pathlib
import pdfplumber
import numpy as np
import nltk

nltk.download('punkt')
import jsonpickle
import PyPDF2
import convertapi
import requests
import pathlib
import urllib.request
from fetch_subtitle_from_yout import fetch
from text_to_speech import speech

#import module from Daisi platform
import pydaisi as pyd

gpt_3_title_extraction_from_text = pyd.Daisi(
    "laiglejm/GPT 3 Title extraction from text")

secret_key = "dzOGx9zbm6P1R9rp"
convertapi.api_secret = secret_key
API_KEY = "5114610602:AAH9Rz3PhTqgqGu8h6GvC8GgzE_gW9SHms0"
bot = telebot.TeleBot(API_KEY)
# speech()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Hi, I am Saransh , a Text-Summarizer Bot. Sometime you have long Paragraph or Pages and you are don't want to read it. So, Use Me. You can send text messages or pdf and I can share Summary of it \n Press /text to start\n"
    )


#TLDR_POSTFIX = "\n tl;dr:"
tldr_tag = "\n tl;dr:"
SUMMARIZE_PREFIX = "Summarize this for a second-grade student:\n\n"
ENGINE = "text-curie-001"
BATCH_SIZE = 500
NUM_TOKENS = 125
# my_secret = os.environ['openapikey']
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY


#function for extract input
def extract_input_text(file_object):
    text = ""
    with pdfplumber.open(file_object) as pdf:
        for page in pdf.pages:
            text = text + page.extract_text() + " "
    return text


def post_processing(response_text):
    try:
        fullstop_index = response_text.rindex('.')
        response_text = response_text[:fullstop_index + 1]
    except Exception as e:
        print(e)
    return response_text.replace('\\n', '')


def showPaperSummary(input_text):
    gpt3_prompt = SUMMARIZE_PREFIX + input_text + tldr_tag
    response = openai.Completion.create(engine=ENGINE,
                                        prompt=gpt3_prompt,
                                        temperature=0,
                                        max_tokens=NUM_TOKENS,
                                        top_p=1.0,
                                        frequency_penalty=1.0,
                                        presence_penalty=1.0)
    batch_summary = response["choices"][0]["text"]

    return post_processing(response_text=batch_summary)


#function for summarization
def summ_batches(input_text):
    sentences = nltk.tokenize.sent_tokenize(input_text)
    tokens = 0
    batch_sentence = ""
    batches = []
    for sentence in sentences:
        tokens = tokens + len(nltk.word_tokenize(sentence))
        if tokens <= BATCH_SIZE:
            batch_sentence = batch_sentence + sentence
        else:
            batches.append(batch_sentence)
            batch_sentence = sentence
            tokens = len(nltk.word_tokenize(sentence))
    if batch_sentence not in batches:
        batches.append(batch_sentence)
    summary = ''
    for batch in batches:
        response = showPaperSummary(batch)
        summary = summary + response
    return summary


#use api title_extraction_from_text from Daisi platform
def get_title(input_text):
    title = gpt_3_title_extraction_from_text.get_title(input_text,
                                                       OPENAI_API_KEY).value
    return title['title']


#function for summarize text
def text_summarize(message):
    a = jsonpickle.encode(message.text)
    title = "Title : "
    title += get_title(a)
    a = summ_batches(a)
    a = a.replace('\n', "")
    speech(a)
    bot.send_message(message.chat.id, title)
    bot.send_message(message.chat.id, a)
    bot.send_audio(message.chat.id, audio=open('output.mp3', 'rb'))

    bot.send_message(message.chat.id, "Press any key for further work\n")


#function for summarize text
def pdf_summarize(message):
    file_id = message.document.file_id
    path = bot.get_file_url(file_id)
    pdf = convertapi.convert('txt', {'File': path})
    #print(pdf.file.url)
    data = urllib.request.urlopen(pdf.file.url)
    a = ""
    for line in data:
        line = str(line)
        a += line
    title = "Title : "
    title += get_title(a)
    a = summ_batches(a)
    a = a.replace('\n', "")
    a = a.replace('\r', "")
    speech(a)
    bot.send_message(message.chat.id, title)
    bot.send_message(message.chat.id, a)
    bot.send_audio(message.chat.id, audio=open('output.mp3', 'rb'))
    bot.send_message(message.chat.id, "Press any key for further work\n")


def get_video_id(videoURL):
    videoID = str(videoURL).split('=')
    videoID = videoID[-1]
    return videoID


#function to summarize the subtitle of youtube
def subtitle_summarize(message):
    a = jsonpickle.encode(message.text)
    a = get_video_id(a)
    a = fetch(a)
    title = "Title : "
    title += get_title(a)
    a = summ_batches(a)
    a = a.replace('\n', "")
    speech(a)
    bot.send_message(message.chat.id, title)
    bot.send_message(message.chat.id, a)
    bot.send_audio(message.chat.id, audio=open('output.mp3', 'rb'))
    bot.send_message(message.chat.id, "Press any key for further work\n")


#    pass


def provide_functionality(message):
    try:
        if (message.text == "1"):
            msg = bot.send_message(message.chat.id,
                                   "Please send the text to summarize.")
            bot.register_next_step_handler(msg, text_summarize)
        elif (message.text == "2"):
            msg = bot.send_message(message.chat.id,
                                   "Please send the pdf to summarize.")
            bot.register_next_step_handler(msg, pdf_summarize)
        elif (message.text == "3"):
            msg = bot.send_message(message.chat.id,
                                   "Please send the link of the youtube.")
            bot.register_next_step_handler(msg, subtitle_summarize)
        elif (message.text == "4"):
            exit(message)
        else:
            msg = bot.send_message(
                message.chat.id,
                "Please select an appropriate option. Thank you!")
            bot.register_next_step_handler(msg, provide_functionality)

    except Exception as e:
        bot.reply_to(message, 'Something went wrong!')


@bot.message_handler(commands=['exit'])
def exit(message):
    bot.send_message(
        message.chat.id,
        "OK, Thank You very much for your patience. Apologies for any kind of trouble you might have faced. It was great talking to you."
    )


@bot.message_handler(content_types=['text'])
def markup_eg(message):
    msg = bot.send_message(
        message.chat.id,
        "Hey there, Following are the functionalities I can provide you.\n Press the number you prefer...\n 1. Summarize the Text \n 2.Summarize the PDF \n 3.Summarize subtitle of the YouTube video \n 4. Exit"
    )
    bot.register_next_step_handler(msg, provide_functionality)


# bot.enable_save_next_step_handlers(delay=1)
# bot.load_next_step_handlers()

bot.polling()
