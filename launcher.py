import bot
import browser
import argparse

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Solve Wizard101 Trivias for free Crowns.")
	parser.add_argument("--browser", help="Launch browser to manually solve captcha.", action='store_true', required=False)
	parser.add_argument("--debug", help="Launch solver in debug mode to get trvia questions for database additions.", action='store_true', required=False)
	parser.add_argument("--headless", help="Launch script headless", action='store_true', required=False)
	args = parser.parse_args()

	browser.DEBUG = args.debug
	browser.HEADLESS = args.headless

	if args.browser or args.debug or args.headless:
		browser.main()
	elif bot.CAPTCHA_API == "":
		bot.log("No Captcha API specified. Please use in browser mode instead.", "error")
	else:
		bot.main()