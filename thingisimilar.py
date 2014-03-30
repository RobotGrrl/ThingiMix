#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

#######################################
# Thingisimilar
#######################################
#
# Compares two things
# (still a work-in-progress)
# -------------------------------------
# By Erin RobotGrrl   March 28, 2014
# 
# RobotGrrl.com
#
# Released under the MIT License
# http://opensource.org/licenses/MIT
#######################################

import sys
import json
import random
import twitter
import schedule
from time import sleep
from textblob import TextBlob
from thingiverse import Thingiverse

DEBUG = False


# Twitter Info
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

api = twitter.Api(consumer_key = consumer_key,
				  consumer_secret = consumer_secret,
				  access_token_key = access_token,
				  access_token_secret = access_token_secret)


# Thingiverse Info
appinfo = {'client_id': '',
				'client_secret': '',
				'redirect_uri': ''}

thingiverse = Thingiverse(appinfo)


# Globals
thing = None
tweets = []
new_tweets = 0
total_score = 0
senti_val = 0
publish_tweet = False



test_things = [37926, # Blossoming Lamp by emmett
			   268401, # 28mm Scale Omnisphere by dutchmogul
			   214861, # Crazy Anime Lego Minifig Hair by RobotGrrl
			   275768, # mighty curcan migelo by TaggLee
			   112074] # Turtle Keychain by Nicolinux



#######
# Main
#######

def main():
	
	global thingiverse
	global twitter
	auto_mode = True

	if DEBUG: print 'welcome'
	thingiverse.DEBUG = False
	thingiverse.txt_url_mode = False
	thingiverse.connect()
	print api.VerifyCredentials().name
	print '\n\nThingisimilar\n'

	schedule.every(2).minutes.do(exploring)


	if auto_mode:
		#main_loop()

		exploring()
		while True:
			schedule.run_pending()
			sleep(1.0)

	else:
		#while True:
		#num1 = raw_input('#1 --> ')
		#num2 = raw_input('#2 -->')
		num1 = test_things[0]
		num2 = test_things[4]
		standard_job(int(num1), int(num2))



def exploring():

	beep1 = random_thing()

	while beep1 == 0:
		beep1 = random_thing()

	beep1 = beep1['id']

	beep2 = random_thing()

	while beep2 == 0:
		beep2 = random_thing()

	beep2 = beep2['id']

	print '1: %s' % (beep1)
	print '2: %s' % (beep2)

	standard_job(int(beep1), int(beep2))



def random_thing():

	global thingiverse

	new_things = thingiverse.get_newest_things()
	largest_id = new_things[0]['id']

	random_num = random.randint(0, int(largest_id))

	thing = thingiverse.get_thing(random_num)

	if 'error' in thing:
		print 'error'
		return 0
	else:
		return thing



