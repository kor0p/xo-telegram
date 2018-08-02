# -*- coding: utf-8 -*-
import telebot,config
from re import search
from telebot.types import InlineKeyboardMarkup as M,InputTextMessageContent as C,InlineQueryResultPhoto as P,InlineQueryResultGif as G,InlineKeyboardButton as B
bot=telebot.TeleBot(config.token)
languages={
    'en':{
        'start':'Choose your side and get started!','bot':'Bot','don’t touch':'Oh, don’t touch this)',
        'win':'Oh, victory!','lose':'You loooose… Try harder!','tie':'It is really tie?','new':'Start a new game?',
        'stop':'Stop! Wait your turn','stop+game':'Stop! There already playing','oh':'Oh shit!','again':'Oh, try again…',
        'wait':'Wait your opponent to start!','start-pl-2':'Let’s go!','size':'Sorry, I can do board this size'
    },
    'ua':{
        'start':'Обирай сторону і почнімо!','bot':'Бот','don’t touch':'Ой, да не тикай сюди!',
        'win':'О, ти переміг!','lose':'О, ні, ти програв…','tie':'Невже нічия?','new':'Зіграємо ще раз?',
        'stop':'Стоп! Не твій хід!','stop+game':'Стоп! Тут уже грають!','oh':'Бляха…','again':'Спробуй ще раз…',
        'wait':'Зачекай-но товариша!','start-pl-2':'Почнімо!','size':'Я не можу робити гру таких розмірів!'
    },
    'ru':{
        'start':'Выбери сторону и начнём!','bot':'Бот','don’t touch':'Ой, да не тыкай сюда!',
        'win':'О, ты победил!','lose':'О, нет, ти проиграл…','tie':'Неужели ничья?','new':'Сыграем ещё раз?',
        'stop':'Стопэ!','stop+game':'Стопэ! Здесь уже играют!','oh':'Ляя…','again':'Попробуйте ещё раз…',
        'wait':'Подожди противника!','start-pl-2':'Начнём!','size':'Я не могу делать игры таких размеров!'
    }
}
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
    name0=g.playerX.first_name
    name1=g.playerO.first_name
    if not f(c.data):
        return 1
    g.b[int(c.data)]=['❌','⭕️'][not g.queue]
    win=winxo(g.b,g.b[int(c.data)],g.s)
    buttons=M()
    if win:
        g.b_text=''
        for i in range(g.s):
            for j in range(g.s):
                g.b_text+=g.b[i*g.s+j]+' '
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
                g.b_text+=g.b[i*g.s+j]+' '
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
    if f(b[4]):
        return 4
    for s in [msgn,sgn]:
        for i in range(3):
            for x,y,z in [[3*i,3*i+1,3*i+2],[i,i+3,i+6]]:
                res=fo(b,x,y,z,s)
                if res>-1: return res
        for x,y,z in [[0,4,8],[2,4,6]]:
            res=fo(b,x,y,z,s)
            if res>-1: return res
    for i,j,r in [(1,3,0),(1,5,2),(3,7,6),(5,7,8),(2,3,1),(0,5,1),(3,8,7),(5,6,7),(1,6,3),(1,8,5),(0,7,3),(2,7,5)]:
            if b[i]==b[j]==sgn and f(b[r]):
                return r
    for i in [0,2,6,8]:
        if f(b[i]):
            return i
    my_c=choice
    while not f(b[my_c]):
        my_c=(my_c+1)%9
    return my_c
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
users=[User(id=0)]; games=[]; text_games=[]
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
                bot.edit_message_text('Canceled\nВідмінено\nОтменено',c.mesage.chat.id,u.out.message_id)
            else:
                if not languages[c.data]==u.t:
                    u.t=languages[c.data]
                bot.edit_message_text('✔️Done\n✔️Готово\n✔️Сделано',c.message.chat.id,u.out.message_id)
@bot.message_handler(commands=['start','new','game','x','o'])
def xotext(m):
    global text_games
    tx=False
    for user in users:
        if m.chat.id==user.id:
            tx=user.t
    try: assert tx
    except:
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
            text_games.append(Game_text(id=m.chat.id,out=out,isX=True,start=False,turn=1,board=['⬜️']*9))
        elif 'o' in t:
            buttons.add(*[B('⬜️',callback_data=f'-{i}') if i!=4 else B('❌',callback_data='-❌') for i in range(9)])
            out=bot.send_message(m.chat.id,f"❌ {tx['bot']} 👈\n⭕️ {name}",reply_markup=buttons)
            text_games.append(Game_text(id=m.chat.id,out=out,isX=False,start=True))
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
        if m.chat.id==game.id:
            g=game
    try: assert g
    except:
        bot.delete_message(m.chat.id,m.message_id)
        return bot.answer_callback_query(c.id,text=t['don’t touch'])
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
    my_choice=my_choice_func(g.b,my_sign,sign)
    if f(g.b[4]):
        my_choice=4
    g.turn+=1
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
                b_text+=f'{g.b[3*i]} {g.b[3*i+1]} {g.b[3*i+2]}\n'
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
            b_text+=f'{g.b[3*i]} {g.b[3*i+1]} {g.b[3*i+2]}\n'
        bot.edit_message_text(b_text+f'\n❌ {name0} 🤛🤜 {name1} ⭕️\n'+t['new']+'\n      /x            /o',m.chat.id,g.out.message_id)
        bot.answer_callback_query(c.id,text=t['tie'])
        del text_games[text_games.index(g)]
    else:
        buttons.add(*[B(g.b[i],callback_data=f'-{i}' if g.b[i]=='⬜️' else f'-{g.b[i]}') for i in range(9)])
        bot.edit_message_text(f'❌ {name0} 👈\n⭕️ {name1}',m.chat.id,g.out.message_id,reply_markup=buttons)
