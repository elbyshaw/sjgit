import subprocess
import csv
import re
import glob
import json


## =========== USER DEFINES ============= ##

team_names = ['fall26_digital_onboarding_phase_2'] # can take multiple teams
id_type = 'gt_username' # choose gt_email or gt_username

## ====================================== ##


def main():
	if (team_names == '' or id_type == ''):
		print("Please choose one or more team names and define an id type.")
		print("Also, please make sure you've set up your CLI for using the gh command to interface with the GT Github Enterprise API.")
		exit(1)

	user_list = readCSV()
	if len(user_list) == 0:
		print("No users in the csv file; nothing to do.")
		exit(0)
	successes = 0
	fails = 0

	for team in team_names:
		print(f"Adding users to {team}")
		run_stats = addUsersToTeam(user_list, team)
		successes += run_stats[0]
		fails += run_stats[1]

	print(f"Total count of teams: {len(team_names)}")
	print(f"Total count of users: {len(user_list)}")
	print(f"Request completed with {successes} successes and {fails} fails.")



def readCSV():
	"""
	Reads in a list of usernames/ids from the csv file in the same directory as the script.
	Returns a list of values extracted from the csv.
	- There should only be 1 csv file in the same directory as the script
	- The csv file should have all values on a single row
	"""
	csv_files = glob.glob("*csv")

	# Check for a SINGLE csv file
	if len(csv_files) == 0:
		print("Error: no .csv file found in current directory")
		exit(1)
	elif len(csv_files) > 1:
		print("Error: multiple csv files found in current directory. This script requires a single csv file.")	
		exit(1)
	else:
		csv_file = csv_files[0]

	# Read in the SINGLE ROW from the csv file
	with open(csv_file, mode='r') as file:
		reader = csv.reader(file)
		rowcount = 0
		usernamelist = []
		for row in reader:
			rowcount += 1
			usernamelist = row
		if rowcount > 1:
			print("Error: csv file should only have 1 row")
			exit(1)
	# Drop blank entries (e.g. an empty file or a trailing comma)
	usernamelist = [u.strip() for u in usernamelist if u.strip()]

	# Start a fresh log for this run and write warnings for bad emails
	with open('log.txt', 'w') as log:
		for i in range(len(usernamelist)):
			# if email list expected, check for @gatech.edu
			if id_type == 'gt_email':
				user = re.sub(r'@(.*?)$', '', usernamelist[i])
				if not re.match(r'(.*?)@gatech.edu', usernamelist[i]):
					print(f"WARNING: Non GT Email skipped: {usernamelist[i]}")
					log.write(f"WARNING: Non GT Email skipped: {usernamelist[i]}\n")
					continue
			# otherwise, just ingest all usernames
			elif id_type == 'gt_username':
				user = usernamelist[i]
	return usernamelist
		
def addUsersToTeam(user_list, team_name):
	"""
	Given a list of users and a team name, adds all users in that list to the team.
	- Ensures team and each user exists
	- DOESN'T check whether user is already on the given team; will just say it added them
	- Returns a list of in the form [# of successes, # of fails]
	"""
	log = open('log.txt', 'a')
	successes = 0
	fails = 0

	# Make sure the specified team exists
	command = ["gh", "api", f"orgs/SiliconJackets/teams/{team_name}"]
	result = subprocess.run(command, capture_output=True, text=True)
	data = json.loads(result.stdout)
	if data.get("status") == "404":
		error_message = f"ERROR: Team {team_name} not found"
		print(error_message)
		log.write(error_message + '\n')
		fails += len(user_list)
		return [successes, fails]	

	for user in user_list:
		command = [
				"gh", "api",
				"--method", "PUT",
				"-H", "Accept: application/vnd.github+json",
				"-H", "X-GitHub-Api-Version: 2022-11-28",
				f"/orgs/SiliconJackets/teams/{team_name}/memberships/{user}",
				"-f", "role=member"
		]

		try:	
			# Attempt to add the user via Github API
			result = subprocess.run(command, capture_output=True, text=True)
			# parse json response from Github API
			data = json.loads(result.stdout)
			
			# Write errors if request failed. A successful membership PUT returns
			# {url, role, state}; every error response carries a "message"
			# (Not Found, rate limit, bad credentials, ...). Keep the user in
			# the retry list for all of them.
			if result.returncode != 0 or "message" in data:
				reason = data.get("message", f"gh exited with status {result.returncode}")
				error_message = f"ERROR: Couldn't add user {user} ({reason})"
				print(error_message)
				log.write(error_message + '\n')
				fails += 1
			else:
				print(f"> LOG: Adding {user} to {team_name}...")
				successes += 1
		except Exception as e:
			print("Encountered an error when trying to use the gh command. Do you have it configured properly?")
			print(f"Error Message: {e}")
			exit(1)
	return [successes, fails]

main()
