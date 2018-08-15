# -*- coding: utf-8 -*-
import telebot
import cherrypy
from cherrypy import request
from config import * # token, ip_address, port
from re import search
from datetime import datetime
from time import mktime
from telebot.types import (
    InlineKeyboardButton as B, InlineKeyboardMarkup as M,
    InlineQueryResultPhoto, InlineQueryResultGif,
    InputTextMessageContent
    )
bot = telebot.TeleBot(token)
WEBHOOK_HOST = ip_address
WEBHOOK_PORT = port  #443,80,88 or 8443,port must be open; I use 8443
WEBHOOK_LISTEN = '0.0.0.0'#on some servers need to be as WEBHOOK_HOST
WEBHOOK_SSL_CERT = '../webhook/webhook_cert.pem'
WEBHOOK_SSL_PRIV = '../webhook/webhook_pkey.pem'
WEBHOOK_URL_BASE = 'https://%s:%s' % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = '/%s/' % token
# constants
games = []
text_games = []
Xsgn = '❌'
Osgn = '⭕️'
winsgn = '🏆'
losesgn = '☠️'
cell='⬜️'
tiesgn = '🤜🤛'
turnsgn = ' 👈'
settingscall = '[en|ua|ru|sr]S|cnl'
callback_text = '-[\d|{}|{}]'.format(Xsgn,Osgn)
callback = '=[\d\d|{}|{}]|cancel|tie|giveup|confirm'.format(Xsgn,Osgn)
languages = {
      'en':{
        'start':'Choose your side and get started!','bot':'Bot',
        'don’t touch':'Oh, don’t touch this)','cnld':'Canceled',
        'win':'Oh, victory!','lose':'You loooose… Try harder!',
        'tie':'It is really tie?','new':'Start a new game?',
        'stop':'Stop! Wait your turn','oh':'Oh shit!',
        'stop+game':'Stop! There already playing','dotie':'Tie',
        'again':'Oh, try again…','confirmtie':'Accept tie?',
        'confirmloss':'Confirm giving up!','start-pl-2':'Let’s go!',
        'player':'Player','gu_done':'gives up','giveup':'Give up',
        'cnl':'Cancel','startN':'Choose size and get started!'
    },'ua':{
        'start':'Обирай сторону і почнімо!','bot':'Бот',
        'don’t touch':'Ой, да не тикай сюди!','cnld':'Відмінено',
        'win':'Вау, перемога!','lose':'О, ні, знову програш…',
        'tie':'Невже нічия?','new':'Зіграємо ще раз?',
        'stop':'Стоп! Не твій хід!','oh':'Бляха…',
        'stop+game':'Стоп! Тут уже грають!','dotie':'Нічия',
        'again':'Спробуй ще раз…','confirmtie':'Приймаєш нічию?',
        'confirmloss':'Підтвердь програш!','start-pl-2':'Почнімо!',
        'player':'Гравець','gu_done':'здався','giveup':'Здатися',
        'cnl':'Відміна','startN':'Обирай розмір і почнімо!'
    },'ru':{
        'start':'Выбери сторону и начнём!','bot':'Бот',
        'don’t touch':'Ой, да не тыкай сюда!','cnld':'Отменено',
        'win':'Вау победа!','lose':'О, нет, опять проиграш…',
        'tie':'Неужели ничья?','new':'Сыграем ещё раз?',
        'stop':'Стопэ! Не твой ход!','oh':'Ляя…',
        'stop+game':'Стопэ! Здесь уже играют!','dotie':'Ничья',
        'again':'Попробуй ещё раз…','confirmtie':'Принимаешь ничью?',
        'confirmloss':'Подтвердите проиграш!','start-pl-2':'Начнём!',
        'player':'Игрок','gu_done':'сдался','giveup':'Сдаться',
        'cnl':'Отмена','startN':'Выбери размер и начнём!'
    },'sr':{
        'start':'Изаберите страну и почните!','bot':'Бот',
        'don’t touch':'Ох, да не идите овде!','cnld':'Промењено',
        'win':'О, ти победио!','lose':'О, не, изгубио си…',
        'tie': 'Стварно жреб?','new':' Се поново играти??',
        'stop':'Стани! Не твој потез!',' oh':'Бре…',
        'stop+game':'Стоп! Овде је већ играју!',
        'again': 'Пробајте поново…','start-pl-2':'Почнемо!',
        'confirmtie':'Да ли прихватате жребање?',
        'confirmloss':'Потврди губитника!','dotie':'жреб',
        'player':'Играч','gu_done':'одустаје','giveup':'одустати',
        'cnl':'Отказ','startN':'Изаберите величине и почните!'
    }}
