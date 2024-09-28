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

onlyfiles = [f for f in listdir('./tutor_data1/image1/') if isfile(join('./tutor_data1/image1/', f))]
print(len(onlyfiles))
post_ids = [img_path.split('.')[0] for img_path in onlyfiles]

ui_element_pool = []
visual_element_pool = []
with open('./all_ui_elements.json', 'r') as f:
	ui_element_pool = json.load(f)
with open('./all_visual_elements.json', 'r') as f:
	visual_element_pool = json.load(f)

msg_example = { # the tutor and the user side use similar format of msg
	'message': 'User message from client',
	'tutor_message': "Tutor\'s message from server",
	'user_id': '', # assigned by the server
	'isImage': False,
	'imgs': [],
	# 'payload': {src: '', alt: '', width: ''},
	'state': "dialog state",
	'sender': "tutor",
	'options': [],
	'sentTime': "just now",
	'direction': "incoming",
	'cloze_test': '',
	'multiple_choices': [],
	'explanation': '',
	'correct_answer': '',
	'post_id': '',
	'mention_ui_elements': [],
	'wiki': [],
	'post_id': 'none'
}

def handle_user_info(msg, user_id, user_file = './user_record.json'):
	user_data = []
	return_user_id = user_id
	post_ids = []
	question_ids = []
	with open(user_file, 'r') as f:
		user_data = json.load(f)
	if msg == '':
		user_data.append({
			'user_id': len(user_data),
			'questions': [],  # 所有回答过的question information
			'correct': 0,  # 记录回答正确的条数
			'total': 0,  # 记录总共回答过的条数
		})
		return_user_id = len(user_data) - 1
	else:
		utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
		beijing_now = utc_now.astimezone(SHA_TZ)
		msg['time_stamp'] = str(beijing_now) + str(beijing_now.tzname())
		user_data[user_id]['questions'].append(msg)
		if (msg['state'] == 'Give Hint' and msg['message'] != 'I don\'t know.' and msg['message'] != '') or ((msg['state'] == 'Ask Question') and msg['message'] != 'I don\'t know.' and msg['message'] != 'I need a hint.' and msg['message'] != ''):
			# print('##### Enter here ############')
			user_data[user_id]['total'] = user_data[user_id]['total'] + 1
			if msg['message'] == msg['correct_answer']:
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


image_server_url = '127.0.0.1:3004/'
@app.route('/', methods = ["GET", "POST"])
def index():
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

		tutor_msg = []

		### Prepare tutor msgs here
		## Self-introduction:
		if user_message == 'Cool, but how?':
			msg = copy.deepcopy(msg_example)
			msg['tutor_message'] = 'I will ask you <b>multiple-choice</b> questions about critiques of the UI feedback-request post (on the right panel) from r/UI_Design.'
			msg['state'] = 'Self Introduction'
			tutor_msg.append(msg)
			msg = copy.deepcopy(msg_example)
			msg[
				'tutor_message'] = 'You can choose the options below my message and input your interested UI or visual element when needed.'
			msg['state'] = 'Self Introduction'
			tutor_msg.append(msg)

			msg['options'].append('Got it. Let\'s go!')



		## Begin Next Question:
		if user_message == 'Got it. Let\'s go!' or user_message == 'Another UI Example!':
			# Tutor message (start)
			msg = copy.deepcopy(msg_example)
			msg['tutor_message'] = 'Here\'s an UI example for you.'
			msg['state'] = 'Begin Next Question'
			# Add this message
			tutor_msg.append(msg)
			print('Tutor turn: Begin Next Question and Ask Question')
			# print('checkpoint')
			msg = copy.deepcopy(msg_example)
			query_results = search_question('', cluster='format_design', type='design_element')
			# To do: Need to check if this question has appeared before
			# Assign user_id:
			user_info = handle_user_info('', '')
			msg['user_id'] = user_info['user_id']
			msg['correct'] = user_info['correct']
			msg['total'] = user_info['total']
			temp_index = random.randint(0, len(query_results) - 1)
			item = query_results[temp_index]
			msg['post_id'] = item['post_id']
			msg['question_id'] = item['question_id']
			msg['cloze_test'] = item['question']
			msg['correct_answer'] = item['right_answer']
			msg['cloze_answer'] = item['right_answer']
			msg['explanation'] = item['explanation']
			msg['mention_ui_elements'] = list(item['mention_ui_elements'])
			msg['answer_cluster'] = item['answer_cluster']
			msg['hint'] = item['hint']
			msg['wiki'] = []
			options = []
			options.append(item['other_option_1'])
			options.append(item['other_option_2'])
			options.append(item['right_answer'])
			# print(options)

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

		## Ask Question (another question of the same UI example)
		if user_message == 'Next Question!' and (state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query UI Component' or state == 'Query Visual Element'):
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
			query_results = search_question('', post_id=data['post_id'], cluster='format_design', type='design_element')
			item = {}
			query_flag = False
			for temp in query_results:
				if temp['question_id'] not in question_ids:
					item = temp
					query_flag = True
					break
			if not query_flag:
				query_results = search_question('', cluster='format_design', type='design_element')
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
				query_results = search_question('', cluster='format_design', type='ui_element')
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

			# Check if the same post has another unasked question
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
				query_results = search_question('', cluster = 'layout_design', type='design_element')
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
		if (user_message == 'I need a hint.' and state == 'Ask Question') or (user_message == 'No, I\'ll try again.' and state == 'Give Up'):
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

		showAnswer = False
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
		if (state == 'Ask Question') and user_message != 'I don\'t know.' and user_message != 'I need a hint.' and user_message != '':
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
				msg['options'] = ['Why?', 'Wait, I got it right!', 'Next Question!', 'I want to explore an UI component.', 'I want to explore a visual element.']
			else:
				msg['options'] = ['Why?', 'Wait, it\'s not necessary right!', 'Next Question!',
								  'I want to explore an UI component.',
								  'I want to explore a visual element.']
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
			msg['options'] = ['Next Question!', 'I want to explore an UI component.', 'I want to explore a visual element.']
			msg['state'] = 'Show Explanation'
			tutor_msg.append(msg)
			print('Tutor turn: Show Explanation')

		## Report Answer
		if (user_message == 'Wait, I got it right!' or user_message == 'Wait, it\'s not necessary right!') and state == 'Show Answer':
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
			msg['options'] = ['Next Question!', 'I want to explore an UI component.', 'I want to explore a visual element.']
			msg['state'] = 'Report Answer'
			tutor_msg.append(msg)
			print('Tutor turn: Report Answer')

		# Query UI Component
		if user_message == 'I want to explore an UI component.' and (state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query Visual Element'):
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
			msg['options'] = ['Next Question!', 'I want to explore a visual element.']
			msg['state'] = 'Query UI Component'
			tutor_msg.append(msg)
			print('Tutor turn: Query UI Component')

		# Query Visual Element
		if user_message == 'I want to explore a visual element.' and (state == 'Show Answer' or state == 'Show Explanation' or state == 'Report Answer' or state == 'Query UI Component'):
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

		
if __name__ == '__main__':
	app.run(debug=True)