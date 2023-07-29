# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ft_onPttgpy1Coc3CHM6so_f5FZqLEmy
"""

from google.colab import drive
mount_path = "/content/drive/"
drive.mount(mount_path)

import tensorflow as tf
from tensorflow.keras.layers import TextVectorization
import pandas as pd
import numpy as np

dataset_path = f"{mount_path}MyDrive/data/comment_data/train.csv/train.csv"

df = pd.read_csv(dataset_path)

X = df['comment_text']
y = df[df.columns[2:]].values
MAX_FEATURES = 200000
vectorizer = TextVectorization(max_tokens = MAX_FEATURES, output_sequence_length = 1800, output_mode = 'int')
vectorizer.adapt(X.values)

model = tf.keras.models.load_model(f"{mount_path}MyDrive/data/toxicity.h5")

API_KEY = 'API_KEY'
import soundfile as sf
import requests
import time
from pytube import YouTube

upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcribe_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization': API_KEY}


# Upload

def upload(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    response = requests.post(upload_endpoint,
                            headers=headers,
                            data=read_file(filename))

    audio_url = response.json()['upload_url']
    return audio_url

# Trasncribe
def transcribe(audio_url):
    json = { "audio_url": audio_url }
    response = requests.post(transcribe_endpoint, json=json, headers=headers)
    job_id = response.json()['id']
    return job_id

# Poll

def poll(transcript_id):
    polling_endpoint = f"{transcribe_endpoint}/{transcript_id}"
    polling_response = requests.get(polling_endpoint,headers=headers)
    return polling_response.json()

def get_transcript_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = poll(transcript_id)
        if data['status']=='completed':
            return data, None
        elif data['status']=='error':
            return data, data['error']
        time.sleep(30)

# Get transcript

def get_transcript(audio_url):
    data, error = get_transcript_result_url(audio_url)
    return data['text']

def Download(video_url):
    data = YouTube(video_url)
    videos = data.streams.filter(only_audio=True)
    videos[0].download(filename="sample.mp3")
    audio_url = upload('sample.mp3')
    text = get_transcript(audio_url)
    return score_text(text)


def audio_input(audio):
  sr, data = audio
  sf.write("temp.wav", data, 44100)
  audio_url = upload("temp.wav")
  text = get_transcript(audio_url)
  return score_text(text)

def audio(audio):
  sr, data = audio
  sf.write("temp.wav", data, 44100)
  audio_url = upload("temp.wav")
  text = get_transcript(audio_url)
  return score_text(text)


def score_text(text):
  vectorized_text = vectorizer(text)
  result = model.predict(np.expand_dims(vectorized_text,0))
  text = ""
  for id, col in enumerate(df.columns[2:]):
    text+="{}: {}\n".format(col,result[0][id]>0.5)
  return text





import gradio as gr

interface1 = gr.Interface(fn= score_text, inputs = "text", outputs = "text")
interface2 = gr.Interface(fn = audio_input, inputs = gr.Audio(), outputs = "text")
interface3 = gr.Interface(fn = Download, inputs = "text", outputs = "text")
interface4 = gr.Interface(fn = audio, inputs = gr.Audio(source="microphone"), outputs = "text")
demo = gr.TabbedInterface([interface1, interface2, interface3, interface4],['text',"audio","youtube","microphone"])

demo.launch()

