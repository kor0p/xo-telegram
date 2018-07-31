# -*- coding: utf-8 -*-
import telebot
from re import search
from config import *
from telebot.types import (
    InlineKeyboardMarkup as M,InputTextMessageContent as C,
    InlineQueryResultPhoto as P,InlineKeyboardButton as B
)
bot=telebot.TeleBot(token)
languages={
    'en':{
        'start':'Choose your side and get started!','bot':'Bot','don’t touch':'Oh, don’t touch this)',
        'win':'Oh, victory!','lose':'You loooose… Try harder!','tie':'It is really tie?','new':'Start a new game?'
    },
    'ua':{
        'start':'Обирай сторону і почнімо!','bot':'Бот','don’t touch':'Ой, не тикай сюди!',
        'win':'О, ти переміг!','lose':'О, ні, ти програв…','tie':'Невже нічия?','new':'Зіграємо ще раз?'
    },
    'ru':{
        'start':'Выбери сторону и начнём!','bot':'Бот','don’t touch':'Ой, не тыкай сюда!',
        'win':'О, ты победил!','lose':'О, нет, ти проиграл…','tie':'Неужели ничья?','new':'Сыграем ещё раз?'
    }
}
f=lambda a: True if a!='❌' and a!='⭕️' else False
def fo(b,x,y,z,s):
    if b[x]==b[y]==s and f(b[z]):
        return z
    elif b[x]==b[z]==s and f(b[y]):
        return y
    elif b[y]==b[z]==s and f(b[x]):
        return x
    return -1
class User:
    def __init__(self,id,language='en',out=False):
        self.id=id
        self.t=languages[language]
        self.out=out
class Game_text:
    def __init__(self,out,id,isX=False,board=[],start=None,turn=-1):
        self.out=out
        self.id=id
        self.isX=isX
        self.b=board
        self.start=start
        self.turn=turn
class Game:
    call=[0,0]
    p1=p2=False
    def __init__(self,id,playerX=None,playerO=None,queue=None,b=[],size=3):
        self.id=id
        self.playerX=playerX
        self.playerO=playerO
        self.queue=queue
        self.b=b
        self.s=size
users=[User(id=0)]
games=[]
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
        if m.chat.id==user.id:
            del users[users.index(user)]
    users.append(User(id=m.chat.id,out=out))
@bot.callback_query_handler(lambda c: search('en|ua|ru|cnl',c.data))
def settings(c):
    id_=c.message.chat.id
    d=c.data
    for user in users:
        if id_==user.id:
            if d=='cnl':
                bot.edit_message_text('Canceled\nВідмінено\nОтменено',id_,u.out.message_id)
            else:
                u=user
                u.t=languages[d]
                bot.edit_message_text('✔️Done\n✔️Готово\n✔️Сделано',id_,u.out.message_id)
@bot.message_handler(commands=['start','new','game','x','o'])
def xotext(m):
    global games
    tx=False
    for user in users:
        if m.chat.id==user.id:
            tx=user.t
    if not tx:
        tx=users[0].t
    t=m.text
    if t.startswith('/start') or t.startswith('/new') or t.startswith('/game'):
        bot.send_message(m.chat.id,tx['start']+'\n             /x                        /o')
    else:
        buttons=M()
        name=m.from_user.first_name if m.from_user.first_name else 'None'
        if 'x' in t:
            buttons.add(*[B('⬜️',callback_data=f'-{i}') for i in range(9)])
            out=bot.send_message(m.chat.id,f"❌ {name} 👈\n⭕️ {tx['bot']}",reply_markup=buttons)
            games.append(Game_text(id=m.chat.id,out=out,isX=True,start=False,turn=1,board=['⬜️']*9))
        elif 'o' in t:
            buttons.add(*[B('⬜️',callback_data=f'-{i}') if i!=4 else B('❌',callback_data='-❌') for i in range(9)])
            out=bot.send_message(m.chat.id,f"❌ {tx['bot']} 👈\n⭕️ {name}",reply_markup=buttons)
            games.append(Game_text(id=m.chat.id,out=out,isX=False,start=True))
