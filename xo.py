# -*- coding: utf-8 -*-
import telebot,cherrypy
from config import *
from re import search
from datetime import datetime
from time import mktime,sleep
from telebot.types import InlineKeyboardMarkup as M,InputTextMessageContent as C,InlineQueryResultPhoto as P,InlineKeyboardButton as B
bot=telebot.TeleBot(token)
WEBHOOK_HOST = ip_address
WEBHOOK_PORT = port  # 443, 80, 88 or 8443 port must be open; I use 8443
WEBHOOK_LISTEN = '0.0.0.0' # on some servers need to be as WEBHOOK_HOST
WEBHOOK_SSL_CERT = '../webhook/webhook_cert.pem'
WEBHOOK_SSL_PRIV = '../webhook/webhook_pkey.pem'
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token
games=[]; text_games=[]
languages={
      'en':{
        'start':'Choose your side and get started!','bot':'Bot','don’t touch':'Oh, don’t touch this)','cnld':'Canceled','win':'Oh, victory!',
        'lose':'You loooose… Try harder!','tie':'It is really tie?','new':'Start a new game?','stop':'Stop! Wait your turn','oh':'Oh shit!',
        'stop+game':'Stop! There already playing','again':'Oh, try again…','start-pl-2':'Let’s go!','confirmloss':'Confirm giving up!',
        'confirmtie':'Accept tie?','player':'Player ','giveup_done':' gives up','dotie':'Tie','giveup':'Give up','cnl':'Cancel'
    },'ua':{
        'start':'Обирай сторону і почнімо!','bot':'Бот','don’t touch':'Ой, да не тикай сюди!','cnld':'Відмінено','win':'О, ти переміг!',
        'lose':'О, ні, ти програв…','tie':'Невже нічия?','new':'Зіграємо ще раз?','stop':'Стоп! Не твій хід!','oh':'Бляха…',
        'stop+game':'Стоп! Тут уже грають!','again':'Спробуй ще раз…','start-pl-2':'Почнімо!','confirmloss':'Підтвердьте програш!',
        'confirmtie':'Приймаєш нічию?','player':'Гравець ','giveup_done':' здався/здалась','dotie':'Нічия','giveup':'Здатися','cnl':'Відміна'
    },'ru':{
        'start':'Выбери сторону и начнём!','bot':'Бот','don’t touch':'Ой, да не тыкай сюда!','cnld':'Отменено','win':'О, ты победил!',
        'lose':'О, нет, ти проиграл…','tie':'Неужели ничья?','new':'Сыграем ещё раз?','stop':'Стопэ! Не твой ход!','oh':'Ляя…',
        'stop+game':'Стопэ! Здесь уже играют!','again':'Попробуйте ещё раз…','start-pl-2':'Начнём!','confirmloss':'Подтвердите проиграш!',
        'confirmtie':'Принимаешь ничью?','player':'Игрок ','giveup_done':' сдался/сдалась','dotie':'Ничья','giveup':'Сдаться','cnl':'Отмена'
    },'sr':{
        'start':'Изаберите страну и почните!','bot':'Бот','don’t touch':'Ох, да не идите овде!','cnld':'Промењено','win':'О, ти победио!',
        'lose':'О, не, изгубио си…','tie': 'Стварно жреб?','new':' Се поново играти??','stop':'Стани! Не твој потез!',' oh':'Бре…',
        'stop+game':'Стоп! Овде је већ играју!','again': 'Пробајте поново…','start-pl-2':'Почнемо!','confirmloss':'Потврди губитника!',
        'confirmtie':'Да ли прихватате жребање?','player':'Играч ','giveup_done':' одустаје','dotie':'жреб','giveup':'одустати','cnl':'Отказ'
    }}
f=lambda a: True if a!='❌' and a!='⭕️' else False
fo = lambda b,x,y,z,s: z if b[x]==b[y]==s and f(b[z]) else y if b[x]==b[z]==s and f(b[y]) else x if b[y]==b[z]==s and f(b[x]) else -1
resf=lambda n,s,q,c: [P(f'{n}{s}'+q.id,'t.me/lviv_lamptest/'+str(2019+6*n+s),'t.me/lviv_lamptest/'+str(675+n*2),reply_markup=c,input_message_content=C('❌ ? 👈\n⭕️ ?'))]
def board_text(board,size,b=''):
    for i in range(size):
        for j in range(size):
            b+=board[i*size+j]
        b+='\n'
    return b
