import requests
from tqdm import tqdm
from urllib.parse import urlparse
from functools import reduce
from datetime import timedelta
from time import sleep


# artist url -> artist albums
def get_artist_albums(client, artist_url):
    def get_artist_albums_by_type(client, artist_url, album_type):
        artist_id = urlparse(artist_url).path.split('/')[-1]
        all_albums = client.artist_albums(artist_id=artist_id, limit=50, album_type=album_type)['items']

        keep_digging = len(all_albums) == 50
        while keep_digging:
            albums = client.artist_albums(artist_id=artist_id, limit=50,
                                          offset=len(all_albums), album_type=album_type)['items']
            keep_digging = len(albums) == 50
            all_albums += albums
        return all_albums

    albums = get_artist_albums_by_type(client, artist_url, album_type='album')
    singles = get_artist_albums_by_type(client, artist_url, album_type='single')
    return albums + singles


# album id -> tracks
def get_album_tracks(client, album_id):
    sleep(1)
    tracks = client.album_tracks(album_id=album_id, limit=50)
    return tracks['items']


# track id -> information
def get_track(client, track_id):
    sleep(0.2)
    track = client.track(track_id=track_id)
    return track


def get_tracks(client, track_ids):
    bits = [track_ids[i: i + 50] for i in range(0, len(track_ids), 50)]
    tracks = list(map(lambda x: client.tracks(x)['tracks'], tqdm(bits, 'collecting tacks infos', leave=False)))
    tracks = list(reduce(lambda x, y: x + y, tracks))
    return tracks


def process(track):
    d = {}
    d['isrc'] = track['external_ids']['isrc']
    d['url'] = track['external_urls']['spotify']
    d['song_title'] = track['name']
    d['duration'] = str(timedelta(seconds=track['duration_ms'] // 1000))
    d['artists'] = '\n'.join(list(map(lambda x: x['name'], track['artists'])))
    d['album'] = track['album']['name']
    return d


def run(client, url):
    albums = get_artist_albums(client, url)
    album_ids = list(map(lambda x: x['id'], albums))

    tracks = list(
        map(lambda x: get_album_tracks(client, x), tqdm(album_ids, desc='collecting tracks from albums', leave=False)))
    tracks = list(reduce(lambda x, y: x + y, tracks))
    track_ids = list(map(lambda x: x['id'], tracks))

    track_infos = get_tracks(client, track_ids)

    p_tracks = list(map(process, tqdm(track_infos, desc='processing', leave=False)))
    return p_tracks


def get_track_credits(track_id, access_token):
    session = requests.Session()
    data = session.get('https://spclient.wg.spotify.com/track-credits-view/v0/experimental/%s/credits' % (track_id),
                       headers={'authorization': access_token}).json()
    d = {}
    d['url'] = "https://open.spotify.com/track/" + track_id
    for credit in data['roleCredits']:
        d[credit['roleTitle']] = '\n'.join(list(map(lambda x: x['name'], credit['artists'])))
    d['source'] = '\n'.join(data['sourceNames'])
    return d
