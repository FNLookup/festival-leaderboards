import datetime
import json
import os
import re
import sys
import threading
import requests

def print_progress_bar(iteration, total, length=50):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r|{bar}| {percent}% Complete')
    sys.stdout.flush()

def makeDir(folder_path):
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
        except Exception as e:
            print('Error making folder: ', e)

def getLeaderboardOf(su, eg1, instrument, page, season):
    url = f"https://events-public-service-live.ol.epicgames.com/api/v1/leaderboards/FNFestival/season00{season}_{su}/{su}_{instrument}/3554e7171c554bdc8b38edb226fe6b0f?page={page}&rank=0&teamAccountIds=&appId=Fortnite&showLiveSessions=false"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {eg1}'
    }
    response = requests.request("GET", url, headers=headers)
    return response.json()

def getAccountIdsNames(accountIDs, eg1_token):
    urlParams = ''

    headers = {
        'Authorization': 'Bearer ' + eg1_token
    }

    for i, uid in enumerate(accountIDs):
        if i == 0:
            urlParams += '?accountId=' + uid
        else:
            urlParams += '&accountId=' + uid

    url = 'https://account-public-service-prod.ol.epicgames.com/account/api/public/account' + urlParams

    response = requests.request("GET", url, headers=headers, data="")
    users = response.json()

    _users_final = {}
    for user in users:
        if not isinstance(user, dict):
            continue
        
        if user.get('id', None) == None:
            continue

        accountId = user['id']
        displayName = user.get('displayName', None)
        # _external_platform_names = []

        # for platform in user.get('externalAuths', []).keys():
        #     _platform_data = user['externalAuths'][platform]

        #     _platform_auth_origin = _platform_data['type']

        #     if displayName == None:
        #         displayName = _platform_data.get('externalDisplayName', 'Unknown competitor')
                
        #     _platform_auth_name = _platform_data.get('externalDisplayName', displayName)

        #     _external_platform_names.append({
        #         'type': _platform_auth_origin,
        #         'displayName': _platform_auth_name
        #     })

        _users_final[accountId] = {
            'displayName': displayName
        }

    return _users_final

def fullcombo(_fcint):
    if _fcint == 0:
        return False
    elif _fcint == 1:
        return True
    
def accuracy(_accint):
    return int(_accint / 10000)

def validtime(_tstr):
    if '.' in _tstr:
        dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    else:
        dt_format = "%Y-%m-%dT%H:%M:%SZ"

    # Parse the string into a datetime object
    dt = datetime.datetime.strptime(_tstr, dt_format).timestamp()
    return dt

def parse_entry(data):
    entry = {
        "rank": data["rank"],
        "teamId": data["teamId"],
        "userName": None,
        "best_run": {},
        "sessions": []
    }

    _bestScoreYet = 0
    _bestRun = {}
    for session in data["sessionHistory"]:
        score = session["trackedStats"]["SCORE"]

        valid_entry = {
            "accuracy": accuracy(session["trackedStats"]["ACCURACY"]),
            "score": score,
            "difficulty": session["trackedStats"]["DIFFICULTY"],
            "instrument": session["trackedStats"]["INSTRUMENT_0"],
            "stars": session["trackedStats"]["STARS_EARNED"],
            "fullcombo": fullcombo(session["trackedStats"]["FULL_COMBO"])
        }

        if score > _bestScoreYet:
            _bestRun = valid_entry
            _bestScoreYet = score

        band = {
            "accuracy": accuracy(session["trackedStats"]["B_ACCURACY"]),
            "fullcombo": fullcombo(session["trackedStats"]["B_FULL_COMBO"]),
            "stars": session["trackedStats"]["B_STARS"],
            "scores": {
                "overdrive_bonus": session["trackedStats"]["B_OVERDRIVE_BONUS"],
                "base_score": session["trackedStats"]["B_BASESCORE"],
                "total": session["trackedStats"]["B_SCORE"]
            }
        }

        players = []
        for key, value in session["trackedStats"].items():
            match = re.match(r"M_(\d+)_ID_(\w+)", key)
            if match:
                player_number, account_id = match.groups()

                is_valid_entry = account_id == data['teamId']

                player = {
                    "accuracy": accuracy(session["trackedStats"].get(f"M_{player_number}_ACCURACY")),
                    "score": session["trackedStats"].get(f"M_{player_number}_SCORE"),
                    "difficulty": session["trackedStats"].get(f"M_{player_number}_DIFFICULTY"),
                    "instrument": session["trackedStats"].get(f"M_{player_number}_INSTRUMENT"),
                    "fullcombo": fullcombo(session["trackedStats"].get(f"M_{player_number}_FULL_COMBO")),
                    "stars": session["trackedStats"].get(f"M_{player_number}_STARS_EARNED"),
                    "is_valid_entry": is_valid_entry
                }
                players.append(player)

        entry["sessions"].append({
            "time": validtime(session["endTime"]),
            "valid": valid_entry,
            "stats": {
                "band": band,
                "players": players
            }
        })

    entry["best_run"] = _bestRun

    return entry

