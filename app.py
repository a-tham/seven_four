from flask import Flask, jsonify, render_template, request, redirect
import pandas as pd
import numpy as np
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras import regularizers
from tensorflow.keras.preprocessing.image import load_img, img_to_array, array_to_img, ImageDataGenerator
from tensorflow.keras.layers import Dense, Flatten, Dropout, Conv1D, MaxPooling1D, BatchNormalization
from tensorflow.keras.layers import ELU
from tensorflow.keras.activations import elu
from tensorflow.keras import models
from tensorflow.keras import layers
from tensorflow.python.keras import backend as k
from pydub import AudioSegment
from skimage import io, data
import io as fileio
import librosa
from librosa import display
import requests
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import spotipy
import seaborn as sns
import matplotlib as mpl
import base64
mpl.use('agg')
from six.moves.urllib.request import urlopen
import os
import urllib
from jinja2 import Environment


# Don't delete
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
env = Environment(cache_size=0)

#To make sure we have always the same matplotlib settings
#(the ones in comments are the ipython notebook settings)

mpl.rcParams['figure.figsize']=(12.0,4.0)    #(6.0,4.0)
mpl.rcParams['font.size']=10                #10
mpl.rcParams['savefig.dpi']=72             #72
mpl.rcParams['figure.subplot.bottom']=.125    #.125

cnn_model = keras.models.load_model('cnn_model.h5')
print(cnn_model.summary())

# get Spotify token
def get_spotify_service():

    cid = ""
    secret = ""
    redirectURI = "http://localhost:8888/callback/"
    username = ""
    scope = 'user-library-read, playlist-read-private, user-library-read, user-read-currently-playing'

    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    scope = 'user-library-read playlist-read-private, user-library-read, user-read-currently-playing'
    service = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    return service

# Search artist and get URI
def search_artist(artist):
    cid = ""
    secret = ""
    username = ""
    redirectURI = "http://localhost:8888/callback/"

    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    scope = 'user-library-read playlist-read-private, user-library-read, user-read-currently-playing'
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    artist = str(artist)

    artist_id = sp.search(q='artist:' + artist, type='artist')
    artist_uri = artist_id['artists']['items'][0]['external_urls']['spotify'].split("/")[-1]

    return artist_uri


# Get album list via artist URI
def get_album_list(artist_uri):
    cid = ""
    secret = ""
    username = ""
    redirectURI = "http://localhost:8888/callback/"

    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    scope = 'user-library-read playlist-read-private, user-library-read, user-read-currently-playing'
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    artist_albums = sp.artist_albums(artist_uri, album_type='album')
    album_count = len(artist_albums['items'])
    album_list_urls = []
    album_list_title = []

    for i in range(album_count):
        album_list_urls.append(artist_albums['items'][i]['external_urls']['spotify'])
        album_list_title.append(artist_albums['items'][i]['name'])

    return album_list_title, album_list_urls

# Get tracks of album via album URI
def album_tracks(album_uri):
    cid = ""
    secret = ""
    username = ""
    redirectURI = "http://localhost:8888/callback/"

    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    scope = 'user-library-read playlist-read-private, user-library-read, user-read-currently-playing'
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    track_title = []
    track_url = []

    album_tracks = sp.album_tracks(album_uri)

    for i in range(len(album_tracks['items'])):
        track_title.append(album_tracks['items'][i]['name'])
        track_url.append(album_tracks['items'][i]['preview_url'])
    return track_title, track_url

freesound_tags = {
    'shoegazeanddreampop': ('guitar loop', 'drone loop', 'ambience loop'),
    'dance': ('trance loop', 'house loop', 'techno loop', 'tech house loop', 'dance loop', 'dubstep loop'),
    'classical': ('violin', 'piano', 'orchestra', 'concert band', 'woodwinds', 'strings'),
    'electronica': ('lofi loop', 'chillhop loop', 'synthwave', 'electronic'),
    'rnb': ('hiphop loop', 'r&b loop'),
    'pop': ('pop loop', 'pop vocals'),
    'rock': ('rock loop', 'drum loop')
}