free = lambda a: a!=Xsgn and a!=Osgn
last_of_three = lambda b,x,y,z,s:\
    z if b[x]==b[y]==s and free(b[z]) else\
    y if b[x]==b[z]==s and free(b[y]) else\
    x if b[y]==b[z]==s and free(b[x]) else -1
resultfunc = lambda n,s,q,c: [InlineQueryResultPhoto(
    f'{n}{s}{q.id}',
    f't.me/lviv_lamptest/{2019+6*n+s}',
    f't.me/lviv_lamptest/{675+n*2}',
    reply_markup=c,
    input_message_content=InputTextMessageContent(
    f'{Xsgn} ?{turnsgn}\n{Osgn} ?')
    )]
def board_text(board,size,b=''):
    for i in range(size):
        for j in range(size):
            b += board[i*size+j]
        b += '\n'
    return b
def winxo(b,s,sz):
    assert 9>sz>2
    if sz==3:
        if b[0]==b[4]==b[8]==s or\
           b[2]==b[4]==b[6]==s:
            return True
        for i in range(3):
            if b[i*3]==b[i*3+1]==b[i*3+2]==s or\
               b[i]==b[i+3]==b[i+6]==s:
               return True
    elif sz<8:
        for i in range(sz-3):
            for j in range(sz-3):
                k=i+j*sz
                if  b[k]==b[k+sz+1]==b[k+sz*2+2]==b[k+sz*3+3]==s or\
                    b[k+3]==b[k+2+sz]==b[k+1+sz*2]==b[k+sz*3]==s:
                    return True
                for l in range(4):
                    u=k+l*sz
                    v=k+l
                    if  b[u]==b[u+1]==b[u+2]==b[u+3]==s or\
                        b[v]==b[v+sz]==b[v+sz*2]==b[v+sz*3]==s:
                        return True
    else:
        #only for sz==8
        for i in range(4):
            for j in range(4):
                k=i+j*sz
                if  b[k]==b[k+9]==b[k+18]==b[k+27]==b[k+36]==s or\
                    b[k+4]==b[k+11]==b[k+18]==b[k+25]==b[k+32]==s:
                    return True
                for l in range(5):
                    u=k+l*8
                    v=k+l
                    if  b[u]==b[u+1]==b[u+2]==b[u+3]==b[u+4]==s or\
                        b[v]==b[v+8]==b[v+16]==b[v+24]==b[v+32]==s:
                        return True
    return False
def end(g,text,w,l,cid):
    b_text = board_text(g.b,g.s)
    button=M()
    button.add(
        B(Xsgn,switch_inline_query_current_chat='x'+str(g.s)),
        B(Osgn,switch_inline_query_current_chat='o'+str(g.s))
        )
    bot.edit_message_text(
        inline_message_id=cid,
        text=b_text+text,
        reply_markup=button
        )
    games.remove(g)
    bot.answer_callback_query(
        g.call[g.queue].id,
        text=w,
        show_alert=True
        )
    return bot.answer_callback_query(
        g.call[not g.queue].id,
        text=l,
        show_alert=True
        )