def standard_job(num1, num2):

	global thingiverse
	global total_score
	global thing
	global senti_avg

	thing1 = thingiverse.get_thing(num1)
	thing2 = thingiverse.get_thing(num2)

	if 'error' in thing1:
		print 'error with #1'
	elif 'error' in thing2:
		print 'error with #2'
	else:


		# Noun phrase extraction (Name, Description, Instructions)

		noun_phrase_score = 0
		name_match_count = 0
		desc_match_count = 0
		instr_match_count = 0


		name_blob1 = TextBlob(thing1['name'])
		name_blob2 = TextBlob(thing2['name'])

		print 'name_blob1'
		print name_blob1.noun_phrases

		print '\n'

		print 'name_blob2'
		print name_blob2.noun_phrases

		for n1 in name_blob1.noun_phrases:
			for n2 in name_blob2.noun_phrases:
				if n1 == n2:
					print 'match! %s == %s' % (n1, n2)
					name_match_count += 1



		print '\n\n'

		desc_blob1 = TextBlob(thing1['description'])
		desc_blob2 = TextBlob(thing2['description'])

		print 'desc_blob1'
		print desc_blob1.noun_phrases

		print '\n'

		print 'desc_blob2'
		print desc_blob2.noun_phrases

		for d1 in desc_blob1.noun_phrases:
			for d2 in desc_blob2.noun_phrases:
				if d1 == d2:
					if d1 == 'customized' or d1 == 'created' or d1 == 'customizer':
						print 'a customizer one'
					else:
						print 'match! %s == %s' % (d1, d2)
						desc_match_count += 1
					


		print '\n\n'

		instr_blob1 = TextBlob(thing1['instructions'])
		instr_blob2 = TextBlob(thing2['instructions'])

		print 'instr_blob1'
		print instr_blob1.noun_phrases

		print '\n'

		print 'instr_blob2'
		print instr_blob2.noun_phrases

		for i1 in instr_blob1.noun_phrases:
			for i2 in instr_blob2.noun_phrases:
				if i1 == i2:
					print 'match! %s == %s' % (i1, i2)
					instr_match_count += 1


		print '\n\n'

		noun_phrase_score = name_match_count + desc_match_count + instr_match_count

		print 'name: %d, desc: %d, instr: %d' % (name_match_count, desc_match_count, instr_match_count)
		print 'noun_phrase_score score: %d' % (noun_phrase_score)
		




		# Tags
		
		thing_tags1 = thingiverse.get_thing_tags(num1)
		thing_tags2 = thingiverse.get_thing_tags(num2)

		tag_score = 0
		tag_match_count = 0

		print '\n'

		print 'tags1: %s' % (thing_tags1)
		print 'tags2: %s' % (thing_tags2)

		print '\n'

		for bloop1 in thing_tags1:
			for bloop2 in thing_tags2:
				tag1 = bloop1['name']
				tag2 = bloop2['name']
				print '%s vs %s' % (tag1, tag2)

				if tag1 == tag2:
					print 'match! %s %s' % (tag1, tag2)
					tag_match_count += 1

		tag_score = tag_match_count
		print 'tag_score score: %d' % (tag_score)





		# Category

		thing_cat1 = thingiverse.get_thing_category(num1)
		thing_cat2 = thingiverse.get_thing_category(num2)

		cat_score = 0

		print '\n'
		print 'cat1: %s' % (thing_cat1)
		print 'cat2: %s' % (thing_cat2)

		cat1 = thing_cat1[0]['name']
		cat2 = thing_cat2[0]['name']

		if cat1 == cat2:
			print 'match!'
			cat_score += 1

		print 'cat_score score: %d' % (cat_score)





		# Save it

		if noun_phrase_score > 0 or tag_score > 0 or cat_score > 0:

			thing1_id = thing1['id']
			thing2_id = thing2['id']

			# thing1, thing2, name matches, desc matches, instr matches, tag matches, cat matches
			s = '%s, %s, %d, %d, %d, %d, %d\n' % (thing1_id, thing2_id, name_match_count, desc_match_count, instr_match_count, tag_score, cat_score)

			f = open('matches_v2.txt', 'a')
			f.write(s)
			f.close()

			# for i in range(0, 5):
			# 	print('\a')
			# 	sleep(0.5)











def main_loop():
	global tweets

	tweets = _get_tweets() # initial loading of the tweets

	schedule.every(5).minutes.do(random_job)
	schedule.every(3).minutes.do(_trigger_tweet)
	schedule.every(2).minutes.do(tweet_job)

	# stream_tweets() # uncomment this line and comment out the two lines above it to use streaming api

	while True:
		schedule.run_pending()
		sleep(1.0)



#######
# Jobs
#######

def tweet_job():

	global thingiverse
	global twitter
	global thing
	global tweets
	global new_tweets
	global total_score

	#print '~'
	find_new_tweets()

	if new_tweets > 0:
		if DEBUG: print 'number of new tweets: %d' % (new_tweets)
		
		for i in range(0, new_tweets):
			
			print 'New tweet: %s (%d)' % (tweets[i].GetText(), tweets[i].GetId())

			num = parse_tweet(tweets[i].GetText())

			if num != 0:
				thing = thingiverse.get_thing(num)

				if 'error' in thing:
					s_id = tweets[i].GetId()
					s_name = tweets[i].GetUser().GetScreenName()
					send_tweet(s_id, s_name, 0)
				else:
					total_score = calculate_thing_score()
					
					s_id = tweets[i].GetId()
					s_name = tweets[i].GetUser().GetScreenName()
					send_tweet(s_id, s_name, 1)
					
		new_tweets = 0



def random_job():

	global thingiverse
	global total_score
	global thing
	global publish_tweet
	global senti_avg

	new_things = thingiverse.get_newest_things()
	largest_id = new_things[0]['id']

	random_num = random.randint(0, int(largest_id))

	thing = thingiverse.get_thing(random_num)

	if 'error' in thing:
		random_score_job()
	else:
		total_score = calculate_thing_score()
		_calculate_sentiment(thing['description'])
		
		if publish_tweet == True:
			send_tweet(None, None, 2)
			publish_tweet = False



#def standard_job(num):



def _trigger_tweet():
	global publish_tweet
	publish_tweet = True



#############
# New Tweets
#############