def winxo(b,s,sz):
    assert sz>2
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
                if b[k]==b[k+sz+1]==b[k+(sz+1)*2]==b[k+(sz+1)*3]==s or\
                   b[k+3]==b[k+2+sz]==b[k+1+sz*2]==b[k+sz*3]==s:
                    return True
                for l in range(4):
                    u,v=k+l*sz,k+l
                    if b[u]==b[u+1]==b[u+2]==b[u+3]==s or\
                       b[v]==b[v+sz]==b[v+sz*2]==b[v+sz*3]==s:
                        return True
    else:
        for i in range(4):
            for j in range(4):
                k=i+j*sz
                if b[k]==b[k+9]==b[k+18]==b[k+27]==b[k+36]==s or\
                   b[k+4]==b[k+11]==b[k+18]==b[k+25]==b[k+32]==s:
                    return True
                for l in range(5):
                    u,v=k+l*8,k+l
                    if b[u]==b[u+1]==b[u+2]==b[u+3]==b[u+4]==s or\
                       b[v]==b[v+8]==b[v+16]==b[v+24]==b[v+32]==s:
                        return True
    return False
def end(g,text,w,l,cid):
    buttons=M()
    b_text=board_text(g.b,g.s)
    sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
    buttons.add(B('❌',switch_inline_query_current_chat='x'+str(g.s)),B(text='⭕️',switch_inline_query_current_chat='o'+str(g.s)))
    bot.edit_message_text(inline_message_id=cid,text=b_text+text,reply_markup=buttons)
    games.remove(g)
    bot.answer_callback_query(g.call[g.queue].id,text=w,show_alert=True)
    return bot.answer_callback_query(g.call[not g.queue].id,text=l,show_alert=True)
def game_xo(g,choice,pl1,t,cid):
    name0=g.playerX.first_name if g.playerX else '?'
    name1=g.playerO.first_name if g.playerO else '?'
    g.b[int(choice)]=['❌','⭕️'][not g.queue]
    win=winxo(g.b,g.b[int(choice)],g.s)
    if win:
        sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
        return end(g,f'\n❌ {name0} '+sign_0+f'\n⭕️ {name1} '+sign_1,t['win'],t['lose'],cid)
    elif not '⬜️' in g.b:
        return end(g,f'\n❌ {name0} 🤛🤜 {name1} ⭕️',t['tie'],t['tie'],cid)
    g.queue=not g.queue
    buttons=M()
    for i in range(g.s):
        buttons.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else g.b[i*g.s+j]) for j in range(g.s)])
    buttons.add(B(t['dotie'],callback_data='tie'),B(t['giveup'],callback_data='giveup'))
    return bot.edit_message_text(inline_message_id=cid,text=f'❌ {name0}'+' 👈'*g.queue+f'\n⭕️ {name1}'+' 👈'*(not g.queue),reply_markup=buttons)
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
    for g in games:
        if mktime(datetime.now().timetuple())-g.time>=600:
            bot.edit_message_text(inline_message_id=g.id,text='⌛️')
            games.remove(g)
    for g in text_games:
        if mktime(datetime.now().timetuple())-g.time>=600:
            bot.edit_message_text('⌛️',game_text.out.chat.id,g.out.message_id)
            text_games.remove(g)
class User:
    out=False
    def __init__(self,id,language='ua'):
        self.id=id
        self.t=languages[language]
class Game_text:
    isX=False; b=[]
    def __init__(self,out,time):
        self.out=out
        self.time=time
class Game:
    playerX=playerO=tie_id=giveup_user=None
    time=out=0; queue=True; b=[]; s=3; call=[0,0]
    def __init__(self,id):
        self.id=id
users=[User(id=0)]
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
@bot.message_handler(commands=['settings'])
def setting(m):
    buttons=M(row_width=2)
    buttons.add(B('Eng',callback_data='enS'),B('Ukr',callback_data='uaS'),B('Rus',callback_data='ruS'),B('Srp',callback_data='srS'),B('Cancel',callback_data='cnl'))
    out=bot.send_message(m.chat.id,'Choose language to play\nОбери мову, якою гратимеш\nВыбери язык, которым будеш играть',reply_markup=buttons)
    for user in users:
        if m.from_user.id==user.id:
            users.remove(user)
    u=User(id=m.from_user.id); u.out=out; users.append(u)
@bot.callback_query_handler(lambda c: search('[en|ua|ru|sr]S|cnl',c.data))
def settings(c):
    for u in users:
        if c.from_user.id==u.id:
            if c.data=='cnl':
                return bot.edit_message_text('Canceled           Відмінено\nОтменено           Отказ',c.message.chat.id,u.out.message_id)
            if not languages[c.data[:2]]==u.t:
                u.t=languages[c.data[:2]]
            bot.edit_message_text('✔️Done         ✔️Готово\n✔️Сделано         ✔️Готово',c.message.chat.id,u.out.message_id)