def game_xo(g,choice,t,cid):
    name_X = g.playerX.first_name if g.playerX else '?'
    name_O = g.playerO.first_name if g.playerO else '?'
    g.b[int(choice[1:])] = [Osgn,Xsgn][g.queue]
    win=winxo(g.b,g.b[int(choice[1:])],g.s)
    if win:
        if g.queue:
            sign_X,sign_O = [winsgn,losesgn]
        else:
            sign_X,sign_O = [losesgn,winsgn]
        return end(g,f'''
                {Xsgn} {name_X} {sign_X}
                {Osgn} {name_O} {sign_O}
            '''.replace('    ',''),
            t['win'],
            t['lose'],
            cid)
    elif not cell in g.b:
        return end(g,f'''
                {Xsgn} {name_X} {tiesgn} {name_O} {Osgn}
            '''.replace('    ',''),
            t['tie'],
            t['tie'],
            cid)
    g.queue = not g.queue # pass turn
    button = M(row_width=g.s)
    button.add(*[
        B(  g.b[i],
            callback_data=f'={i:02}' if g.b[i]==cell else g.b[i])
        for i in range(g.s**2)
        ])
    button.add(
        B(t['dotie'],callback_data='tie'),
        B(t['giveup'],callback_data='giveup')
        )
    return bot.edit_message_text(inline_message_id=cid,
        text=f'''
                {Xsgn} {name_X}{turnsgn*g.queue}
                {Osgn} {name_O}{turnsgn*(not g.queue)}
            '''.replace('    ',''),
            reply_markup=button
            )
def my_choice_func(b,msgn,sgn):
    if not (cell in b):
        return -1
    for s in [msgn,sgn]:
        for i in range(3):
            for x,y,z in [[3*i,3*i+1,3*i+2],[i,i+3,i+6]]:
                res = last_of_three(b,x,y,z,s)
                if res>-1: return res
        for x,y,z in [[0,4,8],[2,4,6]]:
            res = last_of_three(b,x,y,z,s)
            if res>-1: return res
    for i,j,k,l,r in [
        (1,3,1,5,2),(3,7,5,7,8),(2,6,0,8,1),(2,3,0,5,1),
        (3,8,5,6,7),(1,6,0,7,3),(1,8,2,7,5),(4,8,4,8,2)]:
            if (b[i]==b[j]==sgn or b[k]==b[l]==sgn) and free(b[r]):
                return r
    for i in range(9):
        if free(b[i]):
            return i
class Timeout:
    for g in games:
        delta = mktime(datetime.now().timetuple()) - g.time
        if  delta >= 600:
            bot.edit_message_text(
                inline_message_id=g.id,
                text='⌛️')
            games.remove(g)
    for g in text_games:
        delta = mktime(datetime.now().timetuple()) - g.time
        if delta >= 600:
            bot.edit_message_text(
                '⌛️',
                g.out.chat.id,
                g.out.message_id
                )
            text_games.remove(g)
class User:
    out = False
    def __init__(self,id,language='ua'):
        self.id = id
        self.t = languages[language]
class Game_text:
    isX = False; b = []
    def __init__(self,out,time):
        self.out=out
        self.time=time
class Game:
    playerX=playerO=tie_id=giveup_user=newcall = None
    time=out = 0
    queue = True
    b = []
    s = 3
    call = [None,None]
    def __init__(self,id):
        self.id=id
        try:
            self.lastcall=self.call[not self.call.index(newcall)]
        except: pass
users=[User(id=0)]
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in request.headers and \
                'content-type' in request.headers and \
                request.headers['content-type'] == 'application/json':
            length = int(request.headers['content-length'])
            json_string = request.body.read(length).decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)
