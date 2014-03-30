#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

#######################################
# Thinginew
#######################################
#
# Watches for new things on the
# Thingiverse API feed
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
import schedule
import twitter
import random
from time import sleep
from textblob import TextBlob
from thingiverse import Thingiverse

DEBUG = False


# Uncomment for Beaglebone Black
# Also need to uncomment lines in main()
# import Adafruit_BBIO.GPIO as GPIO
# led = 'P9_42'
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
new_count = 0
things = [ [], [], [], [], [] ] # thing id, user id, thing name, creator name, thing url
score_cats = {}
update_count = 0
senti_avg = 0
seen_count = 0



#######
# Main
#######

def main():
	
	global thingiverse
	global new_count
	global things
	global update_count
	global twitter
	global led_pin
	global led_on
	
	# Uncomment for BBB
	# global led_on
	# global led


	if(DEBUG): print 'welcome'	
	thingiverse.DEBUG = False
	thingiverse.txt_url_mode = False
	thingiverse.connect()
	print api.VerifyCredentials().name
	print '\n\nThinginew\n'

	schedule.every(5).minutes.do(refresh_things_job)
	schedule.every(30).minutes.do(send_update_job)
	
	initialize_list()
	refresh_things_job()

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

def refresh_things_job():

	global new_count
	global seen_count
	global things
	global update_count

	find_new()

	if new_count > 0:
		for i in range(0, new_count):
			s1 = '%d: %s (%s) by %s\n%s' % (seen_count, things[2][i], things[0][i], things[3][i], things[4][i])
			print s1.decode('utf-8', 'ignore')
			category_counter(int(things[0][i]))
			seen_count += 1
			update_count += 1
		new_count = 0


def send_update_job():

	global update_count
	global senti_avg
	global twitter

	if update_count == 0:
		print 'nuttin new!'
		return


	# Creating tweet string components

	str_s = find_largest_category()

	str_u = '%d new things!' % (update_count)

	senti_avg /= update_count

	str_f = '['
	str_a = 'Avg sentiment: '

	if senti_avg >= -0.3 and senti_avg <= 0.3:
		str_f += '=]'
		str_a += 'neutral'
	elif senti_avg >= 0.3:
		str_f += '+]'
		str_a += 'positive'
	else:
		str_f += '-]'
		str_a += 'negative'


	# Sending the tweet

	tweet = '%s %s #thinginew\n%s\n%s //%d' % (str_f, str_u, str_a, str_s, random.randrange(0, 100, 1))

	if len(tweet) > 140:
		meep = str_s[0:20]
		meep += ' [...]'
		tweet = '%s %s #thinginew\n%s\n%s //%d' % (str_f, str_u, str_a, meep, random.randrange(0, 100, 1))

		if len(tweet) > 140:
			meep = str_s[0:5]
			meep += ' [...]'
			tweet = '%s %s #thinginew\n%s\n%s //%d' % (str_f, str_u, str_a, meep, random.randrange(0, 100, 1))

	try:
		api.PostUpdate(tweet, None, None, None, None, False, False)
	except twitter.TwitterError as e:
		error_handle('send_update -> PostUpdate', e, False)
	except twitter.ConnectionError as e:
		error_handle('send_update -> PostUpdate', e, False)
	except Exception as e:
		error_handle('send_update -> PostUpdate', e, False)
		
	print '\n%s\n' % (tweet.decode('utf-8', 'ignore'))

	update_count = 0
	senti_avg = 0



#############
# Categories
#############
	
def category_counter(thing_id):

	global thingiverse
	global score_cats


	# add 1 to the category score counter
	for cat in thingiverse.get_thing_category(thing_id):
		cat_name = cat['name']

		try:
			score_cats[cat_name] += 1
		except KeyError:
			score_cats[cat_name] = 0
			score_cats[cat_name] += 1



def find_largest_category():

	global score_cats

	list_cats = score_cats.items()

	if len(list_cats) == 0:
		#print 'nuttin here!'
		return
	elif len(list_cats) == 1:
		print 'why1'
		str_s = 'Most popular category: %s' % (list_cats[0][0])
		score_cats = {}
		return str_s

	largest = []
	max_val = list_cats[0][1]
	str_s = ''
	

	# find the largest value
	for i in range(0, len(list_cats)):
		val = list_cats[i][1]

		if val > max_val:
			max_val = val


	# add the tuples with the largest value to the list
	for i in range(0, len(list_cats)):
		val = list_cats[i][1]

		if val == max_val:
			largest.append(list_cats[i])


	# compose the string
	if len(largest) < 2:
		print 'why2'
		str_s = 'Most popular category: %s' % (largest[0][0])
	else:
		str_s = 'Most popular categories: '

		for i in range(0, len(largest)):
			str_s += '%s' % (largest[i][0])
			if i < len(largest)-1:
				str_s += ', '


	#print str_s

	# reset score afterwards
	score_cats = {}
	
	return str_s



###############
# Things Lists
###############

def find_new():

	global thingiverse
	global new_count
	global things

	thing_id = ''
	user_id = ''
	thing_name = ''
	user_name = ''
	thing_url = ''
	thing_desc = ''

	try:
		new_things = thingiverse.get_newest_things()
	except ValueError as e:
		print e
		if DEBUG: print 'well aw crap'
		return


	for i in range(0, 10):

		new = new_things[new_count]

		for key, value in new.items():
			if key == 'id':
				thing_id = value
			elif key == 'name':
				thing_name = value
			elif key == 'public_url':
				thing_url = value
			elif key == 'description':
				thing_desc = value
			elif key == 'creator':
				for key2, value2 in value.items():
					if key2 == 'id':
						user_id = value2
					elif key2 == 'name':
						user_name = value2


		if thing_id != things[0][new_count]:
			if DEBUG: print 'new count: %d, new thing: %s, old thing_id: %s' % (new_count, thing_id, things[0][new_count])

			calculate_sentiment(thing_desc)

			for bloop in things[0]:
				if thing_id == bloop:
					if DEBUG: print 'this is clearly a false alarm'
					return

			things[0].pop()
			things[1].pop()
			things[2].pop()
			things[3].pop()
			things[4].pop()
			
			things[0].insert(new_count, thing_id)
			things[1].insert(new_count, user_id)
			things[2].insert(new_count, thing_name)
			things[3].insert(new_count, user_name)
			things[4].insert(new_count, thing_url)

			new_count+=1

			if new_count > 9:
				return

		else:
			return



def initialize_list():

	global thingiverse
	global things
	
	thing_id = ''
	user_id = ''
	thing_name = ''
	user_name = ''
	thing_url = ''

	for i in range(0, 10):
		new = thingiverse.get_newest_things()[i]

		for key, value in new.items():
			if key == 'id':
				thing_id = value
			elif key == 'name':
				thing_name = value
			elif key == 'public_url':
				thing_url = value
			elif key == 'creator':
				for key2, value2 in value.items():
					if key2 == 'id':
						user_id = value2
					elif key2 == 'name':
						user_name = value2

		things[0].append(thing_id)
		things[1].append(user_id)
		things[2].append(thing_name)
		things[3].append(user_name)
		things[4].append(thing_url)



###############
# Calculations
###############

def calculate_sentiment(desc):

	global senti_avg

	desc_blob  = TextBlob(desc)
	senti = desc_blob.sentiment
	senti_avg += senti.polarity



#######
# Misc
#######

def error_handle(func_name, e, do_exit):
	print '!!! an error occured in %s' % (func_name)
	print e
	if do_exit: sys.exit()


if __name__ == "__main__":
    main()