@bot.message_handler(commands=['x','o','start','new','game'])
def xotext(m):
    tx=False; t=m.text; buttons=M()
    for user in users:
        if m.chat.id==user.id: tx=user.t
    try: assert tx
    except: tx=users[0].t
    if search('start|new|game',t):
        return bot.send_message(m.chat.id,tx['start']+'\n             /x                        /o')
    for game in text_games:
        if m.chat.id==game.out.chat.id:
            bot.edit_message_text('♻️',m.chat.id,game.out.message_id)
            text_games.remove(game)
    name=m.from_user.first_name if m.from_user.first_name else 'None'
    now=mktime(datetime.now().timetuple())
    if 'x' in t:
        buttons.add(*[B('⬜️',callback_data=f'-{i}') for i in range(9)])
        out=bot.send_message(m.chat.id,f"❌ {name} 👈\n⭕️ {tx['bot']}",reply_markup=buttons)
        g=Game_text(out=out,time=now); g.isX=True; g.b=['⬜️']*9
        text_games.append(g)
    elif 'o' in t:
        buttons.add(*[B('⬜️',callback_data=f'-{i}') if i!=4 else B('❌',callback_data='-❌') for i in range(9)])
        out=bot.send_message(m.chat.id,f"❌ {tx['bot']} 👈\n⭕️ {name}",reply_markup=buttons)
        g=Game_text(out=out,time=now); g.isX=False; g.b=['⬜️' if i!=4 else '❌' for i in range(9)]
        text_games.append(g)
