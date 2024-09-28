import json
import random
from os import listdir
from os.path import isfile, join
onlyfiles = [f for f in listdir('./tutor_data2/image1/') if isfile(join('./tutor_data2/image1/', f))]
with open('./question_base/question_pool2/pool2.json', 'r') as f: # see data_stats.py in /tutor_data1 for more information #./tutor_data1/UI_Design.json  ./question_base/question_pool2/pool2.json
    all_ui_data = json.load(f)
print(len(all_ui_data))
# print(onlyfiles)
print(len(onlyfiles))
post_ids = [img_path.split('.')[0] for img_path in onlyfiles]

ui_data = []
all_comments = []
all_critique = []
all_suggestion = []
all_rationale = []
all_ui_elements = []
all_concepts = []
ui_comments = []
ui_critique = []
ui_suggestion = []
ui_rationale = []
ui_ui_elements = []
ui_concepts = []
questions = []
for ui_post in all_ui_data:
	for question in ui_post['questions']:
		questions.append(question)
	for com in ui_post['comments']:
		all_comments.append(com)
	if ui_post['ui_link'] != "":
		if ui_post['post_id'] in post_ids:
			ui_data.append(ui_post)
			for com in ui_post['comments']:
				ui_comments.append(com)
print('# of ui feedback-request posts: {}'.format(len(all_ui_data)))
print('# of ui feedback-request posts with UI link: {}'.format(len(ui_data)))
print('# of questions: {}'.format(len(questions)))
print('# of comments under ui feedback-request posts: {}'.format(len(all_comments)))
print('# of comments under ui feedback-request posts with UI link: {}'.format(len(ui_comments)))

for com in all_comments:
	for cri in com['critique']:
		all_critique.append(cri)
		for concept in cri['concepts']:
			all_concepts.append(concept)
		for element in cri['ui_elements']:
			all_ui_elements.append(element)
	for sug in com['suggestion']:
		all_suggestion.append(sug)
		for concept in sug['concepts']:
			all_concepts.append(concept)
		for element in sug['ui_elements']:
			all_ui_elements.append(element)
	for rat in com['rationale']:
		all_rationale.append(rat)
		for concept in rat['concepts']:
			all_concepts.append(concept)
		for element in rat['ui_elements']:
			all_ui_elements.append(element)
print('# of critique of all comments: {}'.format(len(all_critique)))
print('# of suggestion of all comments: {}'.format(len(all_suggestion)))
print('# of rationale of all comments: {}'.format(len(all_rationale)))
print('# of ui elements of all comments: {}'.format(len(all_ui_elements)))
print('# of design concepts of all comments: {}'.format(len(all_concepts)))

for com in ui_comments:
	for cri in com['critique']:
		ui_critique.append(cri)
		for concept in cri['concepts']:
			ui_concepts.append(concept)
		for element in cri['ui_elements']:
			ui_ui_elements.append(element)
	for sug in com['suggestion']:
		ui_suggestion.append(sug)
		for concept in sug['concepts']:
			ui_concepts.append(concept)
		for element in sug['ui_elements']:
			ui_ui_elements.append(element)
	for rat in com['rationale']:
		ui_rationale.append(rat)
		for concept in rat['concepts']:
			ui_concepts.append(concept)
		for element in rat['ui_elements']:
			ui_ui_elements.append(element)
print('# of critique of ui comments: {}'.format(len(ui_critique)))
print('# of suggestion of ui comments: {}'.format(len(ui_suggestion)))
print('# of rationale of ui comments: {}'.format(len(ui_rationale)))
print('# of ui elements of ui comments: {}'.format(len(ui_ui_elements)))
print('# of design concepts of ui comments: {}'.format(len(ui_concepts)))


def get_post(index, post_id=''):
	# Currently can get by index, as the data is stored in an array format
	return ui_data[index]

design_concepts = ['visual_design', 'format_design', 'color_design', 'layout_design']
def extract_question(index, post_id='', design_concept=''):
	while True:
		post_info = get_post(index)
		index += 1
		if len(post_info['mentioned_concept_clusters']) > 0:

			comments = post_info['comments']
			mentioned_ui_elements_clusters = post_info['mentioned_ui_elements_clusters']
			mentioned_concept_clusters = post_info['mentioned_concept_clusters']
			random_concept_index = random.randint(0, len(mentioned_concept_clusters) - 1)
			target_concept = mentioned_concept_clusters[random_concept_index]
			print(len(comments))
			select_comment = ''
			select_critique = ''
			select_concept = ''
			other_options = []
			flag = False
			# Select a comment based on some criteria
			for comment in comments:
				if len(comment['critique']) > 0:
					for critique in comment['critique']:
						if len(critique['concepts']) > 0:
							for concept in critique['concepts']:
								if concept['cluster'] == target_concept:
									select_comment = comment
									select_concept = concept
									select_critique = critique
								else:
									if len(other_options) < 2:
										other_options.append(concept['name']) # Need better design, otherwise the options are always the same two
								if select_comment != '' and len(other_options) == 2:
									flag = True
									break
						if flag:
							break
				if flag:
					break
			print(flag)
			if flag and select_comment != '':
				critique_sentence = select_critique['sentence']
				# Select the critique sentence and replace the 'design concept' with the '________'
				cloze_test = critique_sentence.replace(select_concept['name'], '______', 1)
				cloze_answer = select_concept['name']

				return {'cloze_test': cloze_test,
						'cloze_answer': cloze_answer,
						'other_options': other_options,
						'explanation': select_comment['comment_summary'], # explanation for this sentence (the summarized comment content?)
						'comment': select_comment,
						'post': post_info,
						'post_index': index - 1
						}
		if index >= len(ui_data):
			return {'cloze_test': '',
					'cloze_answer': '',
					'other_options': '',
					'explanation': '', # explanation for this sentence (the summarized comment content?)
					'comment': '',
					'post': '',
					'post_index': index - 1
					}

# print(get_post(4))
# result = extract_question(4)
# print(result)