@bot.message_handler(commands=['settings'])
def settingscommand(m):
    button = M(row_width=4)
    button.add(
        B('Eng',callback_data='enS'),
        B('Ukr',callback_data='uaS'),
        B('Rus',callback_data='ruS'),
        B('Srp',callback_data='srS'),
        B('Cancel',callback_data='cnl')
    )
    out = bot.send_message(m.chat.id,'''
        Choose language to play
        Обери мову, якою гратимеш
        Выбери язык, которым будеш играть
        Изаберите језик да игра
        '''.replace('    ',''),reply_markup=button)
    for user in users:
        if m.from_user.id==user.id:
            users.remove(user)
    u = User(id=m.from_user.id); u.out = out; users.append(u)
@bot.callback_query_handler(lambda c: search(settingscall,c.data))
def settings(c):
    for u in users:
        if c.from_user.id==u.id:
            if c.data=='cnl':
                return bot.edit_message_text(
                'Canceled              Відмінено\n'+\
                'Отменено           Отказ',
                c.message.chat.id,
                u.out.message_id)
            elif not languages[c.data[:2]]==u.t:
                u.t = languages[c.data[:2]]
            bot.edit_message_text(
            '✔️Done            ✔️Готово\n'+\
            '✔️Сделано      ✔️Готово',
            c.message.chat.id,
            u.out.message_id)
@bot.message_handler(commands=['x','o','start','new','game'])
def xotext(m):
    tx = False; t = m.text; button = M()
    for user in users:
        if m.chat.id==user.id: tx = user.t
    try: assert tx
    except: tx = users[0].t
    if search('start|new|game',t):
        return bot.send_message(
            m.chat.id,
            f"{tx['start']}\n"+\
            '             /x                        /o'
            )
    for game in text_games:
        if m.chat.id==game.out.chat.id:
            bot.edit_message_text(
                '♻️',
                m.chat.id,
                game.out.message_id
                )
            text_games.pop(game)
    name = m.from_user.first_name
    now = mktime(datetime.now().timetuple())
    if 'x' in t:
        button.add(*[
        B(  cell,
            callback_data=f'-{i}')
        for i in range(9)
        ])
        out = bot.send_message(
            m.chat.id,
            f'''
                {Xsgn} {name}{turnsgn}
                {Osgn} {tx['bot']}
            '''.replace('    ',''),
            reply_markup=button
            )
        g = Game_text(out=out,time=now)
        g.isX = True
        g.b = [cell]*9
        text_games.append(g)
    elif 'o' in t:
        button.add(*[
            B(  cell,
                callback_data=f'-{i}'
            ) if i!=4 else
            B(  Xsgn,
                callback_data=f'-{Xsgn}'
            ) for i in range(9)
            ])
        out = bot.send_message(
            m.chat.id,
            f'''
                {Xsgn} {tx['bot']}
                {Osgn} {name} {turnsgn}
            '''.replace('    ',''),
            reply_markup=button
            )
        g = Game_text(out=out,time=now)
        g.isX = False
        g.b = [cell if i!=4 else Xsgn for i in range(9)]
        text_games.append(g)
