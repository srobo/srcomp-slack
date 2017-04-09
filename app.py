from argparse import ArgumentParser
from collections import namedtuple
from datetime import datetime
import itertools
import json
import urllib.request

import arrow
import isodate
import humanize
import sseclient
import requests


class Bot:

    def __init__(self, stream_url, api_url, webhook_url):
        self.stream_url = stream_url
        self.api_url = api_url
        self.webhook_url = webhook_url

        self.last_match_no = 102

    def send_to_slack(self, message):
        requests.post(self.webhook_url, json=message)

    def get_next_matches(self, n):
        n2 = n + 2
        res = requests.get(self.api_url + '/matches', params={'num': f'{n}..{n2}'})
        return res.json()['matches']

    def run(self):
        for event in sseclient.SSEClient(self.stream_url):
            if event.event == 'match':
                current_matches = json.loads(event.data)
                next_matches = self.get_next_matches(self.last_match_no)

                colours = {
                    'A': '#ff0000',
                    'B': '#00ff00',
                }

                for num, matches in itertools.groupby(next_matches, lambda match: match['num']):
                    matches = list(matches)
                    time = arrow.get(matches[0]['times']['staging']['closes']).humanize()
                    message = {
                        'text': f'*{matches[0]["display_name"]}* *{time}* ({matches[0]["times"]["staging"]["closes"]})',
                        'attachments': []
                    }

                    for match in matches:
                        teams = '`, `'.join('___' if t is None else t for t in match['teams'])
                        message['attachments'].append({
                            'text': f'*{match["arena"]}* — `{teams}`',
                            'color': colours[match['arena']],
                            'mrkdwn_in': ['text'],
                        })

                    self.send_to_slack(message)
                self.last_match_no += 1


def main():
    parser = ArgumentParser()
    parser.add_argument('stream_url')
    parser.add_argument('api_url')
    parser.add_argument('webhook_url')

    args = parser.parse_args()

    bot = Bot(args.stream_url, args.api_url, args.webhook_url)
    bot.run()


if __name__ == '__main__':
    main()
