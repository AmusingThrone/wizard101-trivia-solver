from pathlib import Path
import json
import time
import getpass
import sys
import random
import traceback
import difflib
import requests
import base64
import re
from bs4 import BeautifulSoup

FREEKI_GAMES_LOGIN = "https://www.freekigames.com/auth/popup/login.theform"
FREEKI_HOME_PAGE = "https://www.freekigames.com/"
FREEKI_GAMES_WIZARD_101_TRIVIA = "https://www.freekigames.com/wizard101-trivia"
FREEKIGAMES_QUIZFORM = "https://www.freekigames.com/freegameslanding.freekigames.quizform.quizform"
CAPTCHA_IMAGE_URL = "https://www.freekigames.com/Captcha?mode=ua"
CAPTCHA_POST_URL = "https://www.freekigames.com/auth/popup/loginwithcaptcha.captcha.captcha:internalevent"
CAPTCHA_API = ""
CAPTCHA_URL = "https://www.freekigames.com/auth/popup/LoginWithCaptcha/freekigames?fpSessionAttribute=QUIZ_SESSION"
CROWN_URL = "https://www.freekigames.com/auth/popup/loginwithcaptcha.theform"
FILENAME = "captcha.png"

headers = {
		   'Host': 'www.freekigames.com',
		   'Origin': 'https://www.freekigames.com',
		   'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.1 Safari/605.1.15',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'en-us',
           'DNT': '1'
           }


def log(message, type="log"):
	if type == "log":
		print("[%] " + message)
	elif type == "error":
		print("[!] " + message)
	elif type == "confirm":
		input("[>] " + message)


def login(username, password):
	global connection
	with requests.Session() as connection:
		connection.get(FREEKI_GAMES_LOGIN, headers=headers)
		soup = connection.get(FREEKI_GAMES_LOGIN, headers=headers).text
		soup = BeautifulSoup(soup, 'lxml')
		tac = soup.find('input', {'name': 't:ac'}).get('value')
		tform = soup.find('input', {'name': 't:formdata'}).get('value')

		login_data = {'t:ac': tac, 't:submit': 'login', 'stk': '', 't:formdata': tform, 'targetPopup': False,
                    'targetURL': FREEKI_HOME_PAGE, 'userName': username, 'password': password, 'login': ''}

		login = connection.post(FREEKI_GAMES_LOGIN, data=login_data)

		cookies = connection.cookies.get_dict()
		if 'stk' in cookies:
			log("Successfully logged in.")
		else:
			log("Invalid credentials provided. Unable to login.", "error")
			sys.exit()


def get_solvable_trivias(trivia_page):
	soup = connection.get(trivia_page, headers=headers).text
	soup = BeautifulSoup(soup, 'lxml')
	trivias_elements = soup.find("div", {"class": "gamevert_3column"}).find(
            "ul", recursive=False).findAll("li", recursive=False)
	log("Gathering trivias.")
	trivias = []
	for trivia in trivias_elements:
		if trivia.get("class")[0] != "notake":
			trivias.append([trivia.find("div", {"class": "gamename"}).text, trivia.find("div", {"class": "thumb"}).find(
                            "a", recursive=False).get('href')])
		else:
			log("Skipping \"{}\", already taken.".format(trivia.find("div", {"class": "gamename"}).text), "error")
	log("Found {} possible trivias.".format(len(trivias)))
	return trivias