@bot.callback_query_handler(lambda c: search(r'-(\d|❌|⭕️)',c.data))
def xogame(c):
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
    if c.data=='-❌' or c.data=='-⭕️':
        return bot.answer_callback_query(c.id,text=t['don’t touch'])
    choice=int(c.data[1])
    if f(g.b[choice]):
        g.b[choice]=sign
    else:
        return bot.answer_callback_query(c.id,t['don’t touch'])
    my_choice=my_choice_func(g.b,my_sign,sign)
    if f(g.b[4]): my_choice=4
    if my_choice>-1:
        g.b[my_choice]=my_sign
    name0 = player if g.isX else t['bot']
    name1 = t['bot'] if g.isX else player
    win=False; b=g.b
    for s in ['❌','⭕️']:
        g.queue=False if s=='⭕️' else True
        if b[0]==b[4]==b[8]==s or b[2]==b[4]==b[6]==s:
            win=True
        for i in range(3):
            if b[i*3]==b[i*3+1]==b[i*3+2]==s or b[i]==b[3+i]==b[6+i]==s:
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
            text_games.remove(g)
            break
    if win:
        return 0
    elif not '⬜️' in g.b :
        b_text=''
        for i in range(3):
            b_text+=f'{g.b[3*i]}{g.b[3*i+1]}{g.b[3*i+2]}\n'
        bot.edit_message_text(b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
        bot.answer_callback_query(c.id,text=t['tie'])
        text_games.remove(g)
    else:
        buttons.add(*[B(g.b[i],callback_data=f'-{i}' if g.b[i]=='⬜️' else f'-{g.b[i]}') for i in range(9)])
        bot.edit_message_text(f'❌ {name0} 👈\n⭕️ {name1}',m.chat.id,g.out.message_id,reply_markup=buttons)
@bot.inline_handler(lambda q: True)
def inline(q):
    g=Game(id=q.id)
    g.time=mktime(datetime.now().timetuple())
    games.append(g)
    t=q.query.lower(); res=[]; gif=False
    cnl=M(); cnl.add(B('Cancel',callback_data='cancelstart'))
    if not t: t='3'
    if not any(n in t for n in '345678'):
        t='345678'
    for s in range(3,9):
        if str(s) in t:
            if not 'o' in t: res+=resf(1,s,q,cnl)
            if not 'x' in t: res+=resf(2,s,q,cnl)
    if not 'x' in t.lower() and not 'o' in t.lower():
        res=[*[x for x in res if not res.index(x)%2],*[x for x in res if res.index(x)%2]] # firstly go X-variants, secondly O-variants
    return bot.answer_inline_query(q.id,res)
@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen(cr):
    for game in games:
        if cr.result_id[2:] in game.id:
            game.id=cr.inline_message_id
            g=game
    try: assert g
    except:
        games.append(Game(id=cr.inline_message_id)); g=games[-1]
    if cr.result_id[0]=='1':
        g.playerX=cr.from_user
    elif cr.result_id[0]=='2':
        g.playerO=cr.from_user
    g.s=int(cr.result_id[1])
    if g.s==0: g.s=3
    g.b=['⬜️' for i in range(g.s**2)]
    g.time=mktime(datetime.now().timetuple())
    name0=g.playerX.first_name if g.playerX else '?'
    name1=g.playerO.first_name if g.playerO else '?'
    button=M()
    for i in range(g.s):
        button.row(*[B('⬜️',callback_data=f'{i*g.s+j:02}') for j in range(g.s)])
    g.out=bot.edit_message_text(inline_message_id=g.id,text=f'❌ {name0} 👈\n⭕️ {name1}',reply_markup=button)
@bot.callback_query_handler(lambda c: search(r'\d\d|❌|⭕️|cancel|tie|giveup|confirm',c.data) and c.data[0]!='-')
def xo(c):
    usid=c.from_user.id; t=g=False
    for game in games:
        if c.inline_message_id==game.id:
            g=game
    try: assert g
    except:
        return bot.edit_message_text(inline_message_id=c.inline_message_id,text='♻️')
    for user in users:
        if usid==user.id:
            t=user.t
    try: assert t
    except:
        t=users[0].t
    name0=g.playerX.first_name if g.playerX else '?'
    name1=g.playerO.first_name if g.playerO else '?'
    button=M()
    if c.data=='cancelend':
        g.tie_id=g.giveup_user=None
        for i in range(g.s):
            button.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else g.b[i*g.s+j]) for j in range(g.s)])
        return bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {name0}'+' 👈'*g.queue+f'\n⭕️ {name1}'+' 👈'*(not g.queue),reply_markup=button)
    elif c.data=='cancelstart':
        games.remove(g)
        return bot.edit_message_text(inline_message_id=g.id,text=t['cnld'])
    elif c.data=='tie':
        if all(g.call):
            if usid in [g.call[0].from_user.id,g.call[1].from_user.id]:
                g.tie_id=usid
                button.add(B(t['confirmtie'],callback_data='confirmtie'),B(t['cnl'],callback_data='cancelend'))
                return bot.edit_message_reply_markup(inline_message_id=c.inline_message_id,reply_markup=button)
        return bot.answer_callback_query(c.id,t['don’t touch'],show_alert=True)
    elif g.tie_id:
        if g.tie_id!=usid and g.playerX and g.playerO:
            return end(g,f'\n❌ {name0} 🤛🤜 {name1} ⭕️\n'+t['cnld'],t['tie'],t['tie'],c.inline_message_id)
        return bot.answer_callback_query(c.id,t['don’t touch'],show_alert=True)
    elif c.data=='giveup':
        if all(g.call):
            if usid in [g.call[0].from_user.id,g.call[1].from_user.id]:
                g.giveup_user=c.from_user
                button.add(B(t['confirmloss'],callback_data='confirmloss'),B(t['cnl'],callback_data='cancelend'))
                return bot.edit_message_reply_markup(inline_message_id=c.inline_message_id,reply_markup=button)
        return bot.answer_callback_query(c.id,t['don’t touch'],show_alert=True)
    elif g.giveup_user:
        if g.giveup_user.id==usid and g.playerO and g.playerX:
            sign_0,sign_1,lose,win = ['🏆','☠️',t['win'],t['lose']] if (g.playerX.id==usid)*g.queue else ['☠️','🏆',t['lose'],t['win']]
            return end(g,f'\n❌ {name0} '+sign_0+f'\n⭕️ {name1} '+sign_1+'\n'+t['player']+g.giveup_user.first_name+t['giveup_done'],win,lose,c.inline_message_id)
        return bot.answer_callback_query(c.id,t['don’t touch'],show_alert=True)
    elif c.data=='❌' or c.data=='⭕️':
        return bot.answer_callback_query(c.id,text=t['don’t touch'],show_alert=True)
    if g.playerX:
        if g.playerX.id==c.from_user.id:
            g.call[1]=c
            if g.queue:
                return game_xo(g,c.data,g.playerX,t,c.inline_message_id)
            return bot.answer_callback_query(c.id,text=t['stop'])
        elif not g.playerO:
            g.playerO=c.from_user
            bot.answer_callback_query(c.id,text=t['start-pl-2'])
        if g.playerO.id==c.from_user.id:
            g.call[0]=c
            if not g.queue:
                return game_xo(g,c.data,g.playerO,t,c.inline_message_id)
            return bot.answer_callback_query(c.id,text=t['stop'])
        return bot.answer_callback_query(c.id,text=t['stop+game'])
    elif g.playerO.id!=c.from_user.id:
        g.call[1]=c
        if g.queue:
            g.playerX=c.from_user
            bot.answer_callback_query(c.id,text=t['start-pl-2'])
            return game_xo(g,c.data,g.playerX,t,c.inline_message_id)
        return bot.answer_callback_query(c.id,text=t['stop'])
    return bot.answer_callback_query(c.id,text=t['don’t touch'])
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV})
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
