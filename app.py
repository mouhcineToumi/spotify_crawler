import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yaml
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from spotify import run, get_track_credits
from pathlib import Path

def read_conf():
    with open("config.yaml", "r") as stream:
        try:
            conf = yaml.safe_load(stream)
            return conf
        except yaml.YAMLError as exc:
            print(exc)
            raise yaml.YAMLError


conf = read_conf()
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=conf['client_id'],
                                                           client_secret=conf['client_secret']))

tracks = []
for url in tqdm(conf['urls'], desc='tracks'):
    tracks += run(sp, url)

credits = []
track_ids = list(map(lambda x: x['url'].split('/')[-1], tracks))

for track_id in tqdm(track_ids, desc='credits'):
    credits.append(get_track_credits(track_id, conf['access_token']))


## make sure folder exists
Path("output").mkdir(exist_ok=True)

pd.merge(left=pd.DataFrame(tracks),
         right=pd.DataFrame(credits),
         how='left',
         on='url').to_excel('output/output_%s.xlsx' % (datetime.now().strftime("%d_%m_%Y_%H_%M")))