def solve_trivias(trivias, trivia_data):
	log("Loaded answers for {} trivias.".format(len(trivia_data.keys())))
	for trivia in trivias:
		if trivia[0] in trivia_data.keys():
			url = trivia[1]
			trivia_answers = trivia_data[trivia[0]]
			log("Attempting to solve \"{}\".".format(trivia[0]))

			soup = connection.get(url, headers=headers).text
			soup = BeautifulSoup(soup, 'lxml')
			pattern = re.compile('var\s+quizId\s+=\s+(.*);')
			tac = soup.find('input', {'name': 't:ac'}).get('value').strip()
			tform = soup.find("div", {"id": "quizFormComponent"}).find('input', {'name': 't:formdata'}).get('value').strip()
			for script in soup.find_all("script", {"src": False}):            
				if script:
					m = pattern.search(script.string)
					if m is not None:
						quiz_id = m.group(1).replace('"', "").strip()

			soup = connection.get(url, headers=headers).text
			for x in range(12):
				soup = BeautifulSoup(soup, 'lxml')

				cookie_dict = connection.cookies.get_dict()
				question = soup.find("div", {"class": "quizQuestion"}).text.strip()
				question_id = soup.find('input', {'name': 'questionId'}).get('value').strip()
				answers_elements = soup.findAll("div", {"class": "answer"})
				answers = []
				for answer in answers_elements:
					answers.append(answer.find("span", {"class": "answerText"}).text.strip())
				
				if question in trivia_answers:
					if trivia_answers[question] in answers:
						answer_id = answers_elements[answers.index(trivia_answers[question])]
						answer_id = answer_id.find('input', {'name': 'answers'}).get('value').strip()
					else:
						log("Guessing on question (could not find answer): \"{}\"".format(question), "error")
						log("Answer Choices: 1. \"{}\" 2. \"{}\" 3. \"{}\" 4. \"{}\"".format(answers[0], answers[1], answers[2], answers[3]), "error")
						guess = difflib.get_close_matches(trivia_answers[question], answers, 1)[0]
						log("Selecting answer: \"{}\"".format(guess), "error")
						answer_id = answers_elements[answers.index(guess)]
						answer_id = answer_id.find('input', {'name': 'answers'}).get('value').strip()
				else:
					log("Guessing on question (no answer): \"{}\"".format(question), "error")
					log("Answer Choices: 1. \"{}\" 2. \"{}\" 3. \"{}\" 4. \"{}\"".format(answers[0], answers[1], answers[2], answers[3]), "error")
					answer_id = random.choice(answers_elements)
					answer_id = answer_id.find('input', {'name': 'answers'}).get('value').strip()

				question_data = {'t:ac': tac, 't:submit': 'submit', 'stk': cookie_dict['stk'], 't:formdata': tform,
                    'questionId': question_id, 'answerId': answer_id, 'submit': ''}

				connection.cookies.set("fkigvideo", quiz_id, domain="www.freekigames.com", path='/')
				question = connection.post(FREEKIGAMES_QUIZFORM, data=question_data, headers=headers)
				soup = question.text
			log("Quiz complete. Solving Captcha")
			solve_captcha(tac)
			log("Successfully solved \"{}\".".format(trivia[0]))

		else:
			log("No answers for \"{}\", skipping.".format(trivia[0]), "error")

def get_captcha():
	response = connection.get(CAPTCHA_IMAGE_URL, headers=headers)
	if response.status_code == 200:
		with open(FILENAME, 'wb') as f:
			f.write(response.content)
			# print("saved captcha - attempting to solve")
			return True

def post_captcha(word):
	post = connection.post(CAPTCHA_POST_URL, data={'value': word}, headers=headers)
	if post.text == 'true':
		return True
	return False

def solve_captcha(path):
	solved = False
	cookie_dict = connection.cookies.get_dict()
	#print(cookie_dict)
	#hr['Cookie'] = 'JSESSIONID=%s; stk=%s; Login0=1' % (cookie_dict['JSESSIONID'], cookie_dict['stk'])  # __qca=;
	#connection.get(REDEEM_URL)

	while not solved:
		if get_captcha() == True:
			response = requests.post(CAPTCHA_API, files={'img': (FILENAME, open(FILENAME, 'rb'))})
			captcha_data = json.loads(response.text)
			word = captcha_data['prediction']
			if captcha_data['error'] == False and post_captcha(word):
				log("Successfully solved captcha.")
				solved = True
			else: # if we get a match in close_word but captcha not correct, we request a new captcha
				get_captcha()
		else: # if we dont get any match, we refresh the captcha
			get_captcha()
	get_crowns(word, path)

def get_crowns(word, path):
	connection.cookies.set("showRegister", "block", domain="www.freekigames.com", path='/')
	soup = connection.get(CAPTCHA_URL, headers=headers).text
	soup = BeautifulSoup(soup, 'lxml')
	cookie_dict = connection.cookies.get_dict()
	tac = soup.find('input', {'name': 't:ac'}).get('value').strip()
	tform = soup.find('input', {'name': 't:formdata'}).get('value').strip()

	crown_data = {
		't:ac': tac,
		't:submit': 'login',
		'stk': cookie_dict['stk'],
		't:formdata': tform,
		'fpShowRegister': True,
		'captcha': word,
		'login': ''
	}

	crown_post = connection.post(CROWN_URL, data=crown_data, headers=headers)
	crown_get = connection.get(FREEKI_HOME_PAGE + path, headers=headers).text


def get_answers(page_title):
	with open('trivia.json') as f:
		trivia_data = json.load(f)
	return trivia_data[page_title]

def get_credentials():
	username = input("Username: ")
	password = getpass.getpass("Password: ")

	return username, password


def main():
	username, password = get_credentials()
	login(username, password)
	wizard_trivias = get_solvable_trivias(FREEKI_GAMES_WIZARD_101_TRIVIA)
	solve_trivias(wizard_trivias, get_answers("Wizard101 Trivia"))
