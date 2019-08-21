import requests
import json
import sys
import os
import re
import time
from requests_toolbelt.utils import dump


class Spider():
    nonce_submit = 0
    def __init__(self, url, username, password):
        self.url = url
        self.login_url = url + "/login"
        self.challenges_url = url + "/api/v1/challenges"
        self.attempt_url = url + "/api/v1/challenges/attempt"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.nonce = ""

    def login_page(self):
        return self.session.get(self.login_url).content

    def csrf(self, content):
        self.nonce = re.search('.*csrf_nonce.*"(.*)".*', content.decode('utf-8'))
        self.session.headers.update({ "csrf-token": self.nonce.group(1) })

    def login(self):
        login_page = self.login_page()
        if self.nonce == '':
            self.csrf(login_page)
        data = {
            "name": self.username,
            "password": self.password,
            "nonce": self.nonce.group(1)
        }
        r = self.session.post(self.login_url, data=data)
        content = r.content
        if any(x in str(content) for x in ["Your username or password is incorrect", "Forbidden"]):
            return False
        return True

    def get_challenges(self):
        if self.nonce == '':
            self.csrf(self.session.get(self.url).content)
        content = self.session.get(self.challenges_url).content
        try:
            data = json.loads(content)
            return data
        except:
            print('Not ready yet.')
            exit()

    def download(self, url, path):
        print("[+] Downloading from %s to %s" % (url, path))
        with open(path, "wb") as f:
            f.write(self.session.get(url).content)

    def get_detail(self, id):
        return json.loads(self.session.get(self.challenges_url + "/%d" % (id)).content)

    def submit(self, chal_id, flag):
        datasub = dict(submission=flag, challenge_id=chal_id)
        r = self.session.post(self.attempt_url, json=datasub)
        return json.loads(r.text)
        
def main():
    website = "" #Input CTFD hosted website
    username = "" #Input User Name
    password = "" #Input Pass
    match_key = "Misc" #input question label
    #target = sys.argv[4]
    spider = Spider(website, username, password)
    print("[.] Attempting login...")
    if not spider.login():
        print("[-] Login failed!")
        return
    print("[+] Login succeed!")

    try:
        while True:
            print("[.] Fetching challenges from %s" % (website))
            challenges = spider.get_challenges()["data"]
            print("[+] %d challenges found!" % (len(challenges)))

            if len(challenges) == 0:
                sleep = 5
                print("[.] Sleeping for %d second..." % sleep)
                time.sleep(sleep)
            else:
                break
    except KeyboardInterrupt:
        return

    questions = {}
    for challenge in challenges:
        # Get data
        detail = challenge['id']
        if challenge['category'].lower().startswith(match_key.lower()):
            questions.update({challenge['id']: challenge['name']})

    print("[.] %d challenges matched %s." % (len(questions.keys()), match_key))
    if len(questions.keys()) == 0:
        return

    print()
    for i in sorted(questions.keys()):
        print("[%s] Name: %s" % (i, questions[i]))
    print()
    
    while True:
        sub_id = input("[?] Which id to submit (#/exit)? ")
        if sub_id == 'exit':
            return

        print('[.] Submitting flag...')
        s = spider.submit(int(sub_id), "Flag{ThisIsaRaceToSeeWhoWins}")

        print()
        print(s)

        print()
        y_or_n = input('[?] Try without curly brackets (y/n)? ')
        if y_or_n.lower() == 'y':
            s = spider.submit(int(sub_id), "ThisIsaRaceToSeeWhoWins")
            print(s)

if __name__ == '__main__':
    main()
