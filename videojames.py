import os
import sqlite3

import requests

import hug
from slackclient import SlackClient

def _validate_token(token):
    with open("/etc/videojames/verification_token", "r") as token_file:
        verification_token = token_file.read().strip()
        return token == verification_token

@hug.post()
def lfg(body):
    if not _validate_token(body['token']):
        return

    conn = sqlite3.connect('videojames.db')
    c = conn.cursor()

    with open("/etc/videojames/token","r") as token_file:
        token = token_file.read().strip()

    slack = SlackClient(token)

    res = c.execute('SELECT user FROM games WHERE game=?', (body['text'],))
    users = res.fetchall()

    for user in users:
        id = user[0]

        im_channel = slack.api_call(
            "im.open",
            user=id,
            return_im="true"
        )
        channel = im_channel['channel']['id']

        slack.api_call(
            "chat.postMessage",
            channel=channel,
            text='<@{0}> wants to play "{1}"! Head over to <#{2}>'.format(body['user_id'], body['text'], body['channel_id']),
        )

    conn.close()
    return {
        'response_type': "in_channel",
        'text': '<@{0}> wants to play "{1}"!'.format(body['user_id'],body['text']),
    }

@hug.post()
def games(body):
    if not _validate_token(body['token']):
        return

    conn = sqlite3.connect('videojames.db')
    c = conn.cursor()

    res = c.execute('SELECT DISTINCT game FROM games')
    games = res.fetchall()

    conn.close()

    if len(games) == 0:
        return {
            'text': "No games! WHY..."
        }
    return {
        'text': "\n".join([g[0] for g in games]),
    }

@hug.post()
def subscribe(body):
    if not _validate_token(body['token']):
        return

    conn = sqlite3.connect('videojames.db')
    try:
        c = conn.cursor()
        c.execute('INSERT INTO games(user,game) VALUES(?,?)', (body['user_id'], body['text']))

        conn.commit()
        conn.close()
        return {
            'text': "Subscribed to {0}!".format(body['text'])
        }
    except sqlite3.IntegrityError:
        return {
            'text': "Already subscribed!"
        }

@hug.post()
def unsubscribe(body):
    if not _validate_token(body['token']):
        return

    conn = sqlite3.connect('videojames.db')
    c = conn.cursor()
    c.execute('DELETE FROM games WHERE user=? AND game=?', (body['user_id'], body['text']))
    conn.commit()
    conn.close()
    return {
        'text': "Unsubscribed from {0}!".format(body['text'])
    }