@bot.inline_handler(lambda q: len(q.query)>0)
def inline(q):
    global games
    name=q.from_user.first_name
    buttons=M()
    g=Game(id=q.id)
    games.append(g)
    t=q.query
    if search(r'\d',t):
        size=int(search(r'\d',t).group())
        g.s=size
        for i in range(g.s):
            buttons.row(*[B('⬜️',callback_data=f'{i*g.s+j:02}') for j in range(g.s)])
    else:
        buttons.add(*[B('⬜️',callback_data=f'{i:02}') for i in range(9)])
    r1=P('1'+q.id,'t.me/keklulkeklul/677','t.me/keklulkeklul/677',reply_markup=buttons,input_message_content=C(f'❌ {name} 👈\n⭕️ ?'))
    r2=P('2'+q.id,'t.me/keklulkeklul/679','t.me/keklulkeklul/679',reply_markup=buttons,input_message_content=C(f'❌ ? 👈\n⭕️ {name}'))
    if 'x' in t.lower():
        g.playerX=q.from_user
        bot.answer_inline_query(q.id,[r1])
    elif 'o' in t.lower():
        g.playerO=q.from_user
        bot.answer_inline_query(q.id,[r2])
    else:
        bot.answer_inline_query(q.id,[r1,r2])
@bot.chosen_inline_handler(func=lambda cr: True)
def chosen(cr):
    global games
    for game in games:
        if cr.result_id[1:]==game.id:
            game.id=cr.inline_message_id
            g=game
    try: assert g
    except:
        games.append(Game(id=cr.inline_message_id)); g=games[-1]
    result_id=cr.result_id[0]
    if result_id=='1':
        g.playerX=cr.from_user
        g.playerO=None
        g.p1=True
    elif result_id=='2':
        g.playerX=None
        g.playerO=cr.from_user
        g.p1=True
    g.b=['⬜️' for i in range(g.s**2)]
    g.queue=True
    #except: bot.edit_message_text(inline_message_id=cr.inline_message_id,text='Ой ляя… давай щэ раз')
