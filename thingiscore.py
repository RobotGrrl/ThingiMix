#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

#######################################
# Thingiscore
#######################################
#
# Creates an arbitrary score of a thing
# using the Thingiverse API
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


# Uncomment for Beaglebone Black
# Also need to uncomment lines in main_loop()
# import Adafruit_BBIO.GPIO as GPIO
# led = 'P9_16'
# led_on = True
# GPIO.setup(led, GPIO.OUT)
# GPIO.output(led, GPIO.HIGH)


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
	print '\n\nThingiscore\n'

	if auto_mode:
		main_loop()
	else:
		while True:
			num = raw_input('--> ')
			standard_job(int(num))



def main_loop():
	global tweets

	# Uncomment for BBB
	# global led_on
	# global led


	tweets = _get_tweets() # initial loading of the tweets

	schedule.every(15).minutes.do(_trigger_tweet)
	schedule.every(15).minutes.do(random_job)
	schedule.every(2).minutes.do(tweet_job)

	# stream_tweets() # uncomment this line and comment out the two lines above it to use streaming api

	while True:
		schedule.run_pending()

		# Uncomment for BBB
		# if led_on == True:
		# 	GPIO.output(led, GPIO.LOW)
		# 	led_on = False
		# else:
		# 	GPIO.output(led, GPIO.HIGH)
		# 	led_on = True

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
			
			print 'New tweet: %s (%d)' % (tweets[i].GetText().decode('utf-8', 'ignore'), tweets[i].GetId())

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
		random_job()
	else:
			total_score = calculate_thing_score()
		
		if publish_tweet == True:
			send_tweet(None, None, 2)
			publish_tweet = False



def standard_job(num):

	global thingiverse
	global total_score
	global thing
	global senti_avg

	thing = thingiverse.get_thing(num)

	if 'error' in thing:
		print 'error fetching that thing'
	else:
		total_score = calculate_thing_score()
		
		thing_name = thing['name']
		creator_name = thing['creator']['name']
		thing_url = thing['public_url']
		thing_desc = thing['description']

		_calculate_sentiment(thing_desc)

		stringy = _compose_tweet(2, None)
		print stringy
		print '\n'



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
		tweet = '@%s %s %s by %s\n--> Score: %d #thingiscore\n%s //%d' % (screen_name, senti_f, thing_name, creator_name, total_score, thing_url, random.randrange(0, 100, 1))
		
	# Broadcast
	elif tw_type == 2:
		tweet = '%s %s by %s\n--> Score: %d #thingiscore\n%s //%d' % (senti_f, thing_name, creator_name, total_score, thing_url, random.randrange(0, 100, 1))

	print tweet.decode('utf-8', 'ignore')
	return tweet



#######
# Misc
#######

def stream_tweets():

	for item in api.GetStreamFilter(track=['@RobotGrrlDev', 'thingiscore'], stall_warning=True):
		if item.has_key('text'):
			print 'New tweet: %s - (%d)' % (item['text'].decode('utf-8', 'ignore'), item['id'])
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
