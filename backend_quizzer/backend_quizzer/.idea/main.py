#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import wikipedia
import wikipediaapi
import json
import numpy as np
import random
import time
import math
from time import gmtime, strftime
import csv
import warnings

warnings.filterwarnings('ignore')
import sys, os, re

from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import copy
import base64
import io
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
from os import listdir
from os.path import isfile, join

# from data_stats import *
sys.path.insert(1, './question_base')
from query_question_pool import *
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import json
import time
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from base64 import b64decode
import random
import logging
import sys

SHA_TZ = timezone(
    timedelta(hours=8),
    name='Asia/Shanghai',
)

app = Flask(__name__, static_url_path='')
CORS(app)
app._static_folder = "static"

count = 1
store_data = []

dialogue = []
image_dict = '/root/v2_agent/image1'

# 列表存储数据
onlyfiles = [f for f in listdir(image_dict) if isfile(join(image_dict, f))]
print(len(onlyfiles))
post_ids = [img_path.split('.')[0] for img_path in onlyfiles]

ui_element_pool = []
visual_element_pool = []

# ui池 视觉元素池
with open('./all_ui_elements.json', 'r') as f:
    ui_element_pool = json.load(f)

with open('./all_visual_elements.json', 'r') as f:
    visual_element_pool = json.load(f)

msg_example = {  # the tutor and the user side use similar format of msg
    'message': 'User message from client',
    'tutor_message': "Tutor\'s message from server",
    'user_id': '',  # assigned by the server
    'isImage': False,
    'imgs': [],
    # 'payload': {src: '', alt: '', width: ''},
    'state': "Topic selection",
    'sender': "tutor",
    'options': [],
    'sentTime': "just now",
    'direction': "incoming",
    'cloze_test': '',
    'multiple_choices': [],
    'explanation': '',
    'correct_answer': '',
    'correct_answers': [],
    'post_id': '',
    'mention_ui_elements': [],
    'wiki': [],
    'post_id': 'none',
    'topic': '',
    'resources': []
}


# 处理用户信息
def handle_user_info(msg, user_id, user_file='./user_record.json'):
    user_data = []
    return_user_id = user_id
    post_ids = []
    question_ids = []
    with open(user_file, 'r') as f:
        user_data = json.load(f)

    # 如果消息为空
    if msg == '':
        user_data.append({
            'user_id': len(user_data),
            'questions': [],  # 所有回答过的question information
            'correct': 0,  # 记录回答正确的条数
            'total': 0,  # 记录总共回答过的条数
        })
        return_user_id = len(user_data) - 1
    else:
        # 如果消息不为空
        # 记录时间：
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        beijing_now = utc_now.astimezone(SHA_TZ)
        msg['time_stamp'] = str(beijing_now) + str(beijing_now.tzname())

        user_data[user_id]['questions'].append(msg)

        if (msg['state'] == 'Give Hint' and msg['message'] != 'I don\'t know.' and msg['message'] != '') or (
                (msg['state'] == 'Ask Question') and msg['message'] != 'I don\'t know.' and msg[
            'message'] != 'I need a hint.' and msg['message'] != ''):
            print('##### Enter here ############')
            user_data[user_id]['total'] = user_data[user_id]['total'] + 1
            if msg['message'] in msg['correct_answers']:
                user_data[user_id]['correct'] = user_data[user_id]['correct'] + 1
        for question in user_data[user_id]['questions']:
            if question['post_id'] not in post_ids:
                post_ids.append(question['post_id'])
            if question['question_id'] not in question_ids:
                question_ids.append(question['question_id'])
        print(question_ids)

    with open(user_file, 'w') as f:
        json_string = json.dumps(user_data)
        f.write(json_string)

    return {
        'user_id': return_user_id,
        'post_ids': post_ids,
        'question_ids': question_ids,
        'correct': user_data[return_user_id]['correct'],
        'total': user_data[return_user_id]['total']
    }


def search_wiki(topic):
    if (topic == "Sexual Orientation"):
        return '<p><b>Sexual orientation</b> is an enduring personal pattern of <a href="/wiki/Romance_(love)" title="Romance (love)">romantic</a> attraction or <a href="/wiki/Sexual_attraction" title="Sexual attraction">sexual attraction</a> (or a combination of these) to persons of the opposite <a href="/wiki/Sex" title="Sex">sex</a> or <a href="/wiki/Gender" title="Gender">gender</a>, the same sex or gender, or to both sexes or more than one gender. Patterns are generally categorized under <a href="/wiki/Heterosexuality" title="Heterosexuality">heterosexuality</a>, <a href="/wiki/Homosexuality" title="Homosexuality">homosexuality</a>, and <a href="/wiki/Bisexuality" title="Bisexuality">bisexuality</a>,<sup id="cite_ref-AmPsycholAssn-whatis_1-0" class="reference"><a href="#cite_note-AmPsycholAssn-whatis-1"><span class="cite-bracket">[</span>1<span class="cite-bracket">]</span></a></sup><sup id="cite_ref-AmPsychiAssn-Sexual_orientation_2-0" class="reference"><a href="#cite_note-AmPsychiAssn-Sexual_orientation-2"><span class="cite-bracket">[</span>2<span class="cite-bracket">]</span></a></sup><sup id="cite_ref-AmPsycholAssn-definitions_3-0" class="reference"><a href="#cite_note-AmPsycholAssn-definitions-3"><span class="cite-bracket">[</span>3<span class="cite-bracket">]</span></a></sup> while <a href="/wiki/Asexuality" title="Asexuality">asexuality</a> (experiencing no sexual attraction to others) is sometimes identified as the fourth category.<sup id="cite_ref-Sex_and_society_4-0" class="reference"><a href="#cite_note-Sex_and_society-4"><span class="cite-bracket">[</span>4<span class="cite-bracket">]</span></a></sup><sup id="cite_ref-Bogaert_5-0" class="reference"><a href="#cite_note-Bogaert-5"><span class="cite-bracket">[</span>5<span class="cite-bracket">]</span></a></sup></p>'


image_server_url = '127.0.0.1:3004/'