def find_new_tweets():

	global tweets
	global new_tweets

	s = _get_tweets()

	for i in range(0,10):

		if s[new_tweets].GetId() != tweets[new_tweets].GetId():
			if DEBUG: print 'new tweet'
			tweets.pop()
			tweets.insert(new_tweets, s[new_tweets])
			new_tweets += 1

			if new_tweets > 9:
				return
		else:
			return


def _get_tweets():

	global twitter

	while True:

		try:
			t = api.GetMentions()
		except twitter.TwitterError as e:
			if e[0][0]['code'] == 88:
				print 'Twitter rate limit error'
				sleep(5*60.0) # sleep for 5 mins
			else:
				_error_handle('_get_tweets -> GetMentions', e, True)
		except twitter.ConnectionError as e:
			_error_handle('_get_tweets -> GetMentions', e, True)
		except Exception as e:
			_error_handle('_get_tweets -> GetMentions', e, True)
		else:
			return t



##########################
# Thing Number from Tweet
##########################

def parse_tweet(raw_text):

	global twitter

	the_cmd = 'thingiscore'
	ind_a = raw_text.find(the_cmd)
	ind_b = ind_a
	ind_c = len(raw_text)-1
	slash_count = 0

	if ind_a == -1:
		print '--> did not find key word thingiscore'
		return 0

	for i in range(ind_a+len(the_cmd), len(raw_text)):

		if raw_text[i] == '/':
			slash_count += 1
			if slash_count == 2:
				# this is just the random number at the end of the tweet
				return 0

		if raw_text[i].isdigit():
			#print raw_text[i]
			if ind_b == ind_a: 
				ind_b = i
			else:
				ind_c = i

		if raw_text[i] == ' ':
			if ind_b > ind_a:
				ind_c = i-1
				break

	print 'ind_b: %d (%s) ind_c: %d (%s)' % (ind_b, raw_text[ind_b], ind_c, raw_text[ind_c])

	num = raw_text[ind_b:ind_c+1]
	if DEBUG: print 'parsed thing_id: %s' % (num)

	ret = 0
	try:
		ret = int(num)
	except ValueError as e:
		print '--> could not parse this tweet'
		return 0

	return int(num)



#####################
# Thing Calculations
#####################

def calculate_thing_score():
	
	global thingiverse
	global thing
	global total_score
	global senti_val

	thing_id = int(thing['id'])
	total_score = 0
	featured_score = 0
	like_score = 0
	file_score = 0
	desc_score = 0
	sentiment_score = 0
	wip_score = 0
	instructions_score = 0
	collect_score = 0
	derivative_score = 0
	ancestor_score = 0
	copies_score = 0

	if DEBUG: print '%s' % (thing['name'])

	for key, value in thing.items():
		
		if key == 'is_featured':
			if value == True:
				featured_score += 1000
			total_score += featured_score
			if DEBUG: print 'featured_score: %d' % (featured_score)

		elif key == 'like_count':
			like_score = value*20
			total_score += like_score
			if DEBUG: print 'like_score: %d' % (like_score)

		elif key == 'file_count':
			if value > 1:
				file_score += 500
			total_score += file_score
			if DEBUG: print 'file_score: %d' % (file_score)

		elif key == 'description':
			if len(value) >= 20:
				desc_score += 100
			total_score += desc_score
			if DEBUG: print 'desc_score: %d' % (desc_score)
			# TODO: sentiment value

		elif key == 'is_wip':
			if value == True:
				wip_score -= 50
			total_score += wip_score
			if DEBUG: print 'wip_score: %d' % (wip_score)

		elif key == 'instructions':
			if len(value) == 0:
				instructions_score -= 50
			total_score += instructions_score
			if DEBUG: print 'instructions_score: %d' % (instructions_score)

		elif key == 'collect_count':
			collect_score = value*5
			total_score += collect_score
			if DEBUG: print 'collect_score: %d' % (collect_score)
	

	derivs = thingiverse.get_thing_derivatives(thing_id)
	derivative_score = len(derivs)*100
	total_score += derivative_score
	if DEBUG: print 'derivative_score: %d' % (derivative_score)

	ances = thingiverse.get_thing_ancestors(thing_id)
	ancestor_score = len(ances)*5
	total_score += ancestor_score
	if DEBUG: print 'ancestor_score: %d' % (ancestor_score)

	copies = thingiverse.get_thing_copies(thing_id)
	copies_score = len(copies)*50
	total_score += copies_score
	if DEBUG: print 'copies_score: %d' % (copies_score)


	thing_files = thingiverse.get_thing_file(thing_id, None)
	total_thing_downloads = 0

	for i in range(0, len(thing_files)):
		thing_file_id = thing_files[i]['id']
		#print '%d: thing_file_id: %r' % (i, thing_file_id)
		specific_file = thingiverse.get_thing_file(thing_id, thing_file_id)
		file_downloads = specific_file['downloads']
		#print '%d: file_downloads: %r' % (i, file_downloads)
		total_thing_downloads += file_downloads

	download_score = total_thing_downloads*20
	total_score += download_score
	if DEBUG: print 'download_score %d' % (download_score)


	senti_val = _calculate_sentiment(thing['description'])

	if total_score >= 5000: _log_thing()


	if DEBUG: print 'TOTAL SCORE: %d\n' % (total_score)
	return total_score