@bot.callback_query_handler(lambda c: search(r'-(\d|x|o)',c.data))
def xogame(c):
    global games
    m=c.message
    for user in users:
        if m.chat.id==user.id:
            t=user.t
    try: assert t
    except:
        t=users[0].t
    for game in games:
        if m.chat.id==game.id:
            g=game
    try: assert g
    except:
        games.append(Game(id=c.inline_message_id)); g=games[-1]
    buttons=M()
    sign,my_sign=['❌','⭕️'] if g.isX else ['⭕️','❌']
    if g.start:
        g.b=['⬜️' if i!=4 else '❌' for i in range(9)]
        g.start=False
        g.turn=2
    try:
        if search('\d',c.data[1]):
            choice=int(c.data[1])
        else:
            bot.answer_callback_query(c.id,t['don’t touch'])
        if f(g.b[choice]):
            g.b[choice]=sign
    except:
        bot.answer_callback_query(c.id,t['don’t touch'])
        return 0
    if '⬜️' in g.b:
        if f(g.b[4]):
            my_choice=4
        else:
            for s in [my_sign,sign]:
                for i in range(3):
                    for x,y,z in [[3*i,3*i+1,3*i+2],[i,i+3,i+6]]:
                        my_choice=fo(g.b,x,y,z,s)
                        if my_choice>-1: break
                    if my_choice>-1: break
                if my_choice>-1: break
            if my_choice<0:
                for s in [my_sign,sign]:
                    for x,y,z in [[0,4,8],[2,4,6]]:
                        my_choice=fo(g.b,x,y,z,s)
                        if my_choice>-1: break
                    if my_choice>-1: break
                if my_choice<0:
                    if g.b[4]==my_sign:
                        for i,j,r in [
                            [1,3,0],[1,5,2],[3,7,6],[5,7,8],[2,3,1],[0,5,1],
                            [3,8,7],[5,6,7],[1,6,3],[1,8,5],[0,7,3],[2,7,5]
                            ]:
                                if g.b[i]==g.b[j]==sign and f(g.b[r]):
                                    my_choice=r
                                    break
                        for k in [0,8]:
                            for l in [6,2]:
                                for i,j in [[k,l],[l,k]]:
                                    if g.b[i]==sign and f(g.b[j]):
                                        my_choice=j; break
                                if my_choice>-1: break
                            if my_choice>-1: break
                        if my_choice<0:
                            my_choice=choice
                            while not f(g.b[my_choice]):
                                my_choice=(my_choice+1)%9
                    else :
                        for i in [0,2,6,8]:
                            if f(g.b[i]):
                                my_choice=i
                        if my_choice<0:
                            my_choice=choice
                            while not f(g.b[my_choice]):
                                my_choice=(my_choice+1)%9
    else:
        my_choice=-1
    if f(g.b[4]):
        my_choice=4
    g.turn+=1
    if my_choice>-1:
        g.b[my_choice]=my_sign
    player = c.from_user.first_name if c.from_user.first_name else 'None'
    name0=player if g.isX else t['bot']
    name1=t['bot'] if g.isX else player
    g.win=False
    for s in ['❌','⭕️']:
        g.queue=False if s=='⭕️' else True
        if g.b[0]==g.b[4]==g.b[8]==s or g.b[2]==g.b[4]==g.b[6]==s:
            g.win=True
        for i in range(3):
            if g.b[i*3]==g.b[i*3+1]==g.b[i*3+2]==s or g.b[i]==g.b[3+i]==g.b[6+i]==s:
                g.win=True
        if g.win:
            b_text=''
            for i in range(3):
                b_text+=f'{g.b[3*i]} {g.b[3*i+1]} {g.b[3*i+2]}\n'
            sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
            bot.edit_message_text(b_text+f'\n❌ {name0} {sign_0}\n⭕️ {name1} {sign_1}\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
            if s==sign:
                bot.answer_callback_query(c.id,text=t['win'])
            elif s==my_sign:
                bot.answer_callback_query(c.id,text=t['lose'])
            del games[games.index(g)]
            break
    if g.win:
        return 0
    elif not '⬜️' in g.b :
        b_text=''
        for i in range(3):
            b_text+=f'{g.b[3*i]} {g.b[3*i+1]} {g.b[3*i+2]}\n'
        bot.edit_message_text(b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
        bot.answer_callback_query(c.id,text=t['tie'])
        del games[games.index(g)]
    else:
        buttons.add(*[B(g.b[i],callback_data=f'-{i}' if g.b[i]=='⬜️' else f'-{g.b[i]}') for i in range(9)])
        bot.edit_message_text(f'❌ {name0} 👈\n⭕️ {name1}',m.chat.id,g.out.message_id,reply_markup=buttons)
@bot.callback_query_handler(lambda c: search(r'\d\d|❌|⭕️',c.data) and c.data[0]!='-')
def xo(c):
    global games
    for game in games:
        if c.inline_message_id==game.id:
            g=game
    if g.p1 and g.p2:
        if g.playerX.id==c.from_user.id:
            g.call[1]=c
            if g.queue:
                game_xo(g,c,g.playerX)
            else:
                bot.answer_callback_query(c.id,text='Стопэ')
        elif g.playerO.id==c.from_user.id:
            g.call[0]=c
            if not g.queue:
                game_xo(g,c,g.playerO)
            else:
                bot.answer_callback_query(c.id,text='Стопэ')
        else:
            bot.answer_callback_query(c.id,text='Стопэ, тут вже граютб')
    else:
        try:
            if g.playerO and c.from_user.id!=g.playerO.id:
                g.playerX=c.from_user
                g.p2=True
                bot.answer_callback_query(c.id,text='Почнімо!')
            elif g.playerX and c.from_user.id!=g.playerX.id:
                g.playerO=c.from_user
                g.p2=True
                bot.answer_callback_query(c.id,text='Почнімо!')
            else:
                bot.answer_callback_query(c.id,text='Зачекай товариша!')
            if g.p2:
                buttons=M()
                if 9>g.s>2:
                    for i in range(g.s):
                        buttons.row(*[B('⬜️',callback_data=f'{i*g.s+j:02}') for j in range(g.s)])
                    bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {g.playerX.first_name} 👈\n⭕️ {g.playerO.first_name}',reply_markup=buttons)
                else:
                    bot.answer_callback_query(c.id,text='От халепа!')
                    bot.edit_message_text(inline_message_id=c.inline_message_id,text='Я не можу робити ігри таких розмірів!')
        except:
            bot.answer_callback_query(c.id,text='Ляяя…')
            bot.edit_message_text(inline_message_id=c.inline_message_id,text='Ой ляя… давай щэ раз')

def game_xo(g,c,pl1):
    name0=g.playerX.first_name
    name1=g.playerO.first_name
    if f(c.data):
        s=['❌','⭕️'][not g.queue]
        g.b[int(c.data)]=s
        g.win=False
        if g.s==3:
            if g.b[0]==g.b[4]==g.b[8]==s or g.b[2]==g.b[4]==g.b[6]==s:
                g.win=True
            for i in range(3):
                if g.b[i*3]==g.b[i*3+1]==g.b[i*3+2]==s or g.b[i]==g.b[3+i]==g.b[6+i]==s:
                    g.win=True
        else:
            for i in range(g.s-3):
                for j in range(g.s-3):
                    k=i+j*g.s
                    if g.b[k]==g.b[k+g.s+1]==g.b[k+(g.s+1)*2]==g.b[k+(g.s+1)*3]==s or g.b[k+3]==g.b[k+3+(g.s-1)]==g.b[k+3+(g.s-1)*2]==g.b[k+3+(g.s-1)*3]==s:
                        g.win=True; break
                if g.win: break
            for i in range(g.s-3):
                for j in range(g.s-3):
                    for l in range(4):
                        k=i+j*g.s
                        if g.b[k+l*g.s]==g.b[k+l*g.s+1]==g.b[k+l*g.s+2]==g.b[k+l*g.s+3]==s or g.b[k+l]==g.b[k+l+g.s]==g.b[k+l+g.s*2]==g.b[k+l+g.s*3]==s:
                            g.win=True; break
                    if g.win: break
                if g.win: break
        buttons=M()
        if g.win:
            g.b_text=''
            for i in range(g.s):
                for j in range(g.s):
                    g.b_text+=g.b[i*g.s+j]+' '
                g.b_text+='\n'
            sign_0,sign_1 = ['🏆','☠️'] if g.queue else ['☠️','🏆']
            buttons.add(B('❌',switch_inline_query_current_chat='x'+str(g.s)),B(text='⭕️',switch_inline_query_current_chat='o'+str(g.s)))
            bot.edit_message_text(inline_message_id=c.inline_message_id,text=g.b_text+f'\n❌ {name0} '+sign_0+f'\n⭕️ {name1} '+sign_1,reply_markup=buttons)
            bot.answer_callback_query(g.call[g.queue].id,text='Ти виграв, файно!')
            bot.answer_callback_query(g.call[not g.queue].id,text='Ти програв, не файно…')
            del games[games.index(g)]
        elif not '⬜️' in g.b:
            g.b_text=''
            for i in range(g.s):
                for j in range(g.s):
                    g.b_text+=g.b[i*g.s+j]+' '
                g.b_text+='\n'
            buttons.add(B('❌',switch_inline_query_current_chat='x'+str(g.s)),B(text='⭕️',switch_inline_query_current_chat='o'+str(g.s)))
            bot.edit_message_text(inline_message_id=c.inline_message_id,text=g.b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️',reply_markup=buttons)
            bot.answer_callback_query(g.call[0].id,text='Невже нічия?')
            bot.answer_callback_query(g.call[1].id,text='Невже нічия?')
            del games[games.index(g)]
        else:
            g.queue=not g.queue
            for i in range(g.s):
                buttons.row(*[B(g.b[i*g.s+j],callback_data=f'{i*g.s+j:02}' if g.b[i*g.s+j]=='⬜️' else f'{g.b[i*g.s+j]}') for j in range(g.s)])
            bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {name0}'+' 👈'*g.queue+f'\n⭕️ {name1}'+' 👈'*(not g.queue),reply_markup=buttons)

if __name__ == '__main__':
    bot.polling(none_stop=True)
