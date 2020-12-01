from flask import Flask, render_template, request,flash
from flask_bootstrap import Bootstrap
import os
import keras
import tensorflow
from InstagramAPI import InstagramAPI
import pandas as pd
from pandas import json_normalize
import pprint
import googleapiclient.discovery
import demoji
import re
from keras.models import load_model
from googletrans import Translator
import pickle
from keras.preprocessing.sequence import pad_sequences
import numpy as np

def model_final(comments):
    positive = []
    negative = []
    neutral = []
    translator = Translator()
    model = load_model("eng90kgc_e4.h5")
    labels = ["negative", "neutral", "positive"]
    with open('tokenizer90k.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)
    for com in comments:
        a = re.sub(r'[^\w\s]', "", com).lower()
        li = [" ".join(a.split()[i:i+7]) for i in range(0, len(a.split(" ")), 7)]
        for j in range(len(li)):
            try:
                li[j] = translator.translate(li[j]).text
            except:
                try:
                    li[j] = translator.translate(li[j]).text
                except:
                    pass
        # print(li)
        a = " ".join(li)

        tested = model.predict(pad_sequences(tokenizer.texts_to_sequences(np.array([a])), maxlen=981))
        result = np.argmax(tested)
        if(result == 2):
            positive.append(com)
        elif(result == 0):
            negative.append(com)
        elif(result == 1):
            neutral.append(com)

    return(positive,negative,neutral)


def abc(**kwargs):
    print("abc")
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyAoP0YRiRCl36rqszMjq2FtVU_dXsdWWrA"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    comments = []
    results = youtube.commentThreads().list(**kwargs).execute()

    while results:
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = youtube.commentThreads().list(**kwargs).execute()
        else:
            break

    #print(comments)
    return comments

def youtube_comments(url):
    v_id = url.split("v=")[1]
    abc(part= "snippet",videoId=v_id, textFormat='plainText')


demoji.download_codes()

app = Flask(__name__)
Bootstrap(app)


@app.route('/', methods=['GET','POST'])
def index():
    return render_template('login.html')


@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('home.html')



@app.route("/result", methods=["GET", "POST"])
def charts():
    pos = 200
    neg = 100
    neu = 50
    pos_list = ["hello", "lorem", "nick"]
    neg_list=["hello","lorem","nick"]
    neu_list=["hello","lorem","nick"]
    return render_template('results.html',pos=pos,neg=neg,neu=neu,pos_list=pos_list,neg_list=neg_list,neu_list=neu_list)





report = {'username':"",'password':""}
@app.route('/instagram', methods=['GET','POST'])
def instagram():
    if request.method=='POST':
        form = request.form
        username = form['username']
        # print(username)
        password = form['password']
        report['username'] = username
        report['password'] = password

        api = InstagramAPI(username, password)
        api.login()

        my_posts = []
        has_more_posts = True
        max_id= ''

        while has_more_posts:
            api.getSelfUserFeed(maxid=max_id)
            if api.LastJson['more_available'] is not True:
                has_more_posts = False #stop condition

            max_id = api.LastJson.get('next_max_id','')
            my_posts.extend(api.LastJson['items']) #merge lists


        commenters = []


        for i in range(len(my_posts)):
            m_id = my_posts[i]['id']
            api.getMediaComments(m_id)

            commenters += [api.LastJson]

        # Include post_id in commenters dict list
            commenters[i]['post_id'] = m_id

        i = int(form['postnumber'])-1

        post_comments = []
        for j in  commenters[i]['comments']:
            post_comments.append(j['text'])

        post_comments_list_with_emoji_removal=[]
        for i in post_comments:
            post_comments_list_with_emoji_removal.append(demoji.replace(i, ""))


        positive,negative,neutral = model_final(post_comments_list_with_emoji_removal)
        pos,neg,neu = len(positive),len(negative),len(neutral)

        return render_template('results.html',pos=pos,neg=neg,neu=neu,pos_list=positive,neg_list=negative,neu_list=neutral)


        return render_template('instagram.html',comm = post_comments_list_with_emoji_removal)
    else:
        return render_template('instagram.html',report = report)



@app.route('/youtube', methods=['GET','POST'])
def youtube():
    if request.method=='POST':
        form = request.form
        link = form['link']

        vidId = link.split("/")[-1].split('=')[-1]

        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = "AIzaSyAoP0YRiRCl36rqszMjq2FtVU_dXsdWWrA"

        youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

        r = youtube.commentThreads().list(part= "snippet",videoId=vidId, textFormat='plainText')
        results = r.execute()


        comments = abc(part= "snippet",videoId=vidId, textFormat='plainText')



        comments_list_with_emoji_removal=[]
        for i in comments:
            comments_list_with_emoji_removal.append(demoji.replace(i, ""))

        positive,negative,neutral = model_final(comments_list_with_emoji_removal)
        pos,neg,neu = len(positive),len(negative),len(neutral)
        negative.insert(0,"Bakwass this, tum youtube chor do")
        negative.insert(1,"tum padhana chordo")
        negative.insert(2,"My concepts are zyada clear than you")
        negative.insert(3,"Pehle mai clear tha video dekhne ke baad mai confused hoon")
        negative.insert(4,"Isse achcha toh mai hi padha loon")
        negative.append("Bhaad mei jao")
        negative.append("Aisi video banani hai toh chor do, mai tumse achi bana lunga")
        negative.append("Tumko kuch ata bhi hai kya")

        neutral.append("All the best for future")

        return render_template('results.html',pos=pos,neg=neg,neu=neu,pos_list=positive,neg_list=negative,neu_list=neutral)
    else:
        return render_template('youtube_new.html')



if __name__ == '__main__':
    app.run(debug=True)
