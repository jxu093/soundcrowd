import requests
from sys import argv
from prettytable.prettytable import PrettyTable
from bs4 import BeautifulSoup

from keys import *


sc_request_url = 'https://api.soundcloud.com/tracks.json'
action_url = 'http://9soundclouddownloader.com/download-sound-track'
payload = {'csrfmiddlewaretoken': 's0d0L73y3TaTLXe1smxy8hP3Vdi9lG8y'}


PARSE_BATCH_URL = 'https://api.parse.com/1/batch'
PARSE_URL2 = 'https://api.parse.com/1/classes/Tracks'
PARSE_HEADER = {'X-Parse-Application-Id': PARSE_APP_ID,
                'X-Parse-REST-API-Key': PARSE_API_KEY,
                'Content-Type': 'application/json'
                }


def run_job(genre, limit, offset):
    print '>> Fetching {} songs from offset {} of the {} genre'.format(limit, offset, genre)

    data = {
        'linked_partitioning': 1,
        'client_id': client_id,
        'genres': genre,
        'limit': limit,
        'offset': offset
    }

    r = requests.get(sc_request_url, data)

    results = r.json()

    tracks = results['collection']

    print '>> {} tracks found.'.format(len(tracks))

    reqs = []

    # x = PrettyTable(["Title", "Length", "Plays", "Favs", "SC Link", "DL Link"])

    for i in range(0, limit):
        print i
        track = tracks[i]
    # for track in tracks:
        title = track['title']
        duration = round(track['duration']/60000.0,2)
        playback_count = track['playback_count']
        fav_count = track['favoritings_count']
        # playback_count = "{:,}".format(track['playback_count'])
        # fav_count = "{:,}".format(track['favoritings_count'])
        sound_url = track['permalink_url']
        dl_link = get_dl_link(sound_url)

        index = offset + i + 1

        body = {'title': title, 'length': duration, 'plays': playback_count, 'favs': fav_count, 'sc_url': sound_url, 'dl_url': dl_link, 'index': index}

        req = {'method': 'POST', 'path': '/1/classes/Tracks', 'body': body}

        reqs.append(req)

        # x.add_row([title, duration, playback_count, fav_count, sound_url, dl_link])

    # print x
    resp = requests.post(url=PARSE_BATCH_URL, json={'requests': reqs}, headers=PARSE_HEADER)

    success_count = 0
    fail_count = 0
    for operation in resp.json():
        if 'success' not in operation:
            print operation['error']
            fail_count+=1
        else:
            success_count+=1
    print '>> {} operations successful, {} operations failed.'.format(success_count, fail_count)
    print '>> Track count is now at {}'.format(offset + i + 1)


def get_dl_link(sc_link):
    payload['sound-url'] = sc_link
    r = requests.get(action_url, params=payload)
    soup = BeautifulSoup(r.text, 'html.parser')
    dl_link = soup.find("a", rel="nofollow").get('href')
    return dl_link


def run_job_more(genre, limit, offset):
    MAX = 10
    if limit <= MAX:
        run_job(genre, limit, offset)
    else:
        remaining = limit - MAX
        run_job(genre, MAX, offset)
        run_job_more(genre, remaining, offset+MAX)


if __name__ == '__main__':
    script, genre_, limit_, offset_ = argv
    limit_ = int(limit_)
    offset_ = int(offset_)

    repeat = True
    while repeat:
        run_job_more(genre_, limit_, offset_)
        print '>> Would you like to continue? Say y, n, or c to change options'
        user_input = raw_input()
        if user_input == 'y':
            repeat = True
            offset_ += limit_
        elif user_input == 'n':
            repeat = False
            print '>> Goodbye'
        elif user_input == 'c':
            print '>> You just fetched {} tracks from index {} in {} genre, enter new [genre] [limit] [offset]'.format(limit_, offset_, genre_)
            inputs = raw_input()
            genre_, limit_, offset_ = inputs.split()
            limit_ = int(limit_)
            offset_ = int(offset_)
            repeat = True
        else:
            print '>> Did not understand your input "{}". Goodbye'.format(user_input)
            repeat = False