def _calculate_sentiment(desc):
	desc_blob  = TextBlob(desc)
	senti = desc_blob.sentiment
	return senti.polarity



################
# Tweet Related
################

def send_tweet(status_id, screen_name, tw_type):

	tweet = _compose_tweet(tw_type, screen_name)

	try:
		if tw_type == 0:
			api.PostUpdate(tweet, None, None, None, None, False, False)

		elif tw_type == 1:
			api.PostUpdate(tweet, status_id, None, None, None, False, False)

		elif tw_type == 2:
			api.PostUpdate(tweet, None, None, None, None, False, False)

	except twitter.TwitterError as e:
		_error_handle('send_tweet -> PostUpdate', e, True)
	except twitter.ConnectionError as e:
		_error_handle('send_tweet -> PostUpdate', e, True)
	except Exception as e:
		_error_handle('send_tweet -> PostUpdate', e, True)



def _compose_tweet(tw_type, screen_name):

	global thing
	global total_score
	global senti_val
	

	# Error tweet
	if tw_type == 0:
		if thing['error'] == 'Not Found':
			tweet = '@%s Unable to find that thing //%d' % (screen_name, random.randrange(0, 100, 1))
		else:
			tweet = '@%s An error occured for that thing //%d' % (screen_name, random.randrange(0, 100, 1))
			print '!!!!! error'
			print thing
			print '\n'


	thing_name = thing['name']
	creator_name = thing['creator']['name']
	thing_url = thing['public_url']
	thing_desc = thing['description']

	if len(thing_name) > 45:
		thing_name = thing_name[0:45]
		thing_name += '[...]'


	senti_f = '['
	senti_s = 'Sentiment: '

	if senti_val >= -0.3 and senti_val <= 0.3:
		senti_f += '=]'
		senti_s += 'neutral'
	elif senti_val >= 0.3:
		senti_f += '+]'
		senti_s += 'positive'
	else:
		senti_f += '-]'
		senti_s += 'negative'


	# @user [+] name by name | Score: score | Sentiment: sent | url #thingiscore //num

	# In reply to
	if tw_type == 1:
		tweet = '@%s %s %s by %s\nScore: %d\n%s\n%s #thingiscore //%d' % (screen_name, senti_f, thing_name, creator_name, total_score, senti_s, thing_url, random.randrange(0, 100, 1))
		
	# Broadcast
	elif tw_type == 2:
		tweet = '%s %s by %s\nScore: %d\n%s\n%s #thingiscore //%d' % (senti_f, thing_name, creator_name, total_score, senti_s, thing_url, random.randrange(0, 100, 1))
		
	print tweet
	return tweet



#######
# Misc
#######

def stream_tweets():

	for item in api.GetStreamFilter(track=['@RobotGrrlDev', 'thingiscore'], stall_warning=True):
		if item.has_key('text'):
			print 'New tweet: %s - (%d)' % (item['text'], item['id'])
			num = parse_tweet(item['text'])

			if num != 0:
				thing = thingiverse.get_thing(num)

				if 'error' in thing:
					send_tweet(item['id'], item['user']['screen_name'], 0)
				else:
					total_score = calculate_thing_score()
					send_tweet(item['id'], item['user']['screen_name'], 1)



def _log_thing():

	global thing
	global total_score

	f = open('highscores.txt', 'a')

	thing_id = thing['id']
	thing_url = thing['public_url']
	thing_name = thing['name']
	creator_name = thing['creator']['name']

	s = '%s, %d, %s, %s, %s\n' % (thing_id, total_score, thing_name, creator_name, thing_url)

	f.write(s)

	f.close()



def _error_handle(func_name, e, do_exit):
	print '!!! an error occured in %s' % (func_name)
	print e
	if do_exit: sys.exit()



if __name__ == "__main__":
    main()



# python-twitter useful 'documentation'
# https://github.com/bear/python-twitter/blob/db5fcf0a98ad6ba2bc92f65ae5560f21de4c842a/twitter/status.py
# https://github.com/bear/python-twitter/blob/db5fcf0a98ad6ba2bc92f65ae5560f21de4c842a/twitter/user.py