@bot.callback_query_handler(lambda c: search(callback_text,c.data))
def xogame(c):
    m = c.message
    button = M()
    for user in users:
        if m.chat.id==user.id:
            t=user.t
    try: assert t
    except:
        t = users[0].t
    player = c.from_user.first_name
    for game in text_games:
        if m.chat.id==game.out.chat.id:
            g = game
    try: assert g
    except:
        bot.edit_message_text(
            '♻️',
            m.chat.id,
            m.message_id
            )
        return bot.answer_callback_query(
            c.id,
            text=t['don’t touch']
            )
    sign,my_sign = [Xsgn,Osgn] if g.isX else [Osgn,Xsgn]
    if not free(c.data[1:]):
        return bot.answer_callback_query(
            c.id,
            text=t['don’t touch']
            )
    choice = int(c.data[1])
    g.b[choice] = sign
    my_choice = my_choice_func(g.b,my_sign,sign)
    if free(g.b[4]): my_choice = 4
    if my_choice >- 1:
        g.b[my_choice] = my_sign
    name_X = player if g.isX else t['bot']
    name_O = t['bot'] if g.isX else player
    win = False
    b = g.b
    for s in Xsgn,Osgn:
        g.queue = False if s==Osgn else True
        if  b[0]==b[4]==b[8]==s or\
            b[2]==b[4]==b[6]==s:
            win = True
        for i in range(3):
            if  b[i*3]==b[i*3+1]==b[i*3+2]==s or\
                b[i]==b[3+i]==b[6+i]==s:
                win = True
        if win:
            b_text = ''
            for i in range(3):
                b_text += f'{b[3*i]}{b[3*i+1]}{b[3*i+2]}\n'
            if g.queue:
                sign_X,sign_O = [winsgn,losesgn]
            else:
                sign_X,sign_O = [losesgn,winsgn]
            bot.edit_message_text(f'''
                    {b_text}
                    {Xsgn} {name_X} {sign_X}
                    {Osgn} {name_O} {sign_O}
                    {t['new']}\n'''.replace('    ','')+\
                    '      /x            /o',
                m.chat.id,
                g.out.message_id)
            text_games.remove(g)
            if s==sign:
                return bot.answer_callback_query(
                    c.id,
                    text=t['win'],
                    show_alert=True
                    )
            elif s==my_sign:
                return bot.answer_callback_query(
                c.id,
                text=t['lose'],
                show_alert=True
                )
    if not cell in b :
        b_text = ''
        for i in range(3):
            b_text += f'{b[3*i]}{b[3*i+1]}{b[3*i+2]}\n'
        bot.edit_message_text(f'''
                {b_text}
                {Xsgn} {name_X} {tiesgn} {name_O}{Osgn}
                {t['new']}\n'''.replace('    ','')+\
                '      /x            /o',
            m.chat.id,
            g.out.message_id
            )
        bot.answer_callback_query(
            c.id,
            text=t['tie'],
            show_alert=True
            )
        text_games.remove(g)
    else:
        button.add(*[
            B(  g.b[i],
                callback_data=f'-{i}' if b[i]==cell else f'-{b[i]}'
                ) for i in range(9)])
        bot.edit_message_text(
            f'''
                {Xsgn} {name_X}{turnsgn}
                {Osgn} {name_O}
            '''.replace('    ',''),
            m.chat.id,
            g.out.message_id,
            reply_markup=button
            )
@bot.inline_handler(lambda q: True)
def inline(q):
    g = Game(id=q.id)
    games.append(g)
    tx=False
    for user in users:
        if q.from_user.id==user.id:
            tx = user.t
    try: assert tx
    except:
        tx = users[0].t
    g.time = mktime(datetime.now().timetuple())
    t = q.query.lower(); res = []
    cnl = M()
    cnl.add(B('Cancel',callback_data='cancelstart'))
    if not t:
        button = M()
        button.add(*[
            B(f'{i}',callback_data=f'start{i}')
            for i in range(3,9)
            ])
        if not 'o' in t:
            res += [InlineQueryResultGif(
            f'10{q.id}',
            't.me/lviv_lamptest/2256',
            't.me/lviv_lamptest/2256',
            reply_markup=button,
            input_message_content=\
            InputTextMessageContent(tx['startN'])
            )]
        if not 'x' in t:
            res += [InlineQueryResultGif(
            f'20{q.id}',
            't.me/lviv_lamptest/2257',
            't.me/lviv_lamptest/2257',
            reply_markup=button,
            input_message_content=\
            InputTextMessageContent(tx['startN'])
            )]
        return bot.answer_inline_query(q.id,res)
    if not any(n in t for n in '345678'):
        t = '345678'
    for s in range(3,9):
        if str(s) in t:
            if not 'o' in t: res += resultfunc(1,s,q,cnl)
            if not 'x' in t: res += resultfunc(2,s,q,cnl)
    if not 'x' in t.lower() and not 'o' in t.lower():
        res = [
            *[x for x in res if not res.index(x)%2],
            *[x for x in res if res.index(x)%2]
            ] # firstly go X-variants, secondly O-variants
    return bot.answer_inline_query(q.id,res)
