
import re
from urllib.parse import quote as url_quote
from getpass import getpass as get_pass
from collections import namedtuple
from time import sleep
from os.path import exists

import requests

from ipymarkup import show_markup


TEXT_MATCH = {
    'Accept': 'application/vnd.github.v3.text-match+json'
}

URLS = 'urls.txt'


SerpRecord = namedtuple(
    'SerpRecord',
    ['user', 'repo', 'path', 'matches']
)


def format_q_params(params):
    for key, values in params:
        for value in values:
            yield '{key}:{value}'.format(
                key=key,
                value=value
            )


def gh_q(text, extensions=(), no_orgs=(), no_users=()):
    params = [
        ('extension', extensions),
        ('-org', no_orgs),
        ('-user', no_users)
    ]
    return '{text}+{params}'.format(
        text=text,
        params='+'.join(format_q_params(params))
    )


def format_params(params):
    for key, value in sorted(params.items()):
        yield '{key}={value}'.format(
            key=key,
            value=value
        )
    

def gh_url(*path, **params):
    return 'https://api.github.com/{path}?{params}'.format(
        path='/'.join(path),
        params='&'.join(format_params(params))
    )


def gh_search_code_url(q, sort='indexed', page=1):
    return gh_url('search', 'code', q=q, sort=sort, page=page)


def call_gh(url, auth, headers=None):
    response = requests.get(
        url,
        auth=auth,
        headers=headers
    )
    return response, response.json()


def parse_serp_total(data):
    return data['total_count']


def get_pages(total, step=30):
    for index, _ in enumerate(range(0, total, step)):
        yield index + 1


def is_broken(data):
    return 'items' not in data


def parse_serp(data):
    for item in data['items']:
        path = item['path']
        repo = item['repository']
        user = repo['owner']
        matches = [_['fragment'] for _ in item['text_matches']]
        yield SerpRecord(
            user['login'],
            repo['name'],
            path, matches
        )


def get_serp_record_url(record):
    return 'https://github.com/{user}/{repo}/tree/master/{path}'.format(
        user=record.user,
        repo=record.repo,
        path=record.path
    )


def get_spans(text, pattern):
    for match in re.finditer(pattern, text, re.I):
        yield match.start(), match.end()


def dump_lines(lines, path):
    with open(path, 'w') as file:
        for line in lines:
            file.write(line + '\n')


def load_lines(path):
    if not exists(path):
        return
    with open(path) as file:
        for line in file:
            yield line.rstrip('\n')