@bot.inline_handler(lambda q: True)
def inline(q):
    global games
    name=q.from_user.first_name
    g=Game(id=q.id)
    games.append(g)
    t=q.query; a=b=0
    x=[]; o=[]; results=[]
    button3=M()
    button3.add(*[B('⬜️',callback_data=f'{i:02}') for i in range(9)])
    if not q.query:
        bot.answer_inline_query(q.id,[P('13'+q.id,'t.me/keklulkeklul/677','t.me/keklulkeklul/677',reply_markup=button3,input_message_content=C(f'❌ {name} 👈\n⭕️ ?')),P('23'+q.id,'t.me/keklulkeklul/679','t.me/keklulkeklul/679',reply_markup=button3,input_message_content=C(f'❌ ? 👈\n⭕️ {name}'))])
        return 1
    for s in range(3,9):
        button=M()
        for i in range(s):
            button.row(*[B('⬜️',callback_data=f'{i*s+j:02}') for j in range(s)])
        xs=P('1'+str(s)+q.id,f't.me/keklulkeklul/{2025+s}','t.me/keklulkeklul/677',reply_markup=button,input_message_content=C(f'❌ {name} 👈\n⭕️ ?'))
        os=P('2'+str(s)+q.id,f't.me/keklulkeklul/{2031+s}','t.me/keklulkeklul/679',reply_markup=button,input_message_content=C(f'❌ ? 👈\n⭕️ {name}'))
        if str(s) in t:
            if 'x' in t.lower():
                g.playerX=q.from_user
                results+=[xs]
            elif 'o' in t.lower():
                g.playerO=q.from_user
                results+=[xo]
            else:
                results+=[xs,os]
    if results:
        return bot.answer_inline_query(q.id,results)
    if not 'o' in t.lower():
        g.playerX=q.from_user
        results+=[G('10'+q.id,'t.me/keklulkeklul/2066','t.me/keklulkeklul/2066',reply_markup=button3,input_message_content=C(f'❌ {name} 👈\n⭕️ ?'))]
    if not 'x' in t.lower():
        g.playerO=q.from_user
        results+=[G('20'+q.id,'t.me/keklulkeklul/2067','t.me/keklulkeklul/2067',reply_markup=button3,input_message_content=C(f'❌ ? 👈\n⭕️ {name}'))]
    bot.answer_inline_query(q.id,results)
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
    g.p1=True
    g.s=int(cr.result_id[1])
    if not g.s: g.s=3
    g.b=['⬜️' for i in range(g.s**2)]
    g.queue=True
@bot.callback_query_handler(lambda c: search(r'\d\d|❌|⭕️',c.data) and c.data[0]!='-')
def xo(c):
    global games,users
    for game in games:
        if c.inline_message_id==game.id:
            g=game
    try: assert g
    except:
        games.append(Game(id=c.inline_message_id)); g=games[-1]
    for user in users:
        if c.from_user.id==user.id:
            t=user.t
    try: assert t
    except:
        t=users[0].t
    if g.p1 and g.p2:
        if g.playerX.id==c.from_user.id:
            g.call[1]=c
            if g.queue:
                game_xo(g,c,g.playerX,t)
            else:
                bot.answer_callback_query(c.id,text=t['stop'])
        elif g.playerO.id==c.from_user.id:
            g.call[0]=c
            if not g.queue:
                game_xo(g,c,g.playerO,t)
            else:
                bot.answer_callback_query(c.id,text=t['stop'])
        else:
            bot.answer_callback_query(c.id,text=t['stop+game'])
    else:
        try:
            if g.playerO and c.from_user.id!=g.playerO.id:
                g.playerX=c.from_user
                g.p2=True
                bot.answer_callback_query(c.id,text=t['start-pl-2'])
            elif g.playerX and c.from_user.id!=g.playerX.id:
                g.playerO=c.from_user
                g.p2=True
                bot.answer_callback_query(c.id,text=t['start-pl-2'])
            else:
                bot.answer_callback_query(c.id,text=t['wait'])
            if g.p2:
                buttons=M()
                if 9>g.s>2:
                    for i in range(g.s):
                        buttons.row(*[B('⬜️',callback_data=f'{i*g.s+j:02}') for j in range(g.s)])
                    bot.edit_message_text(inline_message_id=c.inline_message_id,text=f'❌ {g.playerX.first_name} 👈\n⭕️ {g.playerO.first_name}',reply_markup=buttons)
                else:
                    bot.answer_callback_query(c.id,text=t['oh'])
                    bot.edit_message_text(inline_message_id=c.inline_message_id,text=t['size'])
        except:
            bot.answer_callback_query(c.id,text=t['oh'])
            bot.edit_message_text(inline_message_id=c.inline_message_id,text=t['again'])

if __name__ == '__main__':
    bot.polling(none_stop=True)