@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen(cr):
    for game in games:
        if cr.result_id[2:] in game.id:
            game.id=cr.inline_message_id
            g = game
    try: assert g
    except:
        games.append(Game(id=cr.inline_message_id))
        g = games[-1]
    if cr.result_id[0]=='1':
        g.playerX = cr.from_user
    elif cr.result_id[0]=='2':
        g.playerO = cr.from_user
    g.s=int(cr.result_id[1])
    if g.s==0:
        return 1
    g.b=[cell for i in range(g.s**2)]
    g.time=mktime(datetime.now().timetuple())
    name_X = g.playerX.first_name if g.playerX else '?'
    name_O = g.playerO.first_name if g.playerO else '?'
    button=M(row_width=g.s)
    button.add(*[
        B(  g.b[i],
            callback_data=f'={i:02}'
        ) for i in range(g.s**2)
        ])
    bot.edit_message_text(
        inline_message_id=g.id,
        text=f'''
            {Xsgn} {name_X}{turnsgn}
            {Osgn} {name_O}
        '''.replace('    ',''),
        reply_markup=button
        )
@bot.callback_query_handler(lambda c: search('start\d',c.data))
def choicesize(c):
    g=False
    for game in games:
        if c.inline_message_id==game.id:
            g = game
    try: assert g
    except:
        return bot.edit_message_text(
            inline_message_id=c.inline_message_id,text='♻️')
    g.s=int(c.data[-1])
    g.b=[cell for i in range(g.s**2)]
    g.time=mktime(datetime.now().timetuple())
    if not g.playerX and g.playerO.id!=c.from_user.id:
        g.playerX=c.from_user
    elif not g.playerO and g.playerX.id!=c.from_user.id:
        g.playerO=c.from_user
    name_X = g.playerX.first_name if g.playerX else '?'
    name_O = g.playerO.first_name if g.playerO else '?'
    button=M(row_width=g.s)
    button.add(*[
        B(  g.b[i],
            callback_data=f'={i:02}'
        ) for i in range(g.s**2)
        ])
    bot.edit_message_text(
        inline_message_id=g.id,
        text=f'''
            {Xsgn} {name_X}{turnsgn}
            {Osgn} {name_O}
        '''.replace('    ',''),
        reply_markup=button
        )
