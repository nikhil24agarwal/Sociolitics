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

demoji.download_codes()

app = Flask(__name__)
Bootstrap(app)



@app.route('/', methods=['GET','POST'])
def index():
    return render_template('login.html')


@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('home.html')


@app.route('/graph', methods=['GET','POST'])
def graph():
    return render_template('graph.html')





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


            # if has_more_posts:
            #     print(str(len(my_posts)) + ' posts retrieved so far...')

        # print('Total posts retrieved: ' + str(len(my_posts)))
        commenters = []

        # print('wait %.1f minutes' % (len(my_posts)*2/60.))

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

        print(post_comments)


        return render_template('instagram.html',report = report)
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

        r = youtube.commentThreads().list(
        part="snippet",
        order="relevance",
        videoId = vidId,
        maxResults=100    )
        response = r.execute()

        # pprint.pprint(response)
        cmnt=response

        comments_list=[]
        for i in range(len(cmnt['items'])):
            comments_list.append(cmnt['items'][i]['snippet']['topLevelComment']['snippet']['textOriginal'])



        comments_list_with_emoji_removal=[]                               #replacing emojis with empty string and storing the comments into a list
        for i in comments_list:
            comments_list_with_emoji_removal.append(demoji.replace(i, ""))

        print(comments_list_with_emoji_removal)

        return render_template('youtube.html')
    else:
        return render_template('youtube.html')



if __name__ == '__main__':
    app.run(debug=True)
