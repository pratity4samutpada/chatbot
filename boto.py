'''
This is the template server side for ChatBot
'''
from bottle import route, run, template, static_file, request
import json, wikipedia, random, pyowm

owm = pyowm.OWM('524191550297424084f474476a82a0dc')

swear_counter = 0
boto_mad = False
user_name = ""


##BOT LOGIC##
def bot_reply(animation, message):
    return {'animation': animation, 'msg': message}


def handle_swears():
    global swear_counter
    global boto_mad
    swear_counter += 1
    if swear_counter > len(response_dict['swearresponses']):
        boto_mad = True
        return bot_reply('heartbroke', 'You\'ve hurt my feelings.')
    else:
        return bot_reply('crying', response_dict['swearresponses'][swear_counter - 1])


def user_cursing(l):
    if any(x in l for x in response_dict['badwords']):
        return True
    return False


def boto_is_mad(l):
    global boto_mad
    global swear_counter
    if any(x in l for x in response_dict['apologies']):
        boto_mad, swear_counter = False, 0
        return bot_reply('ok', 'I forgive you!')
    else:
        return bot_reply('no', 'I demand an apology!')


def set_username(s):
    global user_name
    opener = [item for item in response_dict["namestrings"] if item in s]
    if opener and opener[0] in s:
        user_name = s.split(opener[0], 1)[1]
    else:
        user_name = s[:-1]
    greeting = 'Nice to meet you, {0}'.format(user_name)
    return bot_reply('dancing', greeting)


def question(l, punct):
    q = ['?', 'what', 'why', 'how', 'when', 'who', 'whose']
    if any(x in l for x in q) or punct in q:
        return True
    return False


def handle_q(s):
    q = ['what', 'why', 'how', 'when', 'who', 'whose', '?']
    q_word = [item for item in q if item in s][0]
    reply, q_content = "I dunno...", s.split(q_word)[1]
    if q_word is 'what':
        reply = what_q(q_content[:-1])

    return bot_reply('confused', reply)


def what_q(s):
    resp = analyze_what_content(s)
    return resp


def analyze_what_content(s):
    if "can" in s[0:6]:
        return boto_can_do()
    elif "is" or "\'s" in s[0:3]:
        return search_wiki(s)


def search_wiki(s):
    query = s[3:].strip()
    return wikipedia.summary(query)


def boto_can_do():
    capabilities = ['Tell you what things are (just ask)', 'Tell jokes (type \'joke\')',
                    'Tell you the weather (type \'weather\')',
                    'add (\'add x and y and...\') and subtract integers (\'subtract x from y from...\'']
    for i in range(len(capabilities)):
        capabilities[i] = str(i + 1) + '.' + capabilities[i] + "***"
    s = "Here's what I can do: " + "".join(capabilities)
    return s


def punctuated(s):
    if s[-1] not in ['.', '!', '?']:
        return False
    return True


def grammar_nazi():
    return bot_reply('dog', 'Can you please punctuate your sentence?')


def tell_joke(a):
    joke = response_dict['jokes'][random.randint(0, len(response_dict['jokes']) - 1)]
    return bot_reply('giggling', joke)


def add(l):
    total = sum([int(i) if type(i) is not int else i for i in l[1::2]])
    return bot_reply('money', str(total))


def subtract(l):
    to_sub = [int(i) for i in l[1::2]]
    diff, i = to_sub[-1], len(to_sub) - 2
    while i >= 0:
        diff -= to_sub[i]
        i -= 1
    return bot_reply('bored', str(diff))

def weather(l):
    s = ' '.join(l)
    location = "".join(s.split("in",1)[1])
    obs = owm.daily_forecast(location, limit=6)
    cast = []
    for weather in obs.get_forecast():
        cast.append(weather.get_status())
    return bot_reply('afraid','Six Day Forecast for '+location+': '+', '.join(cast)+'.')

commands = {'joke': tell_joke, 'add': add, 'subtract': subtract,'weather':weather}


# First get request when server runs.
@route('/', method='GET')
def index():
    return template('chatbot.html')


@route('/chat', method='POST')
def chat():
    global user_name
    global boto_mad
    user_message = request.POST.get('msg').lower()
    strings_in_message = user_message[:-1].split(' ')
    punct = user_message[-1]
    if not punctuated(user_message):
        return json.dumps(grammar_nazi())
    if not user_name:
        return json.dumps(set_username(user_message))
    if boto_mad:
        return json.dumps(boto_is_mad(strings_in_message))
    if user_cursing(strings_in_message):
        return json.dumps(handle_swears())
    if question(strings_in_message, punct):
        return handle_q(user_message)
    if any(x in strings_in_message for x in commands):
        if len(strings_in_message) == 1:
            return json.dumps(commands[user_message[:-1]](strings_in_message))
        return json.dumps(commands[strings_in_message[0]](strings_in_message))
    return json.dumps({'animation': 'inlove', 'msg': user_message[:-1]+", "+user_name+"!"})


@route('/test', method='POST')
def chat():
    user_message = request.POST.get('msg')
    return json.dumps({'animation': 'inlove', 'msg': user_message})


# Static file, loads initially.
@route('/js/<filename:re:.*\.js>', method='GET')
def javascripts(filename):
    return static_file(filename, root='js')


# Static file, loads initially.
@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='css')


@route('/txt/<filename:re:.*\namestrings.txt>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='txt')


@route('/images/<filename:re:.*\.(jpg|png|gif|ico)>', method='GET')
def images(filename):
    return static_file(filename, root='images')


# Loads different kinds of response lists, stores them in  dictionary.
responses = ['apologies', 'badwords', 'swearresponses', 'namestrings', 'jokes']
response_dict = {}
for file in responses:
    with open('txt/' + file + '.txt') as words:
        response_dict[file] = words.read().splitlines()


def main():
    run(host='localhost', port=7003)


if __name__ == '__main__':
    main()