def main():
    print('Initializing...')
    print('Reading Meta')

    meta = {}
    with open('meta.json', 'r') as f:
        meta = json.loads(f.read())

    season_number = meta.get('season', 4)

    print('Generating Device Auth EG1')
    eg1_params = {
        "grant_type": "device_auth",
        "account_id": os.getenv('ACCOUNT_ID'),
        "device_id": os.getenv('DEVICE_ID'),
        "secret": os.getenv('SECRET'),
        "token_type": "eg1"
    }
    token_eg1 = getEG1Token(eg1_params, os.getenv('BASIC_AUTH'))

    all_songs = getSongList()['tracks']

    all_songs = all_songs[0:2]

    for song in all_songs:
        eventId = song['event_id']
        songId = song['id']

        #print('Found song\nID:', songId, '\nEvent ID:', eventId)
        print(f'Getting leaderboard of {songId} - {eventId}')

        instruments = [
            'Solo_Vocals',
            'Solo_Bass',
            'Solo_Guitar',
            'Solo_Drums',
            'Solo_PeripheralBass',
            'Solo_PeripheralGuitar'
        ]

        donepages = 0

        for instrument in instruments:
            #print('Instrument:', instrument)

            _current_pages = -1
            _max_pages = 0

            while _current_pages < _max_pages:

                _current_pages += 1
                donepages += 1

                print_progress_bar(donepages, len(instruments) * 5)

                #print('Page:', _current_pages)
                leaderboard = getLeaderboardOf(eventId, token_eg1, instrument, _current_pages, season_number)
                _max_pages = leaderboard.get('totalPages', 1) - 1

                _leaderboard_parsed = {
                    'entries': []
                }

                for entry in leaderboard['entries']:
                    _newEntry = parse_entry(entry)
                    _leaderboard_parsed['entries'].append(_newEntry)

                #print('Got leaderboard, saving')

                makeDir(f'leaderboards/season{season_number}/{songId}/')

                #print('Obtaining user names with IDs')

                _list_user_ids = []

                for entry in leaderboard['entries']:
                    entryAccountId = entry['teamId']
                    _list_user_ids.append(entryAccountId)

                def userShit(ss, sid, ins, pg):
                    makeDir(f'leaderboards/season{ss}/{sid}/')
                    #print('Getting users')
                    users = getAccountIdsNames(_list_user_ids, token_eg1)

                    #print('Got users, saving')

                    for entry in _leaderboard_parsed['entries']:
                        if entry['teamId'] in users:
                            entry['userName'] = users[entry['teamId']]['displayName']

                    # with open(f'leaderboards/season{ss}/{sid}/{ins}_{pg}_Users.json', 'w') as usersFile:
                    #     usersFile.write(json.dumps(users, indent=4))

                with open(f'leaderboards/season{season_number}/{songId}/{instrument}_{_current_pages}.json', 'w') as pageFile:
                    pageFile.write(json.dumps(_leaderboard_parsed, indent=4))

                userthread = threading.Thread(target=userShit, args=(season_number, songId, instrument, _current_pages))
                userthread.start()
        
            print()

    print("Done fetching!")

def getEG1Token(authParams, basicAuth):
    request = requests.post('https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token', data=authParams, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f"Basic {basicAuth}"})
    json = request.json()
    token = json['access_token']
    return token

def getSongList():
    url = 'https://raw.githubusercontent.com/FNLookup/data/main/festival/jam_tracks.json'
    return requests.get(url).json()

if __name__ == '__main__':
    main()