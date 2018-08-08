# -*- coding: utf-8 -*-
import telebot,cherrypy
from config import *
from re import search
from datetime import datetime
from time import mktime
from telebot.types import InlineKeyboardMarkup as M,InputTextMessageContent as C,InlineQueryResultPhoto as P,InlineQueryResultGif as G,InlineKeyboardButton as B
bot=telebot.TeleBot(token)
WEBHOOK_HOST = ip_address
WEBHOOK_PORT = port  # 443, 80, 88 or 8443 port must be open; I use 8443
WEBHOOK_LISTEN = '0.0.0.0' # on some servers need to be as WEBHOOK_HOST
WEBHOOK_SSL_CERT = '../webhook/webhook_cert.pem'
WEBHOOK_SSL_PRIV = '../webhook/webhook_pkey.pem'
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token
games=[]; text_games=[]
class WebhookServer(object):
    Timeout()
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)
languages={
    'en':{
        'start':'Choose your side and get started!','bot':'Bot','don’t touch':'Oh, don’t touch this)','cnl':'Canceled',
        'win':'Oh, victory!','lose':'You loooose… Try harder!','tie':'It is really tie?','new':'Start a new game?',
        'stop':'Stop! Wait your turn','stop+game':'Stop! There already playing','oh':'Oh shit!','again':'Oh, try again…',
        'wait':'Wait your opponent to start!','start-pl-2':'Let’s go!','size':'Sorry, I can do board this size'
    },
    'ua':{
        'start':'Обирай сторону і почнімо!','bot':'Бот','don’t touch':'Ой, да не тикай сюди!','cnl':'Відмінено',
        'win':'О, ти переміг!','lose':'О, ні, ти програв…','tie':'Невже нічия?','new':'Зіграємо ще раз?',
        'stop':'Стоп! Не твій хід!','stop+game':'Стоп! Тут уже грають!','oh':'Бляха…','again':'Спробуй ще раз…',
        'wait':'Зачекай-но товариша!','start-pl-2':'Почнімо!','size':'Я не можу робити гру таких розмірів!'
    },
    'ru':{
        'start':'Выбери сторону и начнём!','bot':'Бот','don’t touch':'Ой, да не тыкай сюда!','cnl':'Отменено',
        'win':'О, ты победил!','lose':'О, нет, ти проиграл…','tie':'Неужели ничья?','new':'Сыграем ещё раз?',
        'stop':'Стопэ!','stop+game':'Стопэ! Здесь уже играют!','oh':'Ляя…','again':'Попробуйте ещё раз…',
        'wait':'Подожди противника!','start-pl-2':'Начнём!','size':'Я не могу делать игры таких размеров!'
    }}
f=lambda a: True if a!='❌' and a!='⭕️' else False
fo = lambda b,x,y,z,s: z if b[x]==b[y]==s and f(b[z]) else y if b[x]==b[z]==s and f(b[y]) else x if b[y]==b[z]==s and f(b[x]) else -1
def winxo(b,s,sz):
    if sz==3:
        if b[0]==b[4]==b[8]==s or b[2]==b[4]==b[6]==s:
            return True
        for i in range(3):
            if b[i*3]==b[i*3+1]==b[i*3+2]==s or b[i]==b[3+i]==b[6+i]==s:
                return True
        return False
    for i in range(sz-3):
        for j in range(sz-3):
            k=i+j*sz
            if b[k]==b[k+sz+1]==b[k+(sz+1)*2]==b[k+(sz+1)*3]==s:
                return True
            if b[k+3]==b[k+3+(sz-1)]==b[k+3+(sz-1)*2]==b[k+3+(sz-1)*3]==s:
                return True
            for l in range(4):
                if b[k+l*sz]==b[k+l*sz+1]==b[k+l*sz+2]==b[k+l*sz+3]==s:
                    return True
                if b[k+l]==b[k+l+sz]==b[k+l+sz*2]==b[k+l+sz*3]==s:
                    return True
    return False
def game_xo(g,c,pl1,t):
    name0=g.playerX.first_name if g.playerX else '?'
    name1=g.playerO.first_name if g.playerO else '?'
    if not f(c.data):
        return 1
    g.b[int(c.data)]=['❌','⭕️'][not g.queue]
    win=winxo(g.b,g.b[int(c.data)],g.s)
    buttons=M()
    if win:
        g.b_text=''
        for i in range(g.s):
            for j in range(g.s):
                g.b_text+=g.b[i*g.s+j]
            g.b_text+='\n'
        sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
        buttons.add(B('❌',switch_inline_query_current_chat='x'+str(g.s)),B(text='⭕️',switch_inline_query_current_chat='o'+str(g.s)))
        bot.edit_message_text(inline_message_id=c.inline_message_id,text=g.b_text+f'\n❌ {name0} '+sign_0+f'\n⭕️ {name1} '+sign_1,reply_markup=buttons)
        bot.answer_callback_query(g.call[g.queue].id,text=t['win'])
        bot.answer_callback_query(g.call[not g.queue].id,text=t['lose'])
        del games[games.index(g)]
    elif not '⬜️' in g.b:
        g.b_text=''
        for i in range(g.s):
            for j in range(g.s):
                g.b_text+=g.b[i*g.s+j]
            g.b_text+='\n'
        buttons.add(B('❌',switch_inline_query_current_chat='x'+str(g.s)),B(text='⭕️',switch_inline_query_current_chat='o'+str(g.s)))
        bot.edit_message_text(inline_message_id=c.inline_message_id,text=g.b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️',reply_markup=buttons)
        bot.answer_callback_query(g.call[0].id,text=t['tie'])
        bot.answer_callback_query(g.call[1].id,text=t['tie'])
        del games[games.index(g)]
    else:
        g.queue=not g.queue
        for i in range(g.s):
            buttons.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else f'{g.b[i*g.s+j]}') for j in range(g.s)])
        bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {name0}'+' 👈'*g.queue+f'\n⭕️ {name1}'+' 👈'*(not g.queue),reply_markup=buttons)
def my_choice_func(b,msgn,sgn):
    if not ('⬜️' in b):
        return -1
    for s in [msgn,sgn]:
        for i in range(3):
            for x,y,z in [[3*i,3*i+1,3*i+2],[i,i+3,i+6]]:
                res=fo(b,x,y,z,s)
                if res>-1: return res
        for x,y,z in [[0,4,8],[2,4,6]]:
            res=fo(b,x,y,z,s)
            if res>-1: return res
    for i,j,r in [(1,3,0),(1,5,2),(3,7,6),(5,7,8),(2,6,1),(0,8,1),(5,7,8),(2,3,1),(0,5,1),(3,8,7),(5,6,7),(1,6,3),(1,8,5),(0,7,3),(2,7,5)]:
            if b[i]==b[j]==sgn and f(b[r]):
                return r
    for i in range(9):
        if f(b[i]):
            return i
class Timeout:
    global games,text_games
    for g in games:
        if mktime(datetime.now().timetuple())-g.time>=600:
            bot.edit_message_text(inline_message_id=g.id,text='⌛️')
            del games[games.index(g)]
    for g in text_games:
        if mktime(datetime.now().timetuple())-g.time>=600:
            bot.edit_message_text('⌛️',game_text.out.chat.id,g.out.message_id)
            del text_games[text_games.index(g)]
class User:
    out=False
    def __init__(self,id,language='en'):
        self.id=id
        self.t=languages[language]
class Game_text:
    isX=False
    b=[]
    def __init__(self,out,time):
        self.out=out
        self.time=time
class Game:
    call=[0,0]
    time=0
    out=0
    playerX=None
    playerO=None
    queue=None
    b=[]
    size=3
    def __init__(self,id):
        self.id=id
users=[User(id=0)]
@bot.message_handler(commands=['settings'])
def setting(m):
    global users
    t=m.text
    buttons=M()
    buttons.add(B('Eng',callback_data='en'),B('Ukr',callback_data='ua'),B('Rus',callback_data='ru'),B('Cancel',callback_data='cnl'))
    out=bot.send_message(m.chat.id,
    'Choose language to play\nОбери мову, якою гратимеш\nВыбери язык, которым будеш играть',
    reply_markup=buttons)
    for user in users:
        if m.from_user.id==user.id:
            del users[users.index(user)]
    users.append(User(id=m.from_user.id,out=out))
@bot.callback_query_handler(lambda c: search('en|ua|ru|cnl',c.data))
def settings(c):
    global users
    for u in users:
        if c.from_user.id==u.id:
            if c.data=='cnl':
                return bot.edit_message_text('Canceled\nВідмінено\nОтменено',c.mesage.chat.id,u.out.message_id)
            if not languages[c.data]==u.t:
                u.t=languages[c.data]
            bot.edit_message_text('✔️Done\n✔️Готово\n✔️Сделано',c.message.chat.id,u.out.message_id)
@bot.message_handler(commands=['start','new','game'])
def newgame(m):
    tx=False
    for user in users:
        if m.chat.id==user.id: tx=user.t
    try: assert tx
    except: tx=users[0].t
    bot.send_message(m.chat.id,tx['start']+'\n             /x                        /o')
@bot.message_handler(commands=['x','o'])
def xotext(m):
    global text_games
    tx=False; t=m.text; buttons=M()
    for user in users:
        if m.chat.id==user.id: tx=user.t
    try: assert tx
    except: tx=users[0].t
    for game in text_games:
        if m.chat.id==game.out.chat.id: bot.edit_message_text('♻️',m.chat.id,game.out.message_id)
    name=m.from_user.first_name if m.from_user.first_name else 'None'
    now=mktime(datetime.now().timetuple())
    if 'x' in t:
        buttons.add(*[B('⬜️',callback_data=f'-{i}') for i in range(9)])
        out=bot.send_message(m.chat.id,f"❌ {name} 👈\n⭕️ {tx['bot']}",reply_markup=buttons)
        game=Game_text(out=out,time=now); game.isX=True; game.b=['⬜️']*9
        text_games.append(game)
    elif 'o' in t:
        buttons.add(*[B('⬜️',callback_data=f'-{i}') if i!=4 else B('❌',callback_data='-❌') for i in range(9)])
        out=bot.send_message(m.chat.id,f"❌ {tx['bot']} 👈\n⭕️ {name}",reply_markup=buttons)
        game=Game_text(out=out,time=now); game.isX=False; game.b=['⬜️' if i!=4 else '❌' for i in range(9)]
        text_games.append(game)
@bot.callback_query_handler(lambda c: search(r'-(\d|x|o)',c.data))
def xogame(c):
    global text_games
    m=c.message
    buttons=M()
    for user in users:
        if m.chat.id==user.id:
            t=user.t
    try: assert t
    except:
        t=users[0].t
    player = c.from_user.first_name if c.from_user.first_name else 'None'
    for game in text_games:
        if m.chat.id==game.out.chat.id:
            g=game
    try: assert g
    except:
        bot.edit_message_text('♻️',m.chat.id,m.message_id)
        return bot.answer_callback_query(c.id,text=t['don’t touch'])
    sign,my_sign=['❌','⭕️'] if g.isX else ['⭕️','❌']
    if search('\d',c.data[1]):
        choice=int(c.data[1])
        if f(g.b[choice]):
            g.b[choice]=sign
        else:
            bot.answer_callback_query(c.id,t['don’t touch'])
    my_choice=my_choice_func(g.b,my_sign,sign)
    if f(g.b[4]): my_choice=4
    if my_choice>-1:
        g.b[my_choice]=my_sign
    name0 = player if g.isX else t['bot']
    name1 = t['bot'] if g.isX else player
    win=False
    for s in ['❌','⭕️']:
        g.queue=False if s=='⭕️' else True
        if g.b[0]==g.b[4]==g.b[8]==s or g.b[2]==g.b[4]==g.b[6]==s:
            win=True
        for i in range(3):
            if g.b[i*3]==g.b[i*3+1]==g.b[i*3+2]==s or g.b[i]==g.b[3+i]==g.b[6+i]==s:
                win=True
        if win:
            b_text=''
            for i in range(3):
                b_text+=f'{g.b[3*i]}{g.b[3*i+1]}{g.b[3*i+2]}\n'
            sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
            bot.edit_message_text(b_text+f'\n❌ {name0} {sign_0}\n⭕️ {name1} {sign_1}\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
            if s==sign:
                bot.answer_callback_query(c.id,text=t['win'])
            elif s==my_sign:
                bot.answer_callback_query(c.id,text=t['lose'])
            del text_games[text_games.index(g)]
            break
    if win:
        return 0
    elif not '⬜️' in g.b :
        b_text=''
        for i in range(3):
            b_text+=f'{g.b[3*i]}{g.b[3*i+1]}{g.b[3*i+2]}\n'
        bot.edit_message_text(b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
        bot.answer_callback_query(c.id,text=t['tie'])
        del text_games[text_games.index(g)]
    else:
        buttons.add(*[B(g.b[i],callback_data=f'-{i}' if g.b[i]=='⬜️' else f'-{g.b[i]}') for i in range(9)])
        bot.edit_message_text(f'❌ {name0} 👈\n⭕️ {name1}',m.chat.id,g.out.message_id,reply_markup=buttons)
@bot.inline_handler(lambda q: True)
def inline(q):
    global games
    g=Game(id=q.id)
    g.time=mktime(datetime.now().timetuple())
    games.append(g)
    t=q.query; results=[]
    cnl=M(); cnl.add(B('Cancel',callback_data='cancelinline'))
    for s in range(3,9):
        xs=P('1'+str(s)+q.id,f't.me/lviv_lamptest/{2025+s}','t.me/lviv_lamptest/677',reply_markup=cnl,input_message_content=C('❌ ? 👈\n⭕️ ?'))
        os=P('2'+str(s)+q.id,f't.me/lviv_lamptest/{2031+s}','t.me/lviv_lamptest/679',reply_markup=cnl,input_message_content=C('❌ ? 👈\n⭕️ ?'))
        if str(s) in t:
            if not 'o' in t.lower(): results+=[xs]
            if not 'x' in t.lower(): results+=[os]
    if results: return bot.answer_inline_query(q.id,results)
    if not 'o' in t.lower():
        results+=[G('10'+q.id,'t.me/lviv_lamptest/2066','t.me/lviv_lamptest/677',reply_markup=cnl,input_message_content=C('❌ ? 👈\n⭕️ ?'))]
    if not 'x' in t.lower():
        results+=[G('20'+q.id,'t.me/lviv_lamptest/2067','t.me/lviv_lamptest/679',reply_markup=cnl,input_message_content=C('❌ ? 👈\n⭕️ ?'))]
    return bot.answer_inline_query(q.id,results)
@bot.chosen_inline_handler(func=lambda cr: True)
def chosen(cr):
    global games
    for game in games:
        if cr.result_id[2:]==game.id:
            game.id=cr.inline_message_id
            g=game
    try: assert g
    except:
        games.append(Game(id=cr.inline_message_id)); g=games[-1]
    result_id=cr.result_id[0]
    if result_id=='1':
        g.playerX=cr.from_user
    elif result_id=='2':
        g.playerO=cr.from_user
    g.s=int(cr.result_id[1])
    if g.s==0: g.s=3
    g.b=['⬜️' for i in range(g.s**2)]
    g.queue=True
    g.time=mktime(datetime.now().timetuple())
    name0=g.playerX.first_name if g.playerX else '?'
    name1=g.playerO.first_name if g.playerO else '?'
    button=M()
    for i in range(g.s):
        button.row(*[B('⬜️',callback_data=f'{i*g.s+j:02}') for j in range(g.s)])
    g.out=bot.edit_message_text(inline_message_id=g.id,text=f'❌ {name0} 👈\n⭕️ {name1}',reply_markup=button)
@bot.callback_query_handler(lambda c: search(r'\d\d|❌|⭕️|cancel',c.data) and c.data[0]!='-')
def xo(c):
    global games,users
    for game in games:
        if c.inline_message_id==game.id:
            g=game
    try: assert g
    except:
        return bot.edit_message_text(inline_message_id=c.inline_message_id,text='♻️')
    for user in users:
        if c.from_user.id==user.id:
            t=user.t
    try: assert t
    except:
        t=users[0].t
    if c.data=='cancelinline':
        return bot.edit_message_text(inline_message_id=g.id,text=t['cnl'])
    start=False
    if g.playerX:
        if g.playerX.id==c.from_user.id:
            g.call[1]=c
            if g.queue:
                game_xo(g,c,g.playerX,t)
            else:
                return bot.answer_callback_query(c.id,text=t['stop'])
        elif g.playerO:
            if g.playerO.id==c.from_user.id:
                g.call[0]=c
                if not g.queue:
                    game_xo(g,c,g.playerO,t)
                else:
                    return bot.answer_callback_query(c.id,text=t['stop'])
            else:
                bot.answer_callback_query(c.id,text=t['stop+game'])
        else:
            if not g.queue:
                g.playerO=c.from_user
                bot.answer_callback_query(c.id,text=t['start-pl-2'])
                buttons=M()
                for i in range(g.s):
                    buttons.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else g.b[i*g.s+j]) for j in range(g.s)])
                bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {g.playerX.first_name} 👈\n⭕️ {g.playerO.first_name}',reply_markup=buttons)
                game_xo(g,c,g.playerO,t)
            else:
                return bot.answer_callback_query(c.id,text=t['stop'])
    elif g.playerO!=c.from_user.id:
        if g.queue:
            g.playerX=c.from_user
            bot.answer_callback_query(c.id,text=t['start-pl-2'])
            buttons=M()
            for i in range(g.s):
                buttons.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else g.b[i*g.s+j]) for j in range(g.s)])
            bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {g.playerX.first_name} 👈\n⭕️ {g.playerO.first_name}',reply_markup=buttons)
            game_xo(g,c,g.playerX,t)
        else:
            return bot.answer_callback_query(c.id,text=t['stop'])
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV})
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