@app.route('/', methods=["GET", "POST"])
def index():
    tutor_msg = []
    if request.method == 'POST':
        start_time = time.time()
        print('Connect')
        raw_data = list(request.form.to_dict().keys())
        data = json.loads(raw_data[0])
        data = data['data']
        print('Now we get data: ')
        print(data)

        ### Handle user intent
        user_message = data['message']
        state = data['state']
        post_id = data['post_id']
        print('User: {} ({})'.format(user_message, state))

        if state == 'Topic Selection':
            # if user_message=='Sex Orientation':

            msg = copy.deepcopy(msg_example)
            msg['topic'] = user_message
            msg[
                'tutor_message'] = "Based on the topic <b>" + user_message + " </b>you choose, some relevant resources will be shown as below. Please read and study according to your demand"
            msg['state'] = 'Resources'
            user_info = handle_user_info('', '')
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            tutor_msg.append(msg)

            # Next we'll put some resources about that topic by searching the database
            msg = copy.deepcopy(msg_example)
            msg['tutor_message'] = search_wiki(user_message)
            tutor_msg.append(msg)
            
            msg = copy.deepcopy(msg_example)
            msg['tutor_message'] = '<b>And we have some examples from communities of ' + user_message + "</b><br/>";

            # resources_items = []
            # # query_results = search_question('', cluster='color_design', type='design_element')
            # # info[user_message] = ;
            # query_results = [
            #     "<a href='https://www.baidu.com' target='woc' >10 things that you need to know-sincere advice…</a>",
            #     "10 things that you need to know-sincere advice…", "10 things that you need to know-sincere advice…",
            #     "10 things that you need to know-sincere advice…", "10 things that you need to know-sincere advice…",
            #     "10 things that you need to know-sincere advice…"]
            # for i in range(len(query_results)):
            #     resources_items.append(query_results[i])
            #     msg['resources'].append(query_results[i])
            msg[
                'tutor_message'] = msg[
                                       'tutor_message'] + "<a href='https://www.baidu.com' target='woc'>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a>"
            msg['state'] = "Multiple-choice Quiz"
            user_info = handle_user_info('', '')
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            tutor_msg.append(msg)

            msg = copy.deepcopy(msg_example)
            msg[
                'tutor_message'] = "That‘s all, Do you wanna more knowledge about this topic? Or do u have more detailed questions？<b><br/> If no, Please Press the button below.<br/> If you do have questions, please type and submit your texts."
            msg['options'].append("I already understand!")
            msg['state'] = "Step One Finished"
            tutor_msg.append(msg)

        if state == 'Step One Finished' and user_message != "I already understand!":
            msg = copy.deepcopy(msg_example)
            user_message_cleaned = user_message.replace("\n", " ")
            msg['tutor_message'] = search_gpt(user_message_cleaned)
            tutor_msg.append(msg)

            msg = copy.deepcopy(msg_example)
            user_message_cleaned = user_message.replace("\n", " ")
            msg['tutor_message'] = "For more details on these terms, you might find this article helpful:<br/>Content + [link1] ………"
            tutor_msg.append(msg)
            # msg['tutor_message'] = search_content()



            msg = copy.deepcopy(msg_example)
            msg[
                'tutor_message'] = "If you have more questions or need further clarification, feel free to ask!<br/><b> If no, Please Press the button below.<br/>If you do have questions, please type and submit your texts."
            msg['options'].append("I already understand!")
            msg['state'] = 'Step One Finished'
            tutor_msg.append(msg)

        # if state == 'Step One Finished' and user_message == 'I already understand!':
        #     msg = copy.deepcopy(msg_example)
        #     msg['state'] = "Step Two Begins"
        #     msg[
        #         'tutor_message'] = "<b>Great to hear! If you have any more questions or need further support, feel free to ask. I'm here to help!</b>"
        #     msg['state'] = "Step Two Begins"
        #     tutor_msg.append(msg)
        #
        #     msg = copy.deepcopy(msg_example)
        #     msg['tutor_message'] = "Step1 以上"
        #     tutor_msg.append(msg)
        #
        # if state == 'Step Two Begins' and user_message == "I already understand!":
        #     msg = copy.deepcopy(msg_example)
        #     msg['tutor_message'] = "Step1 以上"
        #     tutor_msg.append(msg)

        if user_message == "I already understand!":
            msg = copy.deepcopy(msg_example)
            msg['state'] = "Step One Finished"
            msg[
                'tutor_message'] = "<b>Great to hear! If you have any more questions or need further support, feel free to ask. I'm here to help!</b>"
            tutor_msg.append(msg)

        if state == "Step One Finished":
            msg = copy.deepcopy(msg_example)
            msg['state'] = "Step Two Begins"

            msg['tutor_message'] = "Now let‘s start the case study session, Here is an example of the community post:<br/>" \
                                   "How do I describe the difference between pansexual and bisexual?<br/>" \
                                   "There are some stupid homophobic boys I know and they can’t seem to grasp the different between pan and bi. Does anyone have a better way of explaining being pan other than ‘I don’t care about gender and I like all genders no matter what."
            op = ['Show me comments', 'I didn\'t understand the post']
            for it in op:
                msg['options'].append(it)
            tutor_msg.append(msg)

        if state == 'Step Two Begins' and user_message == "I didn\'t understand the post":
            msg = copy.deepcopy(msg_example)
            msg['state'] = "fail to understand"
            query = user_message + ": How do I describe the difference between pansexual and bisexual?<br/>" \
                                   "There are some stupid homophobic boys I know and they can’t seem to grasp the different between pan and bi. Does anyone have a better way of ex"
            msg['tutor_message'] = search_gpt(query) + "<br/>If you still don‘t understand, <b>copy this paragraph</b> and send it to me"
            msg['options'].append("Show me comments")
            tutor_msg.append(msg)


        if state == "fail to understand" and user_message!="Show me comments":
            msg = copy.deepcopy(msg_example)
            msg["state"] = "fail to understand"
            msg["tutor_message"] = search_gpt(user_message)
            msg['options'].append("Show me comments")
            tutor_msg.append(msg)

        if state == "fail to understand" and user_message == "Show me comments":
            msg = copy.deepcopy(msg_example)
            msg['state'] = 'show comments'
            msg['tutor_message'] = "<b>Comment1:<b/> Gender < Vibes <br/>" \
                                   "<b>Comment2:<b/> Do they not understand that there are more then 2 sexual identities? What is their hang up on the statement?<br/>" \
                                   "<b>Comment3:<b/> Bisexuals: i love all genders. Pansexuals: i love regardless of gender<br/>" \
                                   "<b>Comment4:<b/> my partner can transition and my feelings wouldn't change a bit<br/>" \
                                   "<b>Comment5:<b/> Bi: I like blondes, redheads, and brunettes. Not all at once, or to the same degree. Pan: I don’t care about hair color<br/>"
            msg['options']=["Show me more comments" , "I have a few questions to ask"]
            tutor_msg.append(msg)

        if user_message == "I have a few questions to ask":
            msg = copy.deepcopy(msg_example)
            msg['state'] = 'ask questions'
            msg['tutor_message'] = 'Feel free to ask! '
            tutor_msg.append(msg)

        if state == "ask questions":
            msg = copy.deepcopy(msg_example)
            msg["tutor_message"] = search_gpt(user_message)
            msg['state'] = 'questions'
            msg['options'].append("I got it!")
            tutor_msg.append(msg)

        if user_message == "Show me more comments":
            msg = copy.deepcopy(msg_example)
            msg['state'] = 'show comments'
            msg['tutor_message'] = "<b>Comment1:<b/> Gender < Vibes" \
                                   "<b>Comment2:<b/> Do they not understand that there are more then 2 sexual identities? What is their hang up on the statement?" \
                                   "<b>Comment3:<b/> Bisexuals: i love all genders. Pansexuals: i love regardless of gender" \
                                   "<b>Comment4:<b/> my partner can transition and my feelings wouldn't change a bit" \
                                   "<b>Comment5:<b/> Bi: I like blondes, redheads, and brunettes. Not all at once, or to the same degree. Pan: I don’t care about hair color"
            msg['options'] = ["Show me more comments", "I have a few questions to ask"]
            tutor_msg.append(msg)

        if user_message == "I got it!":
            msg=copy.deepcopy(msg_example)
            msg['tutor_message'] = "wait"
            tutor_msg.append(msg)



        # tutor_msg = []



        ### Prepare tutor msgs here
        ## Self-introduction:

        # if user_message == 'Cool, but how?':
        #     msg = copy.deepcopy(msg_example)
        #     msg['tutor_message'] = 'Firstly, I will ask you which <b>topic</b> is your favourite.'
        #     msg['state'] = 'Self Introduction'
        #     tutor_msg.append(msg)
        #     msg = copy.deepcopy(msg_example)
        #     msg[
        #         'tutor_message'] = 'You can choose the options below my message and input your interested topic or question when needed.'
        #     msg['state'] = 'Self Introduction'
        #     user_info = handle_user_info('', '')
        #     msg['user_id'] = user_info['user_id']
        #     msg['correct'] = user_info['correct']
        #     msg['total'] = user_info['total']
        #     tutor_msg.append(msg)
        #
        #     msg['options'].append('Got it. Let\'s go!')

        ## Begin Next Question:
        if user_message == 'Got it. Let\'s go!' or user_message == 'Another UI Example!':
            # Tutor message (start)
            msg = copy.deepcopy(msg_example)
            msg['tutor_message'] = 'Here\'s some options for you.'

            user_info = handle_user_info('', '')
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            options = ["sexual orientation", "sexual orientation", "sexual orientation"]
            for i in range(len(options)):
                msg['multiple_choices'].append(options[i])
                msg['options'].append(options[i])
            msg['state'] = 'Topic Selection'
            user_info = handle_user_info('', '')
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            tutor_msg.append(msg)

            # msg['state'] = 'Begin Next Question'
            # # Add this message
            # # tutor_msg.append(msg)
            # print('Tutor turn: Begin Next Question and Ask Question')
            # # print('checkpoint')
            # msg = copy.deepcopy(msg_example)
            # query_results = search_question('', cluster='color_design', type='design_element')
            # # To do: Need to check if this question has appeared before
            # # Assign user_id:
            # user_info = handle_user_info('', '')
            # msg['user_id'] = user_info['user_id']
            # msg['correct'] = user_info['correct']
            # msg['total'] = user_info['total']
            # temp_index = random.randint(0, len(query_results) - 1)
            # item = query_results[temp_index]
            # msg['post_id'] = item['post_id']
            # msg['question_id'] = item['question_id']
            # msg['cloze_test'] = item['question']
            # msg['correct_answer'] = item['right_answer']
            # msg['cloze_answer'] = item['right_answer']
            # msg['explanation'] = item['explanation']
            # msg['mention_ui_elements'] = list(item['mention_ui_elements'])
            # msg['answer_cluster'] = item['answer_cluster']
            # msg['hint'] = item['hint']
            # msg['wiki'] = []
            # options = []
            # options.append(item['other_option_1'])
            # options.append(item['other_option_2'])
            # options.append(item['right_answer'])
            # # print(options)
            #
            # arr = np.array([0, 1, 2])
            # np.random.shuffle(arr)
            # for i in arr:
            # 	msg['multiple_choices'].append(options[i])
            # 	msg['options'].append(options[i])
            # # Prepare image link
            # img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
            # imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
            # msg['imgs'].append(imgs)
            # msg['post_title'] = item['post_title']
            # msg['post_body'] = item['post_body']
            # # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
            # temp_msg_pool1 =  ['For the critique about this example:', 'Someone critiques this example like this:', 'There is a possible critique on this example:', 'I got a critique from the community for this example:']
            # temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1)-1)]
            # temp_msg_pool2 = ['Which of the following options would be the right one?', 'Could you choose an option to fill in the blank?',
            # 				  'Which word(s) may fit the sentence according to the UI example?',
            # 				  'Which option would come from the original critique?']
            # temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
            # msg['tutor_message'] = temp_msg_1 + '\n \"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
            # ## Ask Question (first question of an UI example)
            # msg['options'].append('I don\'t know.')
            # msg['options'].append('I need a hint.')
            # msg['state'] = 'Ask Question'
            # tutor_msg.append(msg)

        # if state == 'Topic Selection':
        #     msg = copy.deepcopy(msg_example)
        #     msg['topic'] = user_message
        #     msg['tutor_message'] = "Based on the topic <b>" + user_message + " </b>you choose, some relevant resources will be shown as below. Please read and study according to your demand"
        #     msg['state'] = 'Resources'
        #     user_info = handle_user_info('', '')
        #     msg['user_id'] = user_info['user_id']
        #     msg['correct'] = user_info['correct']
        #     msg['total'] = user_info['total']
        #     tutor_msg.append(msg)
        #
        #     #Next we'll put some resources about that topic by searching the database
        #
        #     resources_items=[]
        #     # query_results = search_question('', cluster='color_design', type='design_element')
        #     # info[user_message] = ;
        #     query_results = ["<a href='https://www.baidu.com' target='woc' >10 things that you need to know-sincere advice…</a>","10 things that you need to know-sincere advice…","10 things that you need to know-sincere advice…","10 things that you need to know-sincere advice…","10 things that you need to know-sincere advice…","10 things that you need to know-sincere advice…"]
        #     for i in range(len(query_results)):
        #         resources_items.append(query_results[i])
        #         msg['resources'].append(query_results[i])
        #
        #     msg=copy.deepcopy(msg_example)
        #     msg['tutor_message'] = "<a href='https://www.baidu.com' target='woc'>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a><br /><a>10 things that you need to know-sincere advice…</a>"
        #     msg['options'].append("Move Forward")
        #     msg['state'] = "Multiple-choice Quiz"
        #     user_info = handle_user_info('', '')
        #     msg['user_id'] = user_info['user_id']
        #     msg['correct'] = user_info['correct']
        #     msg['total'] = user_info['total']
        #     tutor_msg.append(msg)

        if user_message == "Move Forward" and state == 'Multiple-choice Quiz':
            msg = copy.deepcopy(msg_example)
            user_info = handle_user_info('', '')
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['tutor_message'] = "<b>Q: What is the difference between pansexual and bisexual ? </b>"
            options = [
                "Pansexual is attraction to someone regardless of gender; Bisexual is attraction to multiple genders.",
                "Pansexual is the attraction to two or more genders WITHOUT preference; Bisexual the attraction WITH preference.",
                "Pansexual is more inclusive of all genders; Bisexual only refers to being attracted to two genders.",
                "Pansexual’s family doesn’t need to know about their sexual life."]
            msg['correct_answers'].append(options[0])
            msg['correct_answers'].append(options[2])
            msg['multiple_choices'] = options
            for item in options:
                msg['options'].append(item)
            msg['options'].append("Need Hints")
            msg['hint'] = "<b>Hint:</b>pansexuality is initially “gender blind” in attraction"

            # item = query_results[temp_index]
            msg['post_id'] = 1
            msg['question_id'] = 1
            msg[
                'explanation'] = "Having realized your arguments and points of doubt.<br/><a>…….（提供解释）…..<a><br/> So now do you think that's a reasonable explanation?"

            msg['wiki'] = []
            tutor_msg.append(msg)

        if user_message == "Need Hints":
            # msg = copy.deepcopy(msg_example)
            # user_info = handle_user_info(data, data['user_id'])
            # msg['tutor_message'] = user_info['hint']
            # msg['options']=user_info['options']
            # msg['correct_answers'] = user_info['correct_answers']
            # tutor_msg.append(msg)
            msg = copy.deepcopy(data)
            print(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']

            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Link to external dataset using a function
            options = msg['multiple_choices']
            hints = msg['hint']

            temp_msg_pool1 = ['Here are more contexts about this critique:',
                              'More information from the original comment:',
                              'You can check more information about this critique:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1 + '\n' + hints
            print('Tutor turn: Give Hint')
            msg['options'] = msg['multiple_choices']
            if 'I don\'t know.' not in msg['options']:
                msg['options'].append('I don\'t know.')
            # msg['correct_answer'] = 'Right answer'
            msg['state'] = 'Hints Given'
            tutor_msg.append(msg)
        showAnswer = False

        if (state == 'dialog state' or state == 'Hints Given') and user_message != "Need Hints":
            print('hi')
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            msg['sender'] = 'tutor'
            if 'user_id' not in data.keys():
                user_info = handle_user_info('', '')
            else:
                user_info = handle_user_info(data, data['user_id'])
            # user_info = handle_user_info(data, data['user_id'])
            print(msg)
            if user_message not in msg['correct_answers']:
                temp_msg_pool1 = ['I\'m sorry, that\'s not quite right.',
                                  'Oh, that\'s not quite right.',
                                  'Sorry, it seems not the right answer.',
                                  'I\'m sorry, that\'s not the most appropriate option.']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1
                msg['state'] = 'Incorrect Answer'
                tutor_msg.append(msg)
                print('Tutor turn: Give Hint and Incorrect Answer')
            else:
                ## Correct Answer
                # Tutor message
                temp_msg_pool1 = ['That\'s correct!',
                                  'You are right!',
                                  'Great! It\'s correct!',
                                  'Nice! You choose the right answer!',
                                  'Good!', 'Well done!', 'Nice choice!']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1

                msg['state'] = 'Correct Answer'
                # print('wwwwwwwwwwwwwwwwww')
                print(msg)
                tutor_msg.append(msg)
                print('Tutor turn: Give Hint and Correct Answer')
            showAnswer = True

        if showAnswer:
            msg = copy.deepcopy(data)
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_msg_pool1 = ['The correct answer is:',
                              'The word in the original comment is:',
                              'The right choice would be:',
                              'The correct choice is:',
                              'The answer should be:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]

            msg['tutor_message'] = temp_msg_1
            for item in data['correct_answers']:
                msg['tutor_message'] = msg['tutor_message'] + ' <b>' + item + '</b>' + '<br/>'

            if state == 'Incorrect Answer':
                msg['options'] = ['Why?', 'Wait, I got it right!', 'Next Question!']
            else:
                msg['options'] = ['Why?', 'Wait, it\'s not necessarily right!', 'Next Question!', "Move Forward"]
            msg['state'] = 'Show Answer'
            tutor_msg.append(msg)
            print('Tutor turn: Show Answer')
        showAnswer = False

        sample = {
            'user_id': 666,
            'creativity': 'Your friend Xiao Ming has been feeling very confused lately. He told you that he is attracted to almost all genders and doesn\'t care about the gender of a person, but <b>he doesn’t like ONE gender</b>, and unable to be physically or emotionally attracted to  the specific gender. Xiao Ming is unsure whether he is pansexual, polysexual, or bisexual.  He doesn\'t know how to define his sexual orientation. Xiao Ming is looking for <b>advice to better understand and accept himself.</b>',
            'Q1': '<b>Q1:How would you explain the differences between pan, bi and poly?</b>',
            'Q2': 'Q2:What steps would you suggest he take to further explore and clarify his sexual orientation?',
            'Q3': 'Q3:What resources or support would you recommend to Xiao Ming to help him better accept and understand himself?',
            'A1': '',
            'A2': '',
            'A3': ''
        }
        if user_message == 'Move Forward' and (state == 'Show Answer' or state == 'Show Explanation'):
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'

            msg['state'] = 'Scenario-specific creativity Quiz'
            msg_info = copy.deepcopy(msg_example)
            # sample = {
            #     'user_id': user_info['user_id'],
            #     'creativity':'Your friend Xiao Ming has been feeling very confused lately. He told you that he is attracted to almost all genders and doesn\'t care about the gender of a person, but <b>he doesn’t like ONE gender</b>, and unable to be physically or emotionally attracted to  the specific gender. Xiao Ming is unsure whether he is pansexual, polysexual, or bisexual.  He doesn\'t know how to define his sexual orientation. Xiao Ming is looking for <b>advice to better understand and accept himself.</b>',
            #     'Q1':'<b>Q1:How would you explain the differences between pan, bi and poly?</b>',
            #     'Q2':'Q2:What steps would you suggest he take to further explore and clarify his sexual orientation?',
            #     'Q3':'Q3:What resources or support would you recommend to Xiao Ming to help him better accept and understand himself?',
            #     'A1':'',
            #     'A2':'',
            #     'A3':''
            # }
            msg_info['tutor_message'] = sample['creativity']
            print('step3:asking question')
            tutor_msg.append(msg_info)
            msg['tutor_message'] = sample['Q1']
            tutor_msg.append(msg)
            # msg['tutor_message'] = sample['Q1']
            # tutor_msg.append(msg)

        if state == 'Scenario-specific creativity Quiz':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            msg['state'] = 'Scenario-specific creativity Quiz-A1 received'
            sample['A1'] = "<b>" + copy.deepcopy(user_message) + "</b>"
            msg['tutor_message'] = "<b>" + sample['Q2'] + "</b>"
            tutor_msg.append(msg)

        if state == 'Scenario-specific creativity Quiz-A1 received':
            msg = copy.deepcopy(data)
            str = copy.deepcopy(user_message)
            user_info = handle_user_info(data, data['user_id'])
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            msg['state'] = 'Scenario-specific creativity Quiz-A2 received'
            sample['A2'] = "<b>" + str + "</b>"
            msg['tutor_message'] = "<b>" + sample['Q3'] + "<b>"
            tutor_msg.append(msg)

        if state == 'Scenario-specific creativity Quiz-A2 received':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            msg['state'] = 'Scenario-specific creativity Quiz-A2 received'
            sample['A3'] = "<b>" + copy.deepcopy(user_message) + "</b>"
            msg['tutor_message'] = sample['A1'] + "<br/>" + sample['A2'] + "<br/>" + sample['A3']
            tutor_msg.append(msg)
            print(sample)

        ## Ask Question (another question of the same UI example)
        if user_message == 'Next Question!' and (
                state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query UI Component' or state == 'Query Visual Element'):
            msg = copy.deepcopy(msg_example)
            # random UI question
            # query_results = search_question('', type='design_element')

            # To do: Need to check if this question has appeared before
            if 'user_id' not in data.keys():
                user_info = handle_user_info('', '')
            else:
                user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            question_ids = user_info['question_ids']

            # Check if the same post has another unasked question
            query_results = search_question('', post_id=data['post_id'], cluster='color_design', type='design_element')
            item = {}
            query_flag = False
            for temp in query_results:
                if temp['question_id'] not in question_ids:
                    item = temp
                    query_flag = True
                    break
            if not query_flag:
                query_results = search_question('', cluster='color_design', type='design_element')
                for temp in query_results:
                    if temp['question_id'] not in question_ids:
                        item = temp
                        query_flag = True
                        break
            if not query_flag:
                query_results = search_question('', type='')
                for temp in query_results:
                    if temp['question_id'] not in question_ids:
                        item = temp
                        query_flag = True
                        break
            # temp_index = random.randint(0, len(query_results) - 1)
            # item = query_results[temp_index]

            msg['post_id'] = item['post_id']
            msg['question_id'] = item['question_id']
            msg['cloze_test'] = item['question']
            msg['correct_answer'] = item['right_answer']
            msg['cloze_answer'] = item['right_answer']
            msg['explanation'] = item['explanation']
            msg['mention_ui_elements'] = item['mention_ui_elements']
            msg['answer_cluster'] = item['answer_cluster']
            msg['hint'] = item['hint']
            options = []
            options.append(item['other_option_1'])
            options.append(item['other_option_2'])
            options.append(item['right_answer'])
            arr = np.array([0, 1, 2])
            np.random.shuffle(arr)
            for i in arr:
                msg['multiple_choices'].append(options[i])
                msg['options'].append(options[i])
            print('#' * 40)
            print(msg['options'])
            print(msg['wiki'])
            # Prepare image link
            img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
            imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
            msg['imgs'].append(imgs)
            msg['post_title'] = item['post_title']
            msg['post_body'] = item['post_body']
            # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
            temp_msg_pool1 = ['For the critique about this example:', 'Someone critiques this example like this:',
                              'There is a possible critique on this example:',
                              'I got a critique from the community for this example:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            temp_msg_pool2 = ['Which of the following options would be the right one?',
                              'Could you choose an option to fill in the blank?',
                              'Which word(s) may fit the sentence according to the UI example?',
                              'Which option would come from the original critique?']
            temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
            msg['tutor_message'] = temp_msg_1 + '\n \"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
            ## Ask Question (first question of an UI example)
            msg['options'].append('I don\'t know.')
            msg['options'].append('I need a hint.')
            msg['state'] = 'Ask Question'
            tutor_msg.append(msg)

        if state == 'Query UI Component' and user_message != 'Next Question!' and user_message != 'I want to explore a visual element.':
            msg = copy.deepcopy(msg_example)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            question_ids = user_info['question_ids']

            # Check if the same post has another unasked question
            query_results = query_results = search_question(user_message, type='ui_element')
            item = {}
            query_flag = False
            for temp in query_results:
                if temp['question_id'] not in question_ids:
                    item = temp
                    query_flag = True
                    break
            if query_flag:
                # Tutor message (start)
                temp_msg_pool1 = ['Here are an UI example and a critique about ui component ',
                                  'I got a critique of an example for you about ',
                                  'Let\'s check this critique and example related to ']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1 + '\"' + user_message + '\".'
                msg['state'] = 'Begin Next Question'
                # Add this message
                tutor_msg.append(msg)
                print('Tutor turn: Begin Next Question and Ask Question')

                msg = copy.deepcopy(msg_example)
                user_info = handle_user_info(data, data['user_id'])
                msg['user_id'] = user_info['user_id']
                msg['correct'] = user_info['correct']
                msg['total'] = user_info['total']
                # To do: Need to check if this question has appeared before
                # temp_index = random.randint(0, len(query_results) - 1)
                # item = query_results[temp_index]
                msg['post_id'] = item['post_id']
                msg['question_id'] = item['question_id']
                msg['cloze_test'] = item['question']
                msg['correct_answer'] = item['right_answer']
                msg['cloze_answer'] = item['right_answer']
                msg['explanation'] = item['explanation']
                msg['mention_ui_elements'] = item['mention_ui_elements']
                msg['answer_cluster'] = item['answer_cluster']
                msg['hint'] = item['hint']
                options = []
                options.append(item['other_option_1'])
                options.append(item['other_option_2'])
                options.append(item['right_answer'])
                arr = np.array([0, 1, 2])
                np.random.shuffle(arr)
                for i in arr:
                    msg['multiple_choices'].append(options[i])
                    msg['options'].append(options[i])
                # Prepare image link
                img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
                imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
                msg['imgs'].append(imgs)
                msg['post_title'] = item['post_title']
                msg['post_body'] = item['post_body']
                # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
                temp_msg_pool2 = ['Which of the following options would be the right one?',
                                  'Could you choose an option to fill in the blank?',
                                  'Which word(s) may fit the sentence according to the UI example?',
                                  'Which option would come from the original critique?']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = '\"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
                ## Ask Question (first question of an UI example)
                msg['options'].append('I don\'t know.')
                msg['options'].append('I need a hint.')
                msg['state'] = 'Ask Question'
                tutor_msg.append(msg)
            else:
                # Tutor message (start)
                temp_msg_pool1 = ['Sorry, I do not have more critiques with ui component keyword ',
                                  'Sorry, the critique pool from the community does not have questions with ',
                                  'Sorry, there is no more question in the critique pool with ']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                temp_msg_pool2 = ['How about this one?',
                                  'Would you like to try this one?',
                                  'Let\'s check this one!']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = temp_msg_1 + '\"' + user_message + '\".' + temp_msg_2
                msg['state'] = 'Begin Next Question'
                # Add this message
                tutor_msg.append(msg)
                print('Tutor turn: Begin Next Question and Ask Question')

                msg = copy.deepcopy(msg_example)
                user_info = handle_user_info(data, data['user_id'])
                msg['user_id'] = user_info['user_id']
                msg['correct'] = user_info['correct']
                msg['total'] = user_info['total']
                query_results = search_question('', cluster='color_design', type='ui_element')
                # To do: Need to check if this question has appeared before
                temp_index = random.randint(0, len(query_results) - 1)
                item = query_results[temp_index]
                msg['post_id'] = item['post_id']
                msg['question_id'] = item['question_id']
                msg['cloze_test'] = item['question']
                msg['correct_answer'] = item['right_answer']
                msg['cloze_answer'] = item['right_answer']
                msg['explanation'] = item['explanation']
                msg['mention_ui_elements'] = item['mention_ui_elements']
                msg['answer_cluster'] = item['answer_cluster']
                msg['hint'] = item['hint']
                # msg['ui_elements'] = item['ui_elements']
                options = []
                options.append(item['other_option_1'])
                options.append(item['other_option_2'])
                options.append(item['right_answer'])
                print(options)
                arr = np.array([0, 1, 2])
                np.random.shuffle(arr)
                for i in arr:
                    msg['multiple_choices'].append(options[i])
                    msg['options'].append(options[i])
                # Prepare image link
                img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
                imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
                msg['imgs'].append(imgs)
                msg['post_title'] = item['post_title']
                msg['post_body'] = item['post_body']
                # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
                temp_msg_pool2 = ['Which of the following options would be the right one?',
                                  'Could you choose an option to fill in the blank?',
                                  'Which word(s) may fit the sentence according to the UI example?',
                                  'Which option would come from the original critique?']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = '\"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
                ## Ask Question (first question of an UI example)
                msg['options'].append('I don\'t know.')
                msg['options'].append('I need a hint.')
                msg['state'] = 'Ask Question'
                tutor_msg.append(msg)

        if state == 'Query Visual Element' and user_message != 'Next Question!' and user_message != 'I want to explore an UI component.':
            # Decide next UI feedback-request post based on the input user element.
            msg = copy.deepcopy(msg_example)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            question_ids = user_info['question_ids']
            query_results = query_results = search_question(user_message, type='design_element')
            item = {}
            query_flag = False
            for temp in query_results:
                if temp['question_id'] not in question_ids:
                    item = temp
                    query_flag = True
                    break
            if query_flag:
                # Tutor message (start)
                temp_msg_pool1 = ['Here are an UI example and a critique about visual element ',
                                  'I got a critique of an example for you about ',
                                  'Let\'s check this critique and example related to ']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1 + '\"' + user_message + '\".'
                msg['state'] = 'Begin Next Question'
                # Add this message
                tutor_msg.append(msg)
                print('Tutor turn: Begin Next Question and Ask Question')

                msg = copy.deepcopy(msg_example)
                user_info = handle_user_info(data, data['user_id'])
                msg['user_id'] = user_info['user_id']
                msg['correct'] = user_info['correct']
                msg['total'] = user_info['total']
                # To do: Need to check if this question has appeared before
                # temp_index = random.randint(0, len(query_results) - 1)
                # item = query_results[temp_index]
                msg['post_id'] = item['post_id']
                msg['question_id'] = item['question_id']
                msg['cloze_test'] = item['question']
                msg['correct_answer'] = item['right_answer']
                msg['cloze_answer'] = item['right_answer']
                msg['explanation'] = item['explanation']
                msg['mention_ui_elements'] = item['mention_ui_elements']
                msg['answer_cluster'] = item['answer_cluster']
                msg['hint'] = item['hint']
                options = []
                options.append(item['other_option_1'])
                options.append(item['other_option_2'])
                options.append(item['right_answer'])
                arr = np.array([0, 1, 2])
                np.random.shuffle(arr)
                for i in arr:
                    msg['multiple_choices'].append(options[i])
                    msg['options'].append(options[i])
                # Prepare image link
                img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
                imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
                msg['imgs'].append(imgs)
                msg['post_title'] = item['post_title']
                msg['post_body'] = item['post_body']
                # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
                temp_msg_pool2 = ['Which of the following options would be the right one?',
                                  'Could you choose an option to fill in the blank?',
                                  'Which word(s) may fit the sentence according to the UI example?',
                                  'Which option would come from the original critique?']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = '\"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
                ## Ask Question (first question of an UI example)
                msg['options'].append('I don\'t know.')
                msg['options'].append('I need a hint.')
                msg['state'] = 'Ask Question'
                tutor_msg.append(msg)
            else:
                # Tutor message (start)
                temp_msg_pool1 = ['Sorry, I do not have more critiques with ui component keyword ',
                                  'Sorry, the critique pool from the community does not have questions with ',
                                  'Sorry, there is no more question in the critique pool with ']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                temp_msg_pool2 = ['How about this one?',
                                  'Would you like to try this one?',
                                  'Let\'s check this one instead!']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = temp_msg_1 + '\"' + user_message + '\".' + temp_msg_2
                msg['state'] = 'Begin Next Question'
                # Add this message
                tutor_msg.append(msg)
                print('Tutor turn: Begin Next Question and Ask Question')

                msg = copy.deepcopy(msg_example)
                user_info = handle_user_info(data, data['user_id'])
                msg['user_id'] = user_info['user_id']
                msg['correct'] = user_info['correct']
                msg['total'] = user_info['total']
                query_results = search_question('', cluster='color_design', type='design_element')
                # To do: Need to check if this question has appeared before
                temp_index = random.randint(0, len(query_results) - 1)
                item = query_results[temp_index]
                msg['post_id'] = item['post_id']
                msg['question_id'] = item['question_id']
                msg['cloze_test'] = item['question']
                msg['correct_answer'] = item['right_answer']
                msg['cloze_answer'] = item['right_answer']
                msg['explanation'] = item['explanation']
                msg['mention_ui_elements'] = item['mention_ui_elements']
                msg['answer_cluster'] = item['answer_cluster']
                msg['hint'] = item['hint']
                # msg['ui_elements'] = item['ui_elements']
                options = []
                options.append(item['other_option_1'])
                options.append(item['other_option_2'])
                options.append(item['right_answer'])
                print(options)
                arr = np.array([0, 1, 2])
                np.random.shuffle(arr)
                for i in arr:
                    msg['multiple_choices'].append(options[i])
                    msg['options'].append(options[i])
                # Prepare image link
                img_link = 'http://' + image_server_url + item['ui_link'].split('\\')[1]
                imgs = {'src': img_link, 'alt': ''}  # https://i.redd.it/7bkyuit5deg91.jpg
                msg['imgs'].append(imgs)
                msg['post_title'] = item['post_title']
                msg['post_body'] = item['post_body']
                # msg['tutor_message'] = 'Please try to fill in the blank with a design concept in the following critique about this UI example. \n \"' + question + '\"'
                temp_msg_pool2 = ['Which of the following options would be the right one?',
                                  'Could you choose an option to fill in the blank?',
                                  'Which word(s) may fit the sentence according to the UI example?',
                                  'Which option would come from the original critique?']
                temp_msg_2 = temp_msg_pool2[random.randint(0, len(temp_msg_pool2) - 1)]
                msg['tutor_message'] = '\"<b>' + item['question'] + '</b>\"\n' + temp_msg_2
                ## Ask Question (first question of an UI example)
                msg['options'].append('I don\'t know.')
                msg['options'].append('I need a hint.')
                msg['state'] = 'Ask Question'
                tutor_msg.append(msg)

        ## Give Up
        if user_message == 'I don\'t know.' and (state == 'Ask Question' or state == 'Give Hint'):
            msg = copy.deepcopy(data)
            handle_user_info(data, data['user_id'])
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_msg_pool1 = ['Do you really want to give up?',
                              'Would you really like to give up?']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1
            print('Tutor turn: Give Up')
            # Generate options
            msg['options'] = ['No, I\'ll try again.', 'Yes, answer please.']
            msg['state'] = 'Give Up'
            tutor_msg.append(msg)

        ## Give Hint
        if (user_message == 'I need a hint.' and state == 'Ask Question') or (
                user_message == 'No, I\'ll try again.' and state == 'Give Up'):
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Link to external dataset using a function
            options = msg['multiple_choices']
            hints = msg['hint']

            temp_msg_pool1 = ['Here are more contexts about this critique:',
                              'More information from the original comment:',
                              'You can check more information about this critique:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1 + '\n' + hints
            print('Tutor turn: Give Hint')
            msg['options'] = msg['multiple_choices']
            if 'I don\'t know.' not in msg['options']:
                msg['options'].append('I don\'t know.')
            # msg['correct_answer'] = 'Right answer'
            msg['state'] = 'Give Hint'
            tutor_msg.append(msg)

        ## Confirm Give Up
        if user_message == 'Yes, answer please.' and state == 'Give Up':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_msg_pool1 = ['That\'s okay, you\'ll get it next time!',
                              'That\'s fine, you\'ll get it next time!',
                              'Don\'t worry, you\'ll know it next time!',
                              'No problem, you are going to learn it']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1
            msg['state'] = 'Confirm Give Up'
            print('Tutor turn: Confirm Give Up')
            tutor_msg.append(msg)
            showAnswer = True

        ## Check if answer is correct
        # In state 'Give Hint', user input is the multiple choice question
        if state == 'Give Hint' and user_message != 'I don\'t know.' and user_message != '':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            if user_message != data['correct_answer']:
                ## Incorrect Answer
                # Tutor message
                temp_msg_pool1 = ['I\'m sorry, that\'s not quite right.',
                                  'Oh, that\'s not quite right.',
                                  'Sorry, it seems not the right answer.',
                                  'I\'m sorry, that\'s not the most appropriate option.']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1
                msg['state'] = 'Incorrect Answer'
                tutor_msg.append(msg)
                print('Tutor turn: Give Hint and Incorrect Answer')
            else:
                ## Correct Answer
                # Tutor message
                temp_msg_pool1 = ['That\'s correct!',
                                  'You are right!',
                                  'Great! It\'s correct!',
                                  'Nice! You choose the right answer!',
                                  'Good!', 'Well done!', 'Nice choice!']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1
                msg['state'] = 'Correct Answer'
                tutor_msg.append(msg)
                print('Tutor turn: Give Hint and Correct Answer')
            showAnswer = True

        # In state 'Ask Question'
        if (
                state == 'Ask Question') and user_message != 'I don\'t know.' and user_message != 'I need a hint.' and user_message != '':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            if user_message != data['correct_answer']:
                ## Incorrect Answer
                # Tutor message
                temp_msg_pool1 = ['I\'m sorry, that\'s not quite right.',
                                  'Oh, that\'s not quite right.',
                                  'Sorry, it seems not the right answer.',
                                  'I\'m sorry, that\'s not the most appropriate option.']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1
                msg['state'] = 'Incorrect Answer'
                tutor_msg.append(msg)
                print('Tutor turn: Ask Question and Incorrect Answer')
            else:
                ## Correct Answer
                # Tutor message
                temp_msg_pool1 = ['That\'s correct!',
                                  'You are right!',
                                  'Great! It\'s correct!',
                                  'Nice! You choose the right answer!',
                                  'Good!', 'Well done!', 'Nice choice!']
                temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
                msg['tutor_message'] = temp_msg_1
                msg['state'] = 'Correct Answer'
                tutor_msg.append(msg)
                print('Tutor turn: Ask Question and Correct Answer')
            showAnswer = True

        ## Show Answer
        if showAnswer:
            msg = copy.deepcopy(data)
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_msg_pool1 = ['The correct answer is:',
                              'The word in the original comment is:',
                              'The right choice would be:',
                              'The correct choice is:',
                              'The answer should be:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1 + ' <b>' + data['correct_answer'] + '</b>'
            if state == 'Incorrect Answer':
                msg['options'] = ['Why?', 'Wait, I got it right!', 'Next Question!',
                                  'I want to explore an UI component.', 'I want to explore a visual element.']
            else:
                msg['options'] = ['Why?', 'Wait, it\'s not necessarily right!', 'Next Question!']
            msg['state'] = 'Show Answer'
            tutor_msg.append(msg)
            print('Tutor turn: Show Answer')

        ## Show Explanation
        if user_message == 'Why?' and state == 'Show Answer':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            temp_msg_pool1 = ['Here is the related comment summary:',
                              'Check the original comment from the community:',
                              'Check this comment summary:',
                              'This comment summary could help:',
                              'You can check this comment for more information:']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1
            tutor_msg.append(msg)

            msg = copy.deepcopy(data)
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            # Should collect from the tutor; try differentiate different types of sentences
            full_feedback = data['explanation']
            # Stylize the full_feedback here
            msg['tutor_message'] = full_feedback

            # Generate options
            msg['options'] = ['Next Question!', "Move Forward"]
            msg['state'] = 'Show Explanation'
            tutor_msg.append(msg)
            print('Tutor turn: Show Explanation')

        ## Report Answer
        if (
                user_message == 'Wait, I got it right!' or user_message == 'Wait, it\'s not necessarily right!') and state == 'Show Answer':
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            msg['tutor_message'] = 'Okay, I\'ll take a note of that. Thanks for the feedback!'
            # Generate options
            msg['options'] = ['Next Question!', 'I want to explore an UI component.',
                              'I want to explore a visual element.']
            msg['state'] = 'Report Answer'
            tutor_msg.append(msg)
            print('Tutor turn: Report Answer')

        # Query UI component
        if user_message == 'I want to explore an UI component.' and (
                state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query Visual Element'):
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_index = [random.randint(0, len(ui_element_pool) - 1) for _ in range(3)]
            temp_msg_pool1 = ['What’s the keyword of the UI component, e.g., ',
                              'Could you provide a keyword for the UI component, e.g., ',
                              'Which UI component would be your interested one, e.g., ']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1 + ui_element_pool[temp_index[0]] + ', ' + ui_element_pool[
                temp_index[1]] + ', ' + ui_element_pool[temp_index[2]] + '?'
            # Generate options
            msg['options'] = ['Next Question!']
            msg['state'] = 'Query UI Component'
            tutor_msg.append(msg)
            print('Tutor turn: Query UI Component')

        # Query Visual Element
        if user_message == 'I want to explore a visual element.' and (
                state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query UI Component'):
            msg = copy.deepcopy(data)
            user_info = handle_user_info(data, data['user_id'])
            msg['user_id'] = user_info['user_id']
            msg['correct'] = user_info['correct']
            msg['total'] = user_info['total']
            msg['sender'] = 'tutor'
            msg['direction'] = 'incoming'
            # Tutor message
            temp_index = [random.randint(0, len(visual_element_pool) - 1) for _ in range(3)]
            temp_msg_pool1 = ['What’s the keyword of the visual element, e.g., ',
                              'Could you provide a keyword for the visual element, e.g., ',
                              'Which visual element would be your interested one, e.g., ']
            temp_msg_1 = temp_msg_pool1[random.randint(0, len(temp_msg_pool1) - 1)]
            msg['tutor_message'] = temp_msg_1 + visual_element_pool[
                temp_index[0]] + ', ' + visual_element_pool[temp_index[1]] + ', ' + visual_element_pool[
                                       temp_index[2]] + '?'
            # Generate options
            msg['options'] = ['Next Question!', 'I want to explore an UI component.']
            msg['state'] = 'Query Visual Element'
            tutor_msg.append(msg)
            print('Tutor turn: Query Visual Element')

    return jsonify({'success': True, 'data': tutor_msg})


def a(keyword, group_id, user, headers):
    import requests
    import json

    url = "https://siomi.aichat83.com/go/api/steam/see"
    data = {
        "version": "1.1.1",
        "os": "pc",
        "channel": "chatos",
        "language": "zh",
        "pars": {
            "user_id": str(user),
            "question": str(keyword),
            "group_id": str(group_id),
            "question_id": "",
            "server_id": "1"
        }
    }

    data = json.dumps(data, separators=(',', ':'))
    response = requests.post(url, headers=headers, data=data)
    # #     print(response.text)
    #     # "mzgk2fvhr4o7aw8h+Nn/Q4Np/UwO4x8hHyBgcM3eFAO4RI/2dvfBZ5QJ/makTqmC05LeWyhc2DsEEHbg26aldagHXJOxk6IyLj1u3rbucvDIWO1FUnx4KlOA3XxZ6zKvEv8q+9u9M0pa5hhAY2xq8J7qPc8APDS25OxZ9K2f4QLE9FcNB4B5s6uSNjE="
    return response.text


def b(num, headers, group_id, user, token):
    result = ''
    import requests, json
    url = "https://api.aichat81.com/go/api/event/see"
    params = {
        "question_id": str(num),
        "group_id": group_id,
        "user_id": user,
        "token": token,
        "server_id": "1",
        "ctx": "open"
    }

    response = requests.get(url, headers=headers, params=params, stream=True)
    response.encoding = 'utf-8'
    # 检查响应状态码
    if response.status_code == 200:
        # 遍历响应内容，处理每一个事件
        for line in response.iter_lines(decode_unicode=True):
            # 在这里处理每一行的事件数据
            if line != 'event:message' and line:

                # 解析 JSON 格式数据
                try:
                    # 提取出 data 字段中的内容
                    data_start_index = line.find('{"Data"')
                    data_end_index = line.rfind('}')
                    data_str = line[data_start_index:data_end_index + 1]
                    data_dict = json.loads(data_str)

                    result = result + data_dict['Data']
                except:
                    # 提取出 data 字段中的内容
                    data_str = line.split('data:')[1]
                    # 解析 JSON 格式数据
                    data_dict = json.loads(data_str)
                    # 输出提取出的 data 内容
                    result = result + data_dict['Data']

                # 输出提取出的 data 内容
    else:
        print('Failed to subscribe to event stream:', response.status_code)
    return result


import pandas as pd


def select_token_group(file_path):
    """
    从Excel文件中读取token和groupid。

    参数:
    file_path (str): Excel文件的路径。

    返回:
    pd.DataFrame: 包含token和groupid的DataFrame。
    """
    try:
        # 使用pandas的read_excel函数读取Excel文件
        # 假设Excel文件中的工作表名为'Sheet1'，并且包含'token'和'groupid'列
        df = pd.read_excel(file_path, sheet_name='Sheet1')
        data = []
        for i in df.values:
            token = i[1]
            groupid = i[6]
            user = i[2]
            data.append({'token': token, 'groupid': groupid, 'user': user})
        return data
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None


def search_gpt(keyword):
    # 使用示例
    file_path = '/root/v2_agent/backend_quizzer/account.xlsx'  # 更改为你的Excel文件路径
    token_group_df = select_token_group(file_path)
    #     print(token_group_df)
    cookie = random.choice(token_group_df)
    #     print(cookie)
    json_data = {
        '日常聊天': cookie['groupid'],
    }
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Authorization': cookie['token'],
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://cat.chatavx.com',
        'Pragma': 'no-cache',
        'Referer': 'https://cat.chatavx.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    #     print(keyword)
    keyword = keyword  # '用python代码生成'+
    answer = a(keyword=keyword, group_id=cookie['groupid'], user=cookie['user'], headers=headers)

    def decrypt(response):
        # response = requests.post(url, headers=headers, data=data).text[1:-1]
        def decrypt_message(key, iv, ciphertext):
            backend = default_backend()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data.decode('utf-8')

        response = response[1:-1]
        r = response[16:]
        n = response[0:16]
        e = 'hj6cdzrhj72x8ht1'  # 你需要提供相关的初始化向量
        ciphertext = b64decode(r)
        key = n.encode('utf-8')
        iv = e.encode('utf-8')
        decrypted_message = decrypt_message(key, iv, ciphertext)
        #         print(decrypted_message)
        return json.loads(decrypted_message)

    #     print(answer)
    num = decrypt(answer)['data']['question_id']
    result = b(num, headers, cookie['groupid'], cookie['user'], cookie['token'])
    print(result)
    #     try:
    #         code = result.split('```python')[1].split('```')[0]
    #     except:
    #         print(result)
    return result


if __name__ == '__main__':
    app.run(debug=True)
