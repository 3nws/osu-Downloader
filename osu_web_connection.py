import requests
import os
import sys

from os.path import basename
from bs4 import BeautifulSoup
from pathlib import Path
from zipfile import ZipFile

from beatmap import *

class OsuWebConnection:
    # new site
    home_url = "https://osu.ppy.sh/home"
    login_url = "https://osu.ppy.sh/session"

    def __init__(self, validate=True):
        self.session = requests.Session()
        if validate:
            print("Login:")
            self.login = input()
            print("Password:")
            self.password = input()
            self.token = ""
            self.initial_connection()
            self.do_login()

    def initial_connection(self):
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0'})
        self.session.headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
        self.session.headers.update({'Accept-Language': 'en-US,en;q=0.5'})
        self.session.headers.update({'Accept-Encoding': 'gzip, deflate'})
        self.session.headers.update({'Connection': 'keep-alive'})

        r = self.session.get(self.home_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        self.token = soup.find('input').attrs['value']

        print("Session token: " + self.token)

    def do_login(self):
        print("Logging in osu! site with user " + self.login + "....")
        r = self.session.post(OsuWebConnection.login_url,
                data={'_token': self.token,
                    'username': self.login,
                    'password': self.password})
        print(r.text)

    """def is_logged(self):
        r = self.session.get(OsuWebConnection.login_url)
        text = r.text
        if "Username:" in text and "Password:" in text and \
           "Log me on automatically each visit" in text and \
           "Hide my online status this session" in text:
            return False
        elif "Announcements (click for more)" in text:
            return True
        return False
    """

    def convert_to_valid_filename(self, filename):
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c if c in valid_chars else '_' for c in filename)

    def download_beatmap(self, beatmap, path):
        #if not self.is_logged():
        #    self.do_login()

        try:
            beatmap_url = "https://osu.ppy.sh/beatmapsets/" + beatmap.beatmapset_id + '/download'
        except AttributeError:
            beatmap_url = "https://osu.ppy.sh/beatmapsets/" + beatmap.id + '/download'
            
        r = self.session.get(beatmap_url, allow_redirects=False)
        
        if 'Page Missing' in r.text:
            beatmap.download_status = "NOT AVAILABLE"
            return

        try:
            filename_base = self.convert_to_valid_filename(beatmap.beatmapset_id + " " + beatmap.artist + " - " + beatmap.title)
        except AttributeError:
            filename_base = self.convert_to_valid_filename(beatmap.id + " " + beatmap.artist + " - " + beatmap.title)
        filename_temp = filename_base + ".temp"
        filename_final = filename_base + ".osz"
        # beatmap available, download it
        #print(r.text)
        mirrors = { 
            "beatconnect.io": "https://beatconnect.io/b/{}",
            "chimu.moe": "https://api.chimu.moe/v1/download/{}?n=1"
        }
        dled = []
        try: id = beatmap.id
        except AttributeError: id = beatmap.beatmapset_id
        success = False

        # iterate through all available mirrors and try to download the beatmap
        for m in mirrors:
            url = mirrors[m].format(id)
            print("\nTrying to download #{0} from {1}. Press Ctrl + C if download gets stuck for too long.".format(id, m))

            timeout = False
            
            try:
                r = requests.head(url, allow_redirects=True, timeout=10)
            except:
                timeout = True

            # download the beatmap file
            path = Path(path)
            if not timeout and r.status_code == 200:
                filename = path.joinpath(id + ".osz")


                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "wb") as f:
                    print(f"Downloading {filename}")
                    response = requests.get(r.url, stream=True)
                    total_length = response.headers.get('Content-Length')

                    if total_length is None: # no content length header
                        f.write(response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in response.iter_content(chunk_size=4096):
                            dl += len(data)
                            f.write(data)
                            done = int(50 * dl / total_length)
                            sys.stdout.write(f"\r[{'='*done}{' '*(50-done)}] {int(100 * dl / total_length)}%")    
                            sys.stdout.flush()
                dled.append(filename)

                if filename.exists():
                    print("\nDownloaded #{}".format(id))
                    success = True

                break
        
        # print fail message if none of the mirrors work or if download didn't complete
        if not success:
            print("Failed to download #{}! It probably does not exist on the mirrors.\n"
            "Please manually download the beatmap from osu.ppy.sh!".format(id))
        
        print("\nFinished downloading!")

        #Add all files to zip
        self.add_to_zip(dled, "maps")

        return dled

    def add_to_zip(self, paths, name):
        print("Adding to zip....")
        with ZipFile(name, 'w') as z:
            for f in paths:
                z.write(f, basename(f))

    def close(self):
        self.session.close()