@bot.callback_query_handler(lambda c: search(callback,c.data))
def xo(c):
    usid = c.from_user.id; t=g=False
    for game in games:
        if c.inline_message_id==game.id:
            g = game
    try: assert g
    except:
        return bot.edit_message_text(
            inline_message_id=c.inline_message_id,text='♻️')
    for user in users:
        if usid==user.id:
            t = user.t
    try: assert t
    except:
        t = users[0].t
    name_X = g.playerX.first_name if g.playerX else '?'
    name_O = g.playerO.first_name if g.playerO else '?'
    if c.data=='cancelend':
        g.tie_id = g.giveup_user = None
        button = M(row_width=g.s)
        button.add(*[
            B(  g.b[i],
                callback_data=f'={i:02}' if g.b[i]==cell else g.b[i])
            for i in range(g.s**2)
            ])
        return bot.edit_message_text(
            inline_message_id=c.inline_message_id,
            text=f'''
                {Xsgn} {name_X}{turnsgn*g.queue}
                {Osgn} {name_O}{turnsgn*(not g.queue)}
            '''.replace('    ',''),
            reply_markup=button
            )
    elif c.data=='cancelstart':
        games.remove(g)
        return bot.edit_message_text(
            inline_message_id=g.id,
            text=t['cnld']
            )
    elif c.data=='tie':
        if all(g.call):
            if usid in [g.call[0].from_user.id,g.call[1].from_user.id]:
                g.tie_id = usid
                button = M()
                button.add(
                    B(t['confirmtie'],callback_data='confirmtie'),
                    B(t['cnl'],callback_data='cancelend')
                    )
                return bot.edit_message_reply_markup(
                    inline_message_id=c.inline_message_id,
                    reply_markup=button
                    )
        return bot.answer_callback_query(
            c.id,
            t['don’t touch'],
            show_alert=True
            )
    elif g.tie_id:
        if g.tie_id != usid and g.playerX and g.playerO:
            return end(g,f'''
                {Xsgn} {name_X} {tiesgn} {name_O} {Osgn}
                {t['cnld']}
            '''.replace('    ',''),
            t['tie'],
            t['tie'],
            c.inline_message_id
            )
        return bot.answer_callback_query(
            c.id,
            t['don’t touch'],
            show_alert=True
            )
    elif c.data=='giveup':
        if all(g.call):
            if usid in [g.call[0].from_user.id,g.call[1].from_user.id]:
                g.giveup_user=c.from_user
                button = M()
                button.add(
                    B(t['confirmloss'],callback_data='confirmloss'),
                    B(t['cnl'],callback_data='cancelend')
                    )
                return bot.edit_message_reply_markup(
                    inline_message_id=c.inline_message_id,
                    reply_markup=button
                    )
        return bot.answer_callback_query(
            c.id,
            t['don’t touch'],
            show_alert=True
            )
    elif g.giveup_user:
        if g.giveup_user.id==usid and g.playerO and g.playerX:
            if g.playerO.id==usid:
                sign_X,sign_O = winsgn,losesgn
                resX,resO = t['win'],t['lose']
            else:
                sign_X,sign_O = losesgn,winsgn
                resX,resO = t['lose'],t['win']
            return end(g,f'''
            {Xsgn} {name_X} {sign_X}
            {Osgn} {name_O} {sign_O}
            {t['player']} {g.giveup_user.first_name} {t['gu_done']}
                '''.replace('    ',''),
                resX,
                resO,
                c.inline_message_id
                )
        return bot.answer_callback_query(
            c.id,
            t['don’t touch'],
            show_alert=True
            )
    elif not free(c.data):
        Timeout()
        if g.lastcall:
            bot.answer_callback_query(
                g.lastcall.id,
                '⏰',
                show_alert=True
                )
        return bot.answer_callback_query(
            c.id,
            text=t['don’t touch'],
            show_alert=True
            )
    if g.playerX:
        if g.playerX.id==c.from_user.id:
            g.call[1] = g.newcall = c
            if g.queue:
                return game_xo(
                    g,c.data,t,c.inline_message_id
                    )
            return bot.answer_callback_query(c.id,text=t['stop'])
        elif not g.playerO:
            g.playerO = c.from_user
            bot.answer_callback_query(c.id,text=t['start-pl-2'])
        if g.playerO.id==c.from_user.id:
            g.call[0] = g.newcall = c
            if not g.queue:
                return game_xo(
                    g,c.data,t,c.inline_message_id
                    )
            return bot.answer_callback_query(c.id,text=t['stop'])
        return bot.answer_callback_query(c.id,text=t['stop+game'])
    elif g.playerO.id!=c.from_user.id:
        g.call[1] = g.newcall = c
        if g.queue:
            g.playerX = c.from_user
            bot.answer_callback_query(c.id,text=t['start-pl-2'])
            return game_xo(
                g,c.data,t,c.inline_message_id
                )
        return bot.answer_callback_query(c.id,text=t['stop'])
    return bot.answer_callback_query(c.id,text=t['don’t touch'])
bot.remove_webhook()
bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    certificate=open(WEBHOOK_SSL_CERT, 'r')
    )
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV})
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
