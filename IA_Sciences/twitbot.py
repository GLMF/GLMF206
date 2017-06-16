import tweepy
import configparser
import random

MAX_LEN_TEXT = 140


def readconfig(filename='twitter.ini'):
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in config['config']:
        data[key] = config['config'][key]
    return data

def get_api(cfg):
    auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
    auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
    return tweepy.API(auth)

def segmentizeText(text):
    max_line = MAX_LEN_TEXT - 6
    lines = []
    current_line = ''
    for word in text.split(' '):
        if len(current_line) + len(word) + 1 > max_line:
            lines.append(current_line)
            current_line = word
        else:
            if current_line != '':
                current_line += ' '
            current_line += word
    if current_line != '':
        lines.append(current_line)
    return lines

def tweet(api, text, reply_to=None, media=None):
    try:
        if media is None:
            if len(text) > MAX_LEN_TEXT:
                lines = segmentizeText(text)
                nb_lines = len(lines)
                for counter in range(nb_lines):
                     txt = '{} {}/{}'.format(lines[counter], counter + 1, nb_lines)
                     if counter == 0:
                         if reply_to is None:
                             status = api.update_status(status=text) 
                         else:
                             status = api.update_status(status=text, in_reply_to_status_id=reply_to) 
                     else:
                         status = api.update_status(status=text, in_reply_to_status_id=reply_to) 
                     reply_to = status.id
            else:
                if reply_to is None:
                    status = api.update_status(status=text)
                else:
                    status = api.update_status(status=text, in_reply_to_status_id=reply_to) 
        else:
            if reply_to is None:
                status = api.update_with_media(status=text, filename=media) 
            else:
                status = api.update_with_media(status=text, filename=media, in_reply_to_status_id=reply_to) 
    except tweepy.RateLimitError as e:
        print('API Rate Limits atteintes ! Veuillez patienter 15mn')
        exit(1)
    except tweepy.TweepError as e:
        try:
            print(e.args[0][0]['code'], ':', e.args[0][0]['message'])
            print('Plus d\iinfos sur : https://dev.twitter.com/overview/api/response-codes')
        except Exception:
            print(e)
        exit(2)

def getLastId(filename='.lastTweetId'):
    try:
        with open(filename, 'r') as fic:
            id = int(fic.read())
    except IOError:
        print('IOError sur fichier {} : on utilise l\'identifiant 0'.format(filename))
        return 0
    return id

def saveLastId(id, filename='.lastTweetId'):
    last_id = getLastId(filename)

    if last_id < id:
        print('Sauvegarde de l\'id {}'.format(id))
        try:
            with open(filename, 'w') as fic:
                fic.write(str(id))
        except IOError:
            print('IOError lors de l\'écriture dans {}'.format(filename))
            exit(3)
    else:
        print('Identifiant inférieur au dernier identifiant sauvegardé : pas de sauvegarde')

def response(api):
    try:
        id = getLastId()
        followers = api.followers_ids()
        print(followers)
        to_me = api.mentions_timeline()
        for message in to_me:
            if message.id > id and message.user.id in followers:
                tweet(api, 'Salut @{} !'.format(message.user.screen_name), message.user.id)
                saveLastId(message.id)
    except tweepy.RateLimitError as e:
        print('API Rate Limits atteintes ! Veuillez patienter 15mn')
        exit(1)
    except tweepy.TweepError as e:
        try:
            print(e.args[0][0]['code'], ':', e.args[0][0]['message'])
            print('Plus d\iinfos sur : https://dev.twitter.com/overview/api/response-codes')
        except Exception:
            print(e)
        exit(2)

def retweet(api, authorizedUsers):
    try:
        id = getLastId()
        for user in authorizedUsers:
            tweets = tweepy.Cursor(api.user_timeline, screen_name=user).items()
            for tweet in tweets:
                if tweet.id > id:
                    if random.randint(1, 5) == 1:
                        api.retweet(tweet.id)
                        print('On retweete {} !'.format(tweet.id))
                    saveLastId(tweet.id)
    except tweepy.RateLimitError as e:
        print('API Rate Limits atteintes ! Veuillez patienter 15mn')
        exit(1)
    except tweepy.TweepError as e:
        try:
            print(e.args[0][0]['code'], ':', e.args[0][0]['message'])
            print('Plus d\iinfos sur : https://dev.twitter.com/overview/api/response-codes')
        except Exception:
            print(e)
        exit(2)

def analyze(text):
    data = text.split(' ')
    if data.pop(0).lower() == '@twitbotessai':
        action = data.pop(0).lower()
        if action == 'magazine':
            mag = data.pop(0).lower()
            #if len(data) != 0:
            #    return ''
            msg = 'Rédacteur en chef de {} ({}) : {} ({})'
            if mag == '@gnulinuxmag':
                return msg.format('GNU/Linux Magazine', '@gnulinuxmag', 'Tristan Colombo', '@TristanColombo')
            elif mag == '@hackablemag':
                return msg.format('Hackable Magazine', '@hackablemag', 'Denis Bodor', '@Lefinnois')
            elif mag == '@miscredac':
                return msg.format('MISC', '@MISCRedac', 'Cédric Foll', '@follc')
            elif mag == '@linuxpratique':
                return msg.format('Linux Pratique', '@linuxpratique', 'Aline Hof', '404 not found')
    return ''

def robot(api):
    try:
        id = getLastId()
        followers = api.followers_ids()
        to_me = api.mentions_timeline()
        for message in to_me:
            if message.id > id and message.user.id in followers:
                response = analyze(message.text)
                if response != '':
                    tweet(api, '@{} {}'.format(message.user.screen_name, response), message.id_str)
                saveLastId(message.id)
    except tweepy.RateLimitError as e:
        print('API Rate Limits atteintes ! Veuillez patienter 15mn')
        exit(1)
    except tweepy.TweepError as e:
        try:
            print(e.args[0][0]['code'], ':', e.args[0][0]['message'])
            print('Plus d\iinfos sur : https://dev.twitter.com/overview/api/response-codes')
        except Exception:
            print(e)
        exit(2)

if __name__ == '__main__':
    cfg = readconfig()
    api = get_api(cfg)
    robot(api)