def previews(search):
    searching = np.random.choice(freesound_tags[search])
    preview_ids = []
    preview_urls = []
    preview_names = []

    r = requests.get("https://freesound.org/apiv2/search/text/?query={}&token=<TOKEN ID>".format(searching))
    results = r.json()['results']

    for i in range(5):
        preview_ids.append(results[i]['id'])

    for i in preview_ids:
        preview_urls.append(requests.get('https://freesound.org/apiv2/sounds/{}/?token=<TOKEN ID>.format(i)).json()['previews']['preview-hq-mp3'])
        preview_names.append(requests.get('https://freesound.org/apiv2/sounds/{}/?token=<TOKEN ID>'.format(i)).json()['name'].split(".")[0])

    return preview_urls, preview_names

# HTTP API
@app.after_request
def add_header(response):
    response.cache_control.max_age = 1
    return response

@app.route('/', methods = ["GET", "POST"])
def get_artist():
    get_spotify_service()
    artist = ""
    album_uri_short = []
    if request.method == "POST":
        try:
            artist = str(request.form["artist"])
            artist_uri = search_artist(artist)
            album_title, album_uri = get_album_list(artist_uri)
            for i in album_uri:
                uri = i.split("/")[-1]
                album_uri_short.append(uri)
            album_zip = list(zip(album_title, album_uri_short))
            return render_template("index.html", album_zip=album_zip)
        except:
            return render_template("index.html")
    else:
        return render_template("index.html")

@app.route('/album/', methods = ["GET", "POST"])
def get_tracks_url():
    track_zip = []
    track_uri_short = []
    if request.method == "POST":
        try:
            album_uri = request.form['album_uri']
            track_title, track_url = album_tracks(album_uri)
            for i in track_url:
                track_uri = i.split("/")[-1]
                track_uri_short.append(track_uri)
                track_zip = list(zip(track_title, track_uri_short))
            return render_template("index.html", track_zip=track_zip)
        except:
            return render_template("error.html")

@app.route('/tracks/', methods = ["GET", "POST"])
def play_tracks():
    cols = ['classical', 'dance', 'electronica', 'pop', 'rnb', 'rock', 'shoegazeanddreampop']
    genre = ""
    preview_url = ""
    sample_zip = []
    encoded = ""
    image = ""
    explode=(0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2)
    if request.method == "POST":
        track_uri = request.form['track_uri']
        preview_url = 'https://p.scdn.co/mp3-preview/'+str(track_uri)
        preview_song = AudioSegment.from_mp3(fileio.BytesIO(urlopen(preview_url).read()))[:30000]
        preview_song.export("static/assets/preview.wav", format="wav")
        y, sr = librosa.load('static/assets/preview.wav')
        D = librosa.feature.melspectrogram(y, sr=sr, n_mels=96)
        mpl.pyplot.figure(figsize=(12, 4))
        mpl.pyplot.close()
        ax = mpl.pyplot.axes()
        ax.set_axis_off()
        librosa.display.specshow(librosa.power_to_db(D, ref=np.max), cmap='seismic', y_axis='mel', x_axis='time')
        mpl.pyplot.savefig('static/assets/preview.png', bbox_inches='tight', transparent=False, pad_inches=0.0 )
        mpl.pyplot.close()
        img = io.imread('static/assets/preview.png', as_gray=True)
        img = img.reshape(1, img.shape[0], img.shape[1])
        cnn_test_result = cnn_model.predict(img)
        genre = cnn_test_result[0]
        genre_max = cols[np.argmax(genre)]
        sample_urls, sample_names = previews(genre_max)
        sample_zip = list(zip(sample_urls, sample_names))
        mpl.pyplot.figure(figsize=(20,7))
        mpl.pyplot.pie(genre, explode=explode, pctdistance=0.85, labels=cols, autopct='%1.1f%%', shadow=True, startangle=90, rotatelabels=270, textprops={'fontsize': 12})
        mpl.pyplot.axis('equal')
        mpl.pyplot.savefig('static/assets/preview_pie.png')
        mpl.pyplot.close()
        with open('static/assets/preview_pie.png', 'rb') as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
        image = 'data:image/png;base64,' + str(encoded)
        return render_template("predict.html", image=image, preview_url=preview_url, genre=genre, sample_zip=sample_zip)

@app.route('/predict/', methods = ["GET", "POST"])
def get_samples():
        return render_template("predict.html")

@app.route('/samples/', methods = ["GET", "POST"])
def samples():
    sample = ""
    if request.method == "POST":
        get_samples = request.form['samples']
        sample = get_samples
        print(sample)
        return redirect(sample, code=302)
    else:
        return render_template("predict.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080')
