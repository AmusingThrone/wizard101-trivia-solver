from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
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

FREEKI_GAMES_LOGIN = "https://www.freekigames.com/auth/popup/login/freekigames?fpShowRegister=true"
FREEKI_GAMES_LOGIN_SUCCESS = "https://www.freekigames.com/freekigames"
FREEKI_GAMES_WIZARD_101_TRIVIA = "https://www.freekigames.com/wizard101-trivia"
DELAY = 10
DEBUG = ""
HEADLESS = ""

def log(message, type="log"):
	if type == "log":
		print("[%] " + message)
	elif type == "error":
		print("[!] " + message)
	elif type == "confirm":
		input("[>] " + message)


def get_credentials():
	username = input("Username: ")
	password = getpass.getpass("Password: ")
	
	return username, password


def login(username, password, browser):
	wait = WebDriverWait(browser, DELAY)

	username_input = wait.until(EC.element_to_be_clickable((By.NAME, 'userName')))
	username_input.send_keys(username)

	password_input = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
	password_input.send_keys(password)

	wait.until(EC.presence_of_element_located((By.ID, 'bp_login'))).click()
	log("Attempting to login with provided credentials.")

	if browser.current_url == FREEKI_GAMES_LOGIN_SUCCESS:
		log("Successfully logged in.")
	else:
		log("Unable to login with provided credentials.", "error")
		sys.exit("Incorrect credentials provided.")


def get_trivias(browser):
	browser.get(FREEKI_GAMES_WIZARD_101_TRIVIA)
	trivias_elements = browser.find_elements_by_xpath('//div[@class="gamevert_3column"]/ul/li')
	log("Gathering trivias.")	
	trivias = []
	for trivia in trivias_elements:
		if trivia.get_attribute("class") == "notake":
			pass
		else:
			trivias.append([trivia.find_element(By.XPATH, './/div[@class="gamename"]').text, trivia.find_element(By.XPATH, './/div[@class="thumb"]/a').get_attribute('href')])

	log("Found {} possible trivias.".format(len(trivias)))

	return trivias


def get_answers():
	with open('trivia.json') as f:
		trivia_data = json.load(f)
	return trivia_data["Wizard101 Trivia"]


def solve_trivias(trivias, browser):
	wait = WebDriverWait(browser, DELAY)
	trivia_data = get_answers()
	log("Loaded answers for {} trivias.".format(len(trivia_data.keys())))
	for trivia in trivias:
		if trivia[0] in trivia_data.keys():
			url = trivia[1]
			trivia_answers = trivia_data[trivia[0]]
			browser.get(url)
			log("Attempting to solve \"{}\".".format(trivia[0]))

			for x in range(12):
				quizContainer = wait.until(EC.element_to_be_clickable((By.ID, 'quizContainer')))
				question = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="quizQuestion"]'))).text.strip()
				submit_button = wait.until(EC.element_to_be_clickable((By.ID, 'nextQuestion')))
				answers_elements = browser.find_elements_by_xpath('//span[@class="answerText"]')
				answers = []
				for answer in answers_elements:
					answers.append(answer.get_attribute("innerHTML").strip())
				
				if question in trivia_answers:
					if trivia_answers[question] in answers:
						text_element = answers_elements[answers.index(trivia_answers[question])]
						text_element.find_element_by_xpath('../span[@class="answerBox"]').click()
						submit_button.click()
					else:
						log("Guessing on question (could not find answer): \"{}\"".format(question), "error")
						log("Answer Choices: 1. \"{}\" 2. \"{}\" 3. \"{}\" 4. \"{}\"".format(answers[0], answers[1], answers[2], answers[3]), "error")
						guess = difflib.get_close_matches(trivia_answers[question], answers, 1)[0]
						log("Selecting answer: \"{}\"".format(guess), "error")
						text_element = answers_elements[answers.index(guess)]
						text_element.find_element_by_xpath('../span[@class="answerBox"]').click()
						submit_button.click()
				else:
					log("Guessing on question (no answer): \"{}\"".format(question), "error")
					log("Answer Choices: 1. \"{}\" 2. \"{}\" 3. \"{}\" 4. \"{}\"".format(answers[0], answers[1], answers[2], answers[3]), "error")
					text_element = random.choice(answers_elements)
					text_element.find_element_by_xpath('../span[@class="answerBox"]').click()
					submit_button.click()

			log("Quiz complete. Enter any key to continue.", "confirm")

		else:
			log("Skipping solving \"{}\".".format(trivia[0]))


def bot(browser):
	if DEBUG == False:
		username, password = get_credentials()
		browser.get(FREEKI_GAMES_LOGIN)
		login(username, password, browser)

	wizard_101_trivias = get_trivias(browser)
	solve_trivias(wizard_101_trivias, browser)

	browser.quit()
	log("Closed browser.")


def main():
	try:
		chrome_options = Options()
		chrome_options.add_argument("--headless") if DEBUG or HEADLESS else chrome_options.add_argument("--start-maximized")
		browser = webdriver.Chrome(options=chrome_options)
		bot(browser)
	except Exception as e:
		log("Encountered Error: {}".format(traceback.format_exc()), "error")
		browser.quit()
