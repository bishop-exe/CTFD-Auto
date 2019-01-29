from bs4 import BeautifulSoup
import requests
import json
import sys
import os

class Spider():
    nonce_submit = 0
    def __init__(self, url, username, password):
        self.url = url
        self.login_url = url + "/login"
        self.challenges_url = url + "/chals"
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login_page(self):
        return self.session.get(self.login_url).content

    def csrf(self, content):
        return BeautifulSoup(content, "html.parser").find_all("input")[-1]['value']

    def login(self):
        nonce = self.csrf(self.login_page())
        data = {
            "name": self.username,
            "password": self.password,
            "nonce": nonce,
        }
        content = self.session.post(self.login_url, data=data).content
        if "Your username or password is incorrect" in str(content):
            return False
        return True

    def get_challenges(self):
        content = self.session.get(self.challenges_url).content
        return json.loads(content)

    def download(self, url, path):
        print("[+] Downloading from %s to %s" % (url, path))
        with open(path, "wb") as f:
            f.write(self.session.get(url).content)

    def get_detail(self, id):
        return json.loads(self.session.get(self.challenges_url + "/%d" % (id)).content)

    def submit(self, chal_id, flag):
        datasub = dict(key=flag)
        if self.nonce_submit == 0:
            r = self.session.get(self.url + "/challenges")
            data = r.content
            soup = BeautifulSoup(data, 'html.parser')
            self.nonce_submit = soup.find('input', {'name':'nonce'}).get('value')

        datasub["nonce"] = self.nonce_submit
        r = self.session.post("{}/chal/{}".format(self.url, chal_id), data=datasub)
        return json.loads(r.text)
        
def main():
    website = "https://dragonctf.com"
    username = "athf.flcl@gmail.com"
    password = "register"
    #target = sys.argv[4]
    spider = Spider(website, username, password)
    print("[+] Fetching challenges from %s" % (website))
    if not spider.login():
        print("[-] Login failed!")
        return
    print("[+] Login succeed!")
    challenges = spider.get_challenges()["game"]
    print("[+] %d challenges found!" % (len(challenges)))
    questions = {}
    for challenge in challenges:
        # Get data
        detail = spider.get_detail(challenge['id'])
        if challenge['category'][:4].lower() == "misc":
            questions.update({challenge['name']:challenge['id']})
    for i in questions:

        print("[%s] Name: %s" % (questions[i], i))
    
    sub_id = input("which id to submit?")
    s = spider.submit(int(sub_id), "Flag{ThisIsaRaceToSeeWhoWins}")
    print(s["message"])
if __name__ == '__main__':
    main()