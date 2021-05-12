import tkinter as tk
from tkinter import ttk,font,messagebox,colorchooser
from functools import partial
#import winsound
#winsound.Beep(500,1000)
#winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS)
#winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS)
#winsound.PlaySound('SystemExit', winsound.SND_ALIAS)
#winsound.PlaySound('SystemHand', winsound.SND_ALIAS)
#winsound.PlaySound('SystemQuestion', winsound.SND_ALIAS)


try:
    from PIL import Image,ImageTk
except:
    print("Could not load Images")
    
#from PIL import Image,ImageTk
from tkinter import filedialog
import objects,board
import os,shutil,json
import random

ITEMS_DICT=objects.ITEMS_DICT

MONSTERS_DICT=objects.MONSTERS_DICT

CHAR_DICT={
        's':u'\u0000',#0  space
        '#':u'\u25a0',#1  wall
        'd':u'\u25D8',#2  door
        'm':u'\u203C',#3  monster
        'g':u'\u00a9',#4  gold
        'c':u'\u2302',#5  chest
        '?':u'\u0000',#6  trap
        '.':u'\uA71C',#7  entrance
        '!':u'\uA71B',#8  exit
        '*':u'\u2665',#9  player
        '$':u'\u263A',#10 shop
        '|':u'\u25a0',#11 False wall
        }

## Testing Purposes only
p=objects.Player('J',_maxhp=100,_maxmana=100)
#s=objects.Shop(p,["Small HP Potion","Medium HP Potion","Small MP Potion"])
m=objects.Character('test mob',10,6,3,10,10,0.5)
com=board.BoardEvent(player=p,type=type,monster=m)
with open ('test.json','r') as file:
    floor = json.load(file)
bo = board.Board(floor['floor'],p,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],1,"fugs")    
#bo.show_floor_fancy()
test=True
class tester(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.master=master
        #self.master.geometry('+2000+0')#'1050x525')
        self.pack(fill=tk.BOTH,expand=True)
        self.player_obj=p
        self.gamefont = font.Font(family='Consolas',size=12) 
        self.current_floor=bo
        self.gameboard = Visual_Board(self,color='#111111')
        self.charinfo = CharInfo(self)
        self.gameboard.pack(side=tk.LEFT)
        
        for i in ITEMS_DICT.values():
            self.player_obj.get_item(i)
        
        
        self.charinfo.on_update()
        self.charinfo.pack(side=tk.RIGHT)
        self.key_bind_set()
        
        #self.com = Combat_Window(self,com,'w')
        #self.com.pack()
        
    def key_bind_unset(self):
        self.master.unbind('w')
        self.master.unbind('a')
        self.master.unbind('s')
        self.master.unbind('d')
        self.master.unbind('<Left>')
        self.master.unbind('<Right>')
        self.master.unbind('<Up>')
        self.master.unbind('<Down>')
    def key_bind_set(self):
        self.master.bind('w',lambda e: self.gameboard.button_handle('w'))
        self.master.bind('a',lambda e: self.gameboard.button_handle('a'))
        self.master.bind('s',lambda e: self.gameboard.button_handle('s'))
        self.master.bind('d',lambda e: self.gameboard.button_handle('d'))
        self.master.bind('<Left>', lambda e: self.gameboard.button_handle('a'))
        self.master.bind('<Right>', lambda e: self.gameboard.button_handle('d'))
        self.master.bind('<Up>', lambda e: self.gameboard.button_handle('w'))
        self.master.bind('<Down>', lambda e: self.gameboard.button_handle('s'))


## Custom UI Objects
class HorizontalMeterBar(tk.Frame):#(parent,title,[width,height,labelpos,clickable)
    
    def __init__(self,master,current,max,type,cwidth=100,cheight=50,labelpos='in',font=None,**args):
        tk.Frame.__init__(self,master,**args)
        self.cwidth=cwidth
        self.cheight=cheight
        self.boxarr=[]
        self.max=max
        self.current=current
        self.type=type
        self.canvas= tk.Canvas(self,width=self.cwidth,height=self.cheight)
        
        self.canvas.grid(row=0,column=0)
        self.label_id = self.canvas.create_text(self.cwidth/2,(self.cheight/2)+2,text='{0}/{1}'.format(self.current,self.max),justify='center')
    
        self.draw_meter_bar()
        
    def draw_meter_bar(self):
        startx=0
        endx=1
        for x in range(self.cwidth):
            self.boxarr.append(self.canvas.create_rectangle(startx,5,endx,self.cheight,fill=self.get_color(self.current),width=0))
            startx+=1
            endx+=1
        self.canvas.create_rectangle(2,5,self.cwidth,self.cheight)   
        self.canvas.tag_raise(self.label_id)  
        self.set_value(self.current)
    
    def set_value(self,current):
        self.current=current
        percent = (current/self.max)*100
        self.canvas.itemconfig(self.label_id,text=f'{current}/{self.max}',fill='black')
        if percent<=100.00:
            progress=(percent/100)*self.cwidth
            for x in self.boxarr:
                self.canvas.itemconfig(x,fill='white')
            for x in range(int(progress)):
                self.canvas.itemconfig(x+2,fill=self.get_color(percent))
       
    def get_color(self,percent):
        if self.type=='hp':
            if percent <35:
                return 'red'
            elif percent >=35.00 and percent <70:
                return 'orange'
            elif percent >=70:
                return 'green'
        elif self.type=='mp':
            return 'lightblue'
        elif self.type=='exp':
            return "yellow"

class HoverButton(tk.Button):#(activebackground='',activeforeground='')
    def __init__(self,master,**kw):
        tk.Button.__init__(self,master=master,**kw)
        self.defaultBackground= self['background']
        self.defaultForeground= self['foreground']
        self.bind('<Enter>',self.on_enter)
        self.bind('<Leave>',self.on_leave)        
    def on_enter(self,event):
        self['background'] = self['activebackground']
        self['foreground'] = self['activeforeground']
    def on_leave(self,event):
        self['background'] = self.defaultBackground
        self['foreground'] = self.defaultForeground

class SortSearchTreeview(ttk.Treeview):#(heading(sort_by='name|num'))
    def __init__(self,master=None,*args,**kwargs):
        ttk.Treeview.__init__(self,master=master,*args,**kwargs)
        self._toSearch = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self._toSearch)
        self.bind("<KeyPress>", self._keyOnTree)
        self._toSearch.trace_variable("w", self._search)
        self.entry.bind("<Return>", self._hideEntry)
        self.entry.bind("<Escape>", self._hideEntry)
        
    def heading(self,column,sort_by=None,**kwargs):
        if sort_by and not hasattr(kwargs,'command'):
            func = getattr(self,f'_sort_by_{sort_by}',None)
            if func:
                kwargs['command']= partial(func,column,False)
        return super().heading(column,**kwargs)
    
    def _sort(self,column,reverse,data_type,callback):
        try:
            l = [(self.set(k, column), k) for k in self.get_children('')]
            l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
            for index, (_, k) in enumerate(l):
                self.move(k, '', index)
            self.heading(column, command=partial(callback, column, not reverse))
        except Exception as e:
            print(e)
            messagebox.showwarning("","Cannot Sort by name,\nUse search instead")
            
    def _sort_by_num(self, column, reverse):
        self._sort(column, reverse, int, self._sort_by_num)
    def _sort_by_name(self, column, reverse):
        self._sort(column, reverse, str, self._sort_by_name)        
            
    def _keyOnTree(self, event):
        self.entry.place(relx=1, anchor=tk.NE)
        if event.char.isalpha():
          self.entry.insert(tk.END, event.char)
        self.entry.focus_set()

    def _hideEntry(self, event):
        self.entry.delete(0, tk.END)
        self.entry.place_forget()
        self.focus_set()

    def _search(self, *args):
        pattern = self._toSearch.get()
        #avoid search on empty string
        if len(pattern) > 0:
            self.search(pattern)

    def search(self, pattern, item=''):
        children = self.get_children(item)
        for child in children:
            text = self.item(child, 'text')
            if text.lower().startswith(pattern.lower()):
                self.selection_set(child)
                self.see(child)
                return True
            else:
                res = self.search(pattern, child)
                if res:
                    return True	


##
class Base_Window(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.master=master
        self.master.geometry('525x525')#half is 525,270
        screen_width=self.master.winfo_screenwidth()
        screen_height=self.master.winfo_screenheight()
        x_offset = int((screen_width/2) - (525/2))
        y_offset = int((screen_height/2) - (525/2))
        self.master.geometry(f'+{x_offset}+{y_offset}')
        self.gamefont = font.Font(family='Consolas',size=12) 
        self.pack(fill=tk.BOTH,expand=1)
        self.player_obj=None
        self.current_floor=None
        self.floors_arr={}
        self.cc = Character_Creation(self)
        self.cc.pack()
             
    def finish_character_create(self):
        self.master.geometry('1135x555')
        self.istutorial = True if self.cc.tutorial_enabled.get()==1 else False
        self.cc.pack_forget()
        self.cc=None
        screen_width=self.master.winfo_screenwidth()
        screen_height=self.master.winfo_screenheight()
        x_offset = int((screen_width/2) - (1135/2))
        y_offset = int((screen_height/2) - (555/2))
        self.master.geometry(f'+{x_offset}+{y_offset}')
        self.player_obj.get_starter_gear()
        self.generate_next_level()
        self.fill_screen()
        
    def fill_screen(self):
        self.charinfo = CharInfo(self)
        if test==True:
            self.gameboard=Visual_Board(self,color='#111111')
        else:
            self.gameboard=Visual_Board(self)
        self.charinfo.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.gameboard.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.key_bind_set()
        if test==True:
            self.player_obj.get_item(ITEMS_DICT['Light Heal'])
            self.player_obj.get_item(ITEMS_DICT['Light Fire'])
            self.player_obj.get_item(ITEMS_DICT['Light Fire'])
            self.player_obj.get_item(ITEMS_DICT['Copper Axe'])
            self.player_obj.get_item(ITEMS_DICT['Steel Sword'])
            self.charinfo.on_update()
    
    def generate_next_level(self):
        if self.current_floor:
            if self.current_floor.floor_index+1==100:
                pass
            if (self.current_floor.floor_index+1)%10==5:
                self.floors_arr['floor'+str(self.current_floor.floor_index+1)]=board.generate_shop(self.current_floor.floor_index,self.player_obj)
            elif (self.current_floor.floor_index+1)%10==0 and self.current_floor.floor_index!=0:
                self.floors_arr['floor'+str(self.current_floor.floor_index+1)]=board.generate_bonus(self.current_floor.floor_index,self.player_obj)
            else:
                self.floors_arr['floor'+str(self.current_floor.floor_index+1)]=board.generate_next_level(self.current_floor.floor_index,self.player_obj)
        
        else:
            if self.istutorial:
                self.floors_arr['floor-5']=board.generate_next_level(-6,self.player_obj)
                self.current_floor=self.floors_arr['floor-5']
            else:
                self.floors_arr['floor0']=board.generate_next_level(-1,self.player_obj)
                self.current_floor=self.floors_arr['floor0']
            
    def button_handle(self,event): 
        prev = (self.current_floor.player_pos[0],self.current_floor.player_pos[1])
        arr = self.current_floor.move_character(event)#print(event+" pressed")
        directions={'w':[-1,0],'s':[1,0],'a':[0,-1],'d':[0,1]}
        if test==True:
            print(arr)
        
        if len(arr[1])>0:
            self.charinfo.messages.insert('end-1c',arr[1]+'\n')
            if arr[2]=='floor':#Fix This
                if arr[1].endswith('Up.'):
                    self.generate_next_level()
                    if 'floor'+str(self.current_floor.floor_index+1) in self.floors_arr.keys():
                        self.current_floor=self.floors_arr['floor'+str(self.current_floor.floor_index+1)]
                        self.current_floor.player_pos = self.current_floor.entrance_pos
                        self.gameboard.init_floor()
                    else:
                        self.charinfo.messages.insert('end-1c','Last Floor Reached\n')
                if arr[1].endswith('Down.'):
                    if 'floor'+str(self.current_floor.floor_index-1) == 'floor0':
                        self.current_floor=self.floors_arr['floor'+str(self.current_floor.floor_index-1)]
                        self.current_floor.player_pos = self.current_floor.exit_pos
                        self.gameboard.init_floor()
                    else:
                        self.charinfo.messages.insert('end-1c','First Floor Reached\n')
            elif arr[2]=='shop':
                s= self.current_floor.events[(self.current_floor.player_pos[0]+directions[event][0],self.current_floor.player_pos[1]+directions[event][1])].shop
                print(s)
                self.key_bind_unset()
                self.gameboard.create_shop_window(s)
            elif arr[2]=='combat':
                ev = self.current_floor.events[(self.current_floor.player_pos[0]+directions[event][0],self.current_floor.player_pos[1]+directions[event][1])]
                if ev.completed[0] ==False:
                    self.key_bind_unset()
                    self.gameboard.create_combat_window(ev,event)
                    
        if self.current_floor.player_obj.is_dead():
            self.gameboard.gameover_window()        
        self.charinfo.on_update()
        self.gameboard.update_current_map(prev)

    def key_bind_unset(self):
        self.master.unbind('w')
        self.master.unbind('a')
        self.master.unbind('s')
        self.master.unbind('d')
        self.master.unbind('<Left>')
        self.master.unbind('<Right>')
        self.master.unbind('<Up>')
        self.master.unbind('<Down>')
    def key_bind_set2(self):
        self.master.bind('w',lambda e: self.gameboard.button_handle('w'))
        self.master.bind('a',lambda e: self.gameboard.button_handle('a'))
        self.master.bind('s',lambda e: self.gameboard.button_handle('s'))
        self.master.bind('d',lambda e: self.gameboard.button_handle('d'))
        self.master.bind('<Left>', lambda e: self.gameboard.button_handle('a'))
        self.master.bind('<Right>', lambda e: self.gameboard.button_handle('d'))
        self.master.bind('<Up>', lambda e: self.gameboard.button_handle('w'))
        self.master.bind('<Down>', lambda e: self.gameboard.button_handle('s'))
    def key_bind_set(self):
        self.master.bind('w',lambda e: self.button_handle('w'))
        self.master.bind('a',lambda e: self.button_handle('a'))
        self.master.bind('s',lambda e: self.button_handle('s'))
        self.master.bind('d',lambda e: self.button_handle('d'))
        self.master.bind('<Left>', lambda e: self.button_handle('a'))
        self.master.bind('<Right>', lambda e: selfbutton_handle('d'))
        self.master.bind('<Up>', lambda e: self.button_handle('w'))
        self.master.bind('<Down>', lambda e: self.button_handle('s'))
    
    ##Unused    
    def load_levels(self):#needs fixing, uses existing object need a new copy per use of that floor | Use dict maybe?
        #self.floors_arr={}
        self.floors_arr = board.generate_levels(1,10,self.player_obj)
        self.current_floor = self.floors_arr['floor1']
        
        
        self.key_bind_set()
    
    
class Character_Creation(tk.Frame):#(parent)#implement Load character
    def __init__(self,master,**args):
        tk.Frame.__init__(self,master,**args)
        self.master=master
        
        #self.creation_menu=None
        self.player=None
        self.menu()
    
    def menu(self):
        tk.Label(self,text="Enter a Name").grid(column=0,row=0)
        self.name_entry = tk.Entry(self)
        self.name_entry.insert(10,'Johnathy')
        self.name_entry.grid(column=1,row=0)
        
        self.tutorial_enabled = tk.IntVar()
        self.tutorial_enabled.set(0)
        self.check_tutorial = tk.Checkbutton(self,text='Enable Tutorial',variable =self.tutorial_enabled,onvalue=1,offvalue=0)
        self.check_tutorial.grid(columnspan=2)
        
        file_select = tk.Button(self,text="choose a file",command=self.ask_file)
        file_select.grid(column=0,row=8,columnspan=2,sticky='we',pady=2)
        self.filename = tk.Label(self,text="")
        self.filename.grid(column=0,row=9,columnspan=2)
        
        confirm = tk.Button(self,text='Confirm',command=self.confirm)
        confirm.grid(column=0,row=10,columnspan=2,sticky='we')
        
    def menu_child_window(self):
        #self.master.master.iconify()
        
        x,y,cx,cy = self.master.bbox("insert")
        x = x + self.master.master.winfo_x()
        y = y + cy + self.master.master.winfo_y()
        self.creation_menu = cm = tk.Toplevel(self.master)
        self.creation_menu.wm_geometry(f"+{x}+{y}")
        cm.wm_overrideredirect(1)
        #cm.grab_set()
        self.masterframe = tk.Frame(cm,width=200,height=200)
        
        tk.Label(self.masterframe,text="Enter a Name").grid(column=0,row=0)
        self.name_entry = tk.Entry(self.masterframe)
        self.name_entry.insert(10,'Johnathy')
        self.name_entry.grid(column=1,row=0)
        
        '''
        Class selection?
        
        '''
        file_select = tk.Button(self.masterframe,text="choose a file",command=self.ask_file)
        file_select.grid(column=0,row=8,columnspan=2,sticky='we',pady=2)
        self.filename = tk.Label(self.masterframe,text="")
        self.filename.grid(column=0,row=9,columnspan=2)
        
        confirm = tk.Button(self.masterframe,text='Confirm',command=self.confirm)
        confirm.grid(column=0,row=10,columnspan=2,sticky='we')
        
        self.masterframe.pack(padx=10,pady=10)        
    def ask_file(self):
        filename = None
        filename=filedialog.askopenfilename(initialdir='C:/Users',filetypes=[('Images',('*.jpg','*.png','*.gif'))])
        if filename != '':
            shutil.copy2(filename,os.getcwd())
            if os.path.isfile('./src/bg1.gif'):
                os.remove('./src/bg1.gif')
            os.rename(filename.split('/')[-1],"./src/bg1.gif")
            self.filename.config(text=filename.split('/')[-1],relief='raised')
    def confirm(self):#remember to unpack this window
        self.master.player_obj=objects.Player(self.name_entry.get(),_maxhp=100,_maxmana=100)
        self.master.finish_character_create()

class Combat_Window(tk.Frame):#(parent,eventobj,prevDirection)
    def __init__(self,master,event,direction):
        tk.Frame.__init__(self,master)
        self.master=master
        
        #self.combatwindow=None
        
        self.directionafter=direction
        self.event=event
        self.monster=event.monster
        self.player=self.master.player_obj#event.player
        self.turns=0
        self.turn_order=[]
        self.combat_log=[]
        
        self.create_frame()
        self.status_ui()
        self.menu_ui()
    
    def create_frame(self):
        self.upperframe= tk.Frame(self,width=428,height=275,relief='raised',bg='darkgrey')#put models here
        self.lowerframe= tk.Frame(self,width=428,height=290,bg='lightgrey')
        self.upperframe.pack_propagate(False)
        self.lowerframe.pack_propagate(False)
        self.upperframe.grid(column=0,row=0)
        self.lowerframe.grid(column=0,row=1)
    
    def status_ui(self):
        self.player_frame = tk.Frame(self.upperframe)
        self.player_frame.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)
        self.player_frame.columnconfigure(0,weight=1)
        self.player_frame.columnconfigure(1,weight=1)
        
        tk.Label(self.player_frame,anchor='center',text=f'{self.player.name}').grid(sticky='we',columnspan=2)

        self.p_labels=[
            tk.Label(self.player_frame,anchor='e',text=f'Health:'),
            HorizontalMeterBar(self.player_frame,self.master.player_obj.currhp,self.master.player_obj.maxhp,'hp',cheight=25,font=self.master.gamefont),
            #tk.Label(self.player_frame,anchor='w',text=f'{self.player.currhp}/{self.player.maxhp}'),
            tk.Label(self.player_frame,anchor='e',text=f'Mana:'),
            HorizontalMeterBar(self.player_frame,self.master.player_obj.currmp,self.master.player_obj.maxmp,'mp',cheight=25,font=self.master.gamefont),
            tk.Label(self.player_frame,anchor='e',text=f'Attack:'),
            tk.Label(self.player_frame,anchor='w',text=f'{self.player.attack}'),
            tk.Label(self.player_frame,anchor='e',text=f'Defense:'),
            tk.Label(self.player_frame,anchor='w',text=f'{self.player.defence}'),
            tk.Label(self.player_frame,anchor='e',text=f'Hitchance:'),
            tk.Label(self.player_frame,anchor='w',text=f'{int(self.player.hitchance*100)}%'),
        ]
        for i in range(0,len(self.p_labels),2):
            self.p_labels[i].grid(column=0,row=i+1,sticky='e')
            self.p_labels[i+1].grid(column=1,row=i+1,sticky='w')
        
        self.center_info = tk.Frame(self.upperframe)
        self.center_info.pack(side=tk.LEFT)
        

        self.enemy_frame = tk.Frame(self.upperframe)
        self.enemy_frame.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.enemy_frame.columnconfigure(0,weight=1)
        self.enemy_frame.columnconfigure(1,weight=1)
        
        tk.Label(self.enemy_frame,anchor='center',text=f'{self.monster.name}').grid(sticky='we',columnspan=2)
        self.e_labels=[
            tk.Label(self.enemy_frame,anchor='w',text=f'Health:'),
            HorizontalMeterBar(self.enemy_frame,self.monster.currhp,self.monster.maxhp,'hp',cheight=25,font=self.master.gamefont),
#            tk.Label(self.enemy_frame,anchor='w',text=f'{self.monster.currhp}/{self.monster.maxhp}'),
            tk.Label(self.enemy_frame,anchor='w',text=f'Attack:'),
            tk.Label(self.enemy_frame,anchor='w',text=f'{self.monster.attack}'),
            tk.Label(self.enemy_frame,anchor='w',text=f'Defense:'),
            tk.Label(self.enemy_frame,anchor='w',text=f'{self.monster.defence}'),
            tk.Label(self.enemy_frame,anchor='w',text=f'Hitchance:'),
            tk.Label(self.enemy_frame,anchor='w',text=f'{int(self.monster.hitchance*100)}%'),
            tk.Label(self.enemy_frame,anchor='w',text=''),
            tk.Label(self.enemy_frame,anchor='w',text=''),
        ]
        for i in range(0,len(self.e_labels),2):
            self.e_labels[i].grid(column=0,row=i+1,sticky='e')
            self.e_labels[i+1].grid(column=1,row=i+1,sticky='w')            
    
    def menu_ui(self):
        #self.message_frame= tk.Frame(self.lowerframe)
        #self.message_frame.pack(fill=tk.X,expand=1,anchor='n')
        
        self.b_frame= tk.Frame(self.lowerframe)
        self.b_frame.pack(fill=tk.BOTH,expand=1,anchor='s')
        self.b_frame.columnconfigure(0,weight=1)
        self.b_frame.columnconfigure(1,weight=1)
        self.b_frame.rowconfigure(1,weight=1)
        self.b_frame.rowconfigure(2,weight=1)
        
        self.message=tk.Label(self.b_frame,text=f'You Encountered a {self.monster.name}',height=5)
        self.message.grid(row=0,column=0,columnspan=2)
        
        self.start_button=HoverButton(self.b_frame,text='Start\nBattle',height=5,width=10,activebackground='lightblue',activeforeground='black',command=self.advance_turn)
        self.run_button=HoverButton(self.b_frame,text='Run',height=5,width=10,activebackground='red',activeforeground='black',command=self.run_battle)
        self.items_button=HoverButton(self.b_frame,text="Items",height=5,activebackground='lightblue',activeforeground='black',width=10,command=self.combat_item_menu)
        self.spells_button=HoverButton(self.b_frame,text="Spells\nNot done",height=5,width=10,activebackground='lightblue',activeforeground='black',command=self.combat_spell_menu)

        self.start_button.grid(row=1,column=0,sticky='nswe')
        self.run_button.grid(row=2,column=0,sticky='nswe')
        self.items_button.grid(row=1,column=1,sticky='nswe')
        self.spells_button.grid(row=2,column=1,sticky='nswe')
        
    def combat_item_menu(self): #make a turn pass
        def back():
            self.i_frame.pack_forget()
            self.b_frame.pack(fill=tk.BOTH,expand=1)
        def no_resize(event):
            if self.inv.identify_region(event.x,event.y)== 'separator':
                return 'break'
        def fill_inventory():
            for row in self.inv.get_children():
                self.inv.delete(row)
            for item in self.player.inventory:
                if isinstance(item,objects.Potion):
                    self.inv.insert('','end',text=item.name,values=("","",item.recovers))
        def item_use(event):
            try:
                inv_id = self.inv.selection()[0]
                item = ITEMS_DICT[self.inv.item(inv_id,'text')]
                self.combat_log.append(str(self.player.use_item(item))+'\n') 
                self.message.config(text=self.combat_log[-1])
                self.advance_turn()
                fill_inventory()
                back()
            except IndexError as e:  
                print(e)
                pass
        self.b_frame.pack_forget()
        self.i_frame = tk.Frame(self.lowerframe)
        self.i_frame.pack(fill=tk.BOTH,expand=1)
        HoverButton(self.i_frame,text='Back',activebackground='lightgrey',activeforeground='black',command=back).pack(side='top',fill='x')
        self.inv = SortSearchTreeview(self.i_frame,selectmode='browse')
        self.inv['columns']=['Attack','Defense','Health']
        self.inv.column('#0',width=245,anchor=tk.W)
        self.inv.column('Attack',width=50,anchor='center')
        self.inv.column('Defense',width=50,anchor='center')
        self.inv.column('Health',width=50,anchor='center')
        self.inv.heading('#0',text="Item",sort_by='name')
        self.inv.heading('Attack',text="Att",sort_by='name')
        self.inv.heading('Defense',text="Def",sort_by='name')
        battle_inv_scroll = ttk.Scrollbar(self.i_frame,orient='vertical',command=self.inv.yview)
        self.inv.heading('Health',text="HP")
        self.inv.configure(yscrollcommand=battle_inv_scroll.set)
        self.inv.pack(side='left',fill='y',expand=1)
        battle_inv_scroll.pack(side='right',fill='y',expand=1)
        self.inv.bind("<Button-1>",no_resize)
        self.inv.bind("<Double-Button-1>",item_use)
        fill_inventory()
    def combat_spell_menu(self): #make a turn pass
        def back():
            self.sp_frame.pack_forget()
            self.b_frame.pack(fill=tk.BOTH,expand=1)
        def get_color(level):
            if self.player.equipped_spells[level].spellvalue[0]=='self':
                return 'lightgreen'
            else:
                return 'pink'
        def get_equipped_spells():
            if self.player.equipped_spells['level:1']!=None: 
                self.level_1.configure(state='normal')
                self.level_1.configure(text=self.player.equipped_spells['level:1'].name,activebackground=get_color('level:1'),activeforeground='black')
            if self.player.equipped_spells['level:2']!=None: 
                self.level_2.configure(state='normal')
                self.level_2.configure(text=self.player.equipped_spells['level:2'].name,activebackground=get_color('level:2'),activeforeground='black')
            if self.player.equipped_spells['level:3']!=None: 
                self.level_3.configure(state='normal')
                self.level_3.configure(text=self.player.equipped_spells['level:3'].name,activebackground=get_color('level:3'),activeforeground='black')
            if self.player.equipped_spells['level:4']!=None: 
                self.level_4.configure(state='normal')
                self.level_5.configure(text=self.player.equipped_spells['level:4'].name,activebackground=get_color('level:4'),activeforeground='black')
                    
        
        self.b_frame.pack_forget()
        self.sp_frame = tk.Frame(self.lowerframe)
        self.sp_frame.pack(fill=tk.BOTH,expand=1)
        HoverButton(self.sp_frame,text='Back',activebackground='lightgrey',activeforeground='black',command=back).pack(side='top',fill='x')
        
        self.sp2_frame= tk.Frame(self.sp_frame)
        self.sp2_frame.pack(fill=tk.BOTH,expand=1)
        self.sp2_frame.columnconfigure(0,weight=1)
        self.sp2_frame.columnconfigure(1,weight=1)
        self.sp2_frame.rowconfigure(0,weight=1)
        self.sp2_frame.rowconfigure(1,weight=1)
        
        self.level_1=HoverButton(self.sp2_frame,text="",width=10,state='disabled')
        self.level_2=HoverButton(self.sp2_frame,text="",width=10,state='disabled')
        self.level_3=HoverButton(self.sp2_frame,text="",width=10,state='disabled')
        self.level_4=HoverButton(self.sp2_frame,text="",width=10,state='disabled')
        get_equipped_spells()
        
        self.level_1.grid(row=0,column=0,sticky='nswe')
        self.level_2.grid(row=1,column=0,sticky='nswe')
        self.level_3.grid(row=0,column=1,sticky='nswe')
        self.level_4.grid(row=1,column=1,sticky='nswe')
        
        print("Create+Implement Spell system")
        
    def run_battle(self):
        self.event.completed[0]=False
        self.master.charinfo.on_update()
        self.master.key_bind_set()
        self.master.charinfo.messages.insert('end-1c',f"{self.player.name} Ran away from {self.monster.name}!")
        self.master.gameboard.canvas.delete(self.master.gameboard.combatframe)
        self.master.charinfo.toggle_top_state()
   
    def advance_turn(self):
        if self.turns==0:
            self.start_button.configure(text="Fight")
            self.start_button.configure(height=2)
            first = random.choices((self.monster,self.player),weights=[40,60])[0]
            self.turn_order.append(first)
            if first==self.monster:
                self.turn_order.append(self.player)
            else:
                self.turn_order.append(self.monster)
            self.combat_log.append(f'{first.name} Strikes First!\n')
        #print(self.turn_order[self.turns%2].name+'\'s attacks '+self.turn_order[(self.turns+1)%2].name)
        self.combat_log.append(self.turn_order[self.turns%2].att_target(self.turn_order[(self.turns+1)%2]))
        if self.turns==0:
            self.message.config(text=self.combat_log[0]+self.combat_log[-1])
        else:
            self.message.configure(text=self.combat_log[-1])
        self.p_labels[1].set_value(self.master.player_obj.currhp)
        self.e_labels[1].set_value(self.monster.currhp)
        
        self.check_win(self.turn_order[(self.turns+1)%2])
        
        self.turns+=1
    
    def check_win(self,target):
        if target.is_dead():
            if self.monster.is_dead():
                self.combat_log.append(f"Combat Completed in {self.turns} turns\n{self.player.name} wins!\n{self.player.name} gained {self.monster.exp}EXP and {self.monster.gold} Gold\n")    
            elif self.player.is_dead():
                self.combat_log.append(f'Combat Completed in {self.turn} turns {self.player.name} loses!\nGame Over\n')
            self.message.config(text=self.combat_log[-1])
            self.b_frame.pack_forget()
            HoverButton(self.lowerframe,text='Combat Complete',activebackground='green',activeforeground='white',command=lambda e=self.player.is_dead():self.complete(e)).pack(fill=tk.BOTH,expand=1)
                
    def complete(self,event):
        if event==False:
            self.event.completed[0]=True
            self.event.completed[1]=''.join(self.combat_log)
            self.master.charinfo.on_update()
            self.master.key_bind_set()
            self.master.button_handle(self.directionafter)
            for line in self.combat_log:
                self.master.charinfo.messages.insert('end-1c',line)
            self.master.gameboard.canvas.delete(self.master.gameboard.combatframe)
            self.master.charinfo.toggle_top_state()


class ShopUi(tk.Frame):#(parent,playerobj,shopobj) - fix shop, remove titles and extend column widths
    def __init__(self,master,shop,**args):
        tk.Frame.__init__(self,master,**args)
        self.master=master
        self.shop=shop
        self.show_ui_frame()
        self.on_update()
        
        
    def show_ui_frame(self):
        self.s_frame = tk.Frame(self,width=470,height=150)
        self.p_frame = tk.Frame(self,width=470,height=150)
        self.s_frame.pack_propagate(False)
        self.p_frame.pack_propagate(False)
        
        self.s_frame.grid(column=0,row=0)
        self.p_frame.grid(column=0,row=1)
        
        tk.Label(self.s_frame,text='Merchant',anchor='w',justify=tk.CENTER).pack(side='top',fill='x')
        self.si = SortSearchTreeview(self.s_frame,selectmode='browse')
        self.si['columns']=['Attack','Defense','Health','Price']
        self.si.column('#0',width=225,anchor=tk.W)
        self.si.column('Attack',width=55,anchor='center')
        self.si.column('Defense',width=65,anchor='center')
        self.si.column('Health',width=50,anchor='center')
        self.si.column('Price',width=55,anchor='center')
        self.si.heading('#0',text="Item",sort_by='name')
        self.si.heading('Attack',text="",sort_by='name')
        self.si.heading('Defense',text="",sort_by='name')
        self.si.heading('Health',text="",sort_by='name')
        self.si.heading('Price',text="Price",sort_by='name')
        shop_scroll = ttk.Scrollbar(self.s_frame,orient='vertical',command=self.si.yview)
        self.si.configure(yscrollcommand=shop_scroll.set)
        self.si.pack(side='left',fill='y',expand=1)
        shop_scroll.pack(side='right',fill='y',expand=1)
        self.si.bind("<Button-1>",self.no_resize)
        self.si.bind("<Double-Button-1>",self.player_buy)
        
        self.player_info = tk.Frame(self.p_frame)
        self.player_info.pack(side='top',fill='x')
        tk.Label(self.player_info,text='Player',anchor='w').pack(side='left')
        self.g_label =tk.Label(self.player_info,text="Gold:",anchor='w')
        self.g_label.pack(side='right')
        self.pi = SortSearchTreeview(self.p_frame,selectmode='browse')
        self.pi['columns']=['Attack','Defense','Health','Price']
        self.pi.column('#0',width=225,anchor=tk.W)
        self.pi.column('Attack',width=55,anchor='center')
        self.pi.column('Defense',width=65,anchor='center')
        self.pi.column('Health',width=50,anchor='center')
        self.pi.column('Price',width=55,anchor='center')
        self.pi.heading('#0',text="Item",sort_by='name')
        self.pi.heading('Attack',text="",sort_by='name')
        self.pi.heading('Defense',text="",sort_by='name')
        self.pi.heading('Health',text="",sort_by='name')
        self.pi.heading('Price',text="Price",sort_by='name')
        
        player_scroll = ttk.Scrollbar(self.p_frame,orient='vertical',command=self.pi.yview)
        self.pi.configure(yscrollcommand=player_scroll.set)
        self.pi.pack(side='left',fill='y',expand=1)
        player_scroll.pack(side='right',fill='y',expand=1)
        self.pi.bind("<Button-1>",self.no_resize)
        self.pi.bind("<Double-Button-1>",self.player_sell)
        
        f3 = tk.Frame(self)
        b1=tk.Button(f3,text='Finish Shopping',command=self.frame_destroy)
        b1.pack(padx=10,pady=10)
        f3.grid(row=2,columnspan=2)   
    
    def fill_inventories(self):
        for row in self.pi.get_children():
            self.pi.delete(row)
        for item in self.master.player_obj.inventory:
            if isinstance(item,objects.Potion):
                self.pi.insert('','end',text=item.name,values=(f"+{item.recovers}",f"{item.type}","",item.price))
            elif isinstance(item,objects.Equipment):
                if item.slot=='weapon':
                    self.pi.insert('','end',text=item.name,values=(f'{item.bonus[0]} Att',f"Hit% {int(item.bonus[1]*100)}","",item.price))
                else:
                    self.pi.insert('','end',text=item.name,values=(f"{item.bonus} Def",f'{item.slot}',"",item.price))
            elif isinstance(item,objects.Spell_book):
                if item.spellvalue[0]=='self':
                    self.pi.insert('','end',text=item.name+'(Spellbook)',values=(f"{item.spellslot}",f'{item.spellvalue[1]}HP',f"{item.cost}MP",item.price))
                else:
                    self.pi.insert('','end',text=item.name+'(Spellbook)',values=(f"{item.spellslot}",f'{item.spellvalue[1]}Dmg',f"{item.cost}MP",item.price))
                
        for row in self.si.get_children():
            self.si.delete(row)
        for item in self.shop.shop_inventory:
            if isinstance(item,objects.Potion):
                self.si.insert('','end',text=item.name,values=(f"+{item.recovers}",f"{item.type}",'',item.price))
            elif isinstance(item,objects.Equipment):
                if item.slot=='weapon':
                    self.si.insert('','end',text=item.name,values=(f'{item.bonus[0]} Att',f"Hit% {int(item.bonus[1]*100)}","",item.price))
                else:
                    self.si.insert('','end',text=item.name,values=(f"{item.bonus} Def",f'{item.slot}',"",item.price))
            elif isinstance(item,objects.Spell_book):
                if item.spellvalue[0]=='self':
                    self.si.insert('','end',text=item.name+'(Spellbook)',values=(f"{item.spellslot}",f'{item.spellvalue[1]}HP',f"{item.cost}MP",item.price))
                else:
                    self.si.insert('','end',text=item.name+'(Spellbook)',values=(f"{item.spellslot}",f'{item.spellvalue[1]}Dmg',f"{item.cost}MP",item.price))
            
    def player_buy(self,event):
        try:
            inv_id = self.si.selection()[0]
            item=ITEMS_DICT[self.si.item(inv_id,'text').split('(')[0]]
            self.master.charinfo.messages.insert('end-1c',self.shop.player_purchase_item(item))
        except IndexError:
            pass
        self.on_update()
    def player_sell(self,event):
        try:
            inv_id = self.pi.selection()[0]
            item=ITEMS_DICT[self.pi.item(inv_id,'text').split('(')[0]]
            self.master.charinfo.messages.insert('end-1c',self.shop.player_sell_item(item))
        except IndexError:
            pass
        self.on_update()
    def on_update(self):
        self.g_label.config(text=f'Gold:{self.master.player_obj.gold :15}      ')
        self.fill_inventories()
        self.master.charinfo.on_update()    
    def no_resize(self,event):
        if self.pi.identify_region(event.x,event.y)== 'separator':
            return 'break'
        if self.si.identify_region(event.x,event.y) == "separator":
            return "break"        
    
    def frame_destroy(self):
        self.master.key_bind_set()
        self.master.charinfo.on_update()
        self.master.gameboard.canvas.delete(self.master.gameboard.shopframe)
        self.master.charinfo.toggle_top_state()
    def end(self):
        self.on_update()
        tw=self.shopWindow
        self.shopWindow=None
        self.master.key_bind_set()
        if tw:
            tw.destroy()

class Portrait(tk.Frame):#(parent)
    def __init__(self,master,**args):
        tk.Frame.__init__(self,master,**args)
        self.master=master.master.master.master.master
        self.canvas = tk.Canvas(self,width=420,height=250)
        #self.player_obj=player_obj
        #self.main_window=main_window
        try:
            self.bg_img = ImageTk.PhotoImage(Image.open('./src/bg1.gif').resize((420,250)) )
            self.canvas.create_image(0,0,anchor='nw',image=self.bg_img)
        except Exception as e:
            print(e)
        #self.canvas.create_line(125,0,125,250,fill='grey')
        #self.canvas.create_line(0,125,250,125,fill='grey')
        #self.label_id = self.canvas.create_text(50,50,text='fugs',justify='center')
        self.draw_squares()
        self.canvas.pack()
        self.item_hover_text()
        self.spell_hover_text()
        
        self.s= ImageTk.PhotoImage(Image.open('b.png'))
        self.canvas.create_image(81,151,anchor='nw',image=self.s)
                
        
        #(x,y,x1,x2)    
    def draw_squares(self):
        self.b_1 = self.canvas.create_rectangle(80,30,110,60,fill="#F0F0F0",tags=("boxes","head"))#head
        self.b_2 = self.canvas.create_rectangle(80,70,110,100,fill="#F0F0F0",tags=("boxes","chest"))#chest
        self.b_3 = self.canvas.create_rectangle(80,110,110,140,fill="#F0F0F0",tags=("boxes","legs"))#pants
        self.b_4 = self.canvas.create_rectangle(120,70,150,100,fill="#F0F0F0",tags=("boxes","hands"))#gloves
        self.b_5 = self.canvas.create_rectangle(80,150,110,180,fill="#F0F0F0",tags=("boxes","feet"))#shoes
        self.b_6 = self.canvas.create_rectangle(40,70,70,100,fill="#F0F0F0",tags=("boxes","weapon"))#weapon 70-40 and 100-70
        self.canvas.tag_bind("boxes","<Double-Button-1>",self.to_unequip)  
        
        '''Style 1
        self.s_1 = self.canvas.create_rectangle(230,30,260,60,fill="#F0F0F0",tags=('spell','spell_slot_1'))
        self.s_2 = self.canvas.create_rectangle(270,30,300,60,fill="#F0F0F0",tags=('spell','spell_slot_2'))
        self.s_3 = self.canvas.create_rectangle(310,30,340,60,fill="#F0F0F0",tags=('spell','spell_slot_3'))
        self.s_4 = self.canvas.create_rectangle(350,30,380,60,fill="#F0F0F0",tags=('spell','spell_slot_4'))
        '''

        self.s_1 = self.canvas.create_rectangle(40,200,70,230,fill="",tags=('spells','level:1'))
        self.s_2 = self.canvas.create_rectangle(80,200,110,230,fill="",tags=('spells','level:2'))
        self.s_3 = self.canvas.create_rectangle(120,200,150,230,fill="",tags=('spells','level:3'))
        self.s_4 = self.canvas.create_rectangle(160,200,190,230,fill="",tags=('spells','level:4'))
        self.canvas.tag_bind("spells","<Double-Button-1>",self.unequip_spell)
        self.canvas.tag_bind("spells","<Button-3>",self.cast_spell)
        
    def to_unequip(self,event):
        clicked_id=event.widget.find_withtag('current')[0]
        selected_gear = self.canvas.gettags(clicked_id)[1]
        if self.master.player_obj.equipped[selected_gear] != None:
            self.master.charinfo.portait_message_update(self.master.player_obj.unequip_by_type(selected_gear))
            self.master.charinfo.on_update()
            self.on_update()    
    def unequip_spell(self,event):
        clicked_id=event.widget.find_withtag('current')[0]
        selected_spell =  self.canvas.gettags(clicked_id)[1]
        if self.master.player_obj.equipped_spells[selected_spell] != None:
            self.master.charinfo.portait_message_update(self.master.player_obj.unequip_spell_by_slot(selected_spell))
            self.master.charinfo.on_update()
            self.on_update()
    def cast_spell(self,event):
        clicked_id=event.widget.find_withtag('current')[0]
        selected_spell =  self.canvas.gettags(clicked_id)[1]
        if self.master.player_obj.equipped_spells[selected_spell] != None:
            if self.master.player_obj.equipped_spells[selected_spell].spellvalue[0]=='self':
                self.master.charinfo.portait_message_update(self.master.player_obj.cast_spell(self.master.player_obj.equipped_spells[selected_spell].name))
            if self.master.player_obj.equipped_spells[selected_spell].spellvalue[0]=='enemy':
                self.master.charinfo.portait_message_update("Cannot use a combat spell out of combat.")
            if self.master.player_obj.equipped_spells[selected_spell].spellvalue[0]=='npc':
                self.master.charinfo.portait_message_update("Cannot talk to an NPC's that have not been implemented")
        self.master.charinfo.on_update()
        self.on_update()
        
    def item_hover_text(self):#Modify this to format string
        tooltip = ToolTip(self)
        def enter(event):
            hovered_id=event.widget.find_withtag('current')[0]#self.canvas.gettags(event))
            selected_tag = self.canvas.gettags(hovered_id)[1]
            if self.master.player_obj.equipped[selected_tag]!=None:
                item_formatted=""
                if isinstance(self.master.player_obj.equipped[selected_tag],objects.Equipment):
                    if self.master.player_obj.equipped[selected_tag].slot=="weapon":
                        item_formatted = f'{self.master.player_obj.equipped[selected_tag].name}\nAttack: {self.master.player_obj.equipped[selected_tag].bonus[0]}\nHit Chance: {self.master.player_obj.equipped[selected_tag].bonus[1]}'
                    else:
                        item_formatted = f'{self.master.player_obj.equipped[selected_tag].name}\nDefence: {self.master.player_obj.equipped[selected_tag].bonus}\n'
                tooltip.show_tooltip(item_formatted)
            else:
                tooltip.show_tooltip("Nothing\nEquipped")
        def leave(event):
            tooltip.hide_tooltip()
        self.canvas.tag_bind("boxes","<Enter>",enter)
        self.canvas.tag_bind("boxes","<Leave>",leave)

    def spell_hover_text(self):#Modify this to format string
        tooltip = ToolTip(self)
        def enter(event):
            hovered_id=event.widget.find_withtag('current')[0]#self.canvas.gettags(event))
            selected_tag = self.canvas.gettags(hovered_id)[1]
            if self.master.player_obj.equipped_spells[selected_tag]!=None:
                tooltip.show_tooltip(f'''{self.master.player_obj.equipped_spells[selected_tag].name}
{self.master.player_obj.equipped_spells[selected_tag].spellslot}
Target:{self.master.player_obj.equipped_spells[selected_tag].spellvalue[0]}
For:{self.master.player_obj.equipped_spells[selected_tag].spellvalue[1]}
MP Cost:{self.master.player_obj.equipped_spells[selected_tag].cost}''')
            else:
                tooltip.show_tooltip("Nothing\nEquipped")
        def leave(event):
            tooltip.hide_tooltip()
        self.canvas.tag_bind("spells","<Enter>",enter)
        self.canvas.tag_bind("spells","<Leave>",leave)
    
    def on_update(self):
        self.equipped_update()
        self.spell_update()
    
    def equipped_update(self):
        for box in self.canvas.find_withtag('boxes'):
            element = self.canvas.gettags(box)[1]
            if self.master.player_obj.equipped[element]==None:
                self.canvas.itemconfig(box,fill="")
            else:
                self.canvas.itemconfig(box,fill="#F0F0F0")
                
    def spell_update(self):
        for spell in self.canvas.find_withtag("spells"):
            element = self.canvas.gettags(spell)[1]
            if self.master.player_obj.equipped_spells[element]==None:
                self.canvas.itemconfig(spell,fill="")
            else:
                self.canvas.itemconfig(spell,fill="#F0F0F0")

class TowerMap(tk.Frame):#(parent) - Incomplete TODO
    def __init__(self,master,**args):
        tk.Frame.__init__(self,master,**args)
        self.master=master.master.master.master.master
        self.canvas = tk.Canvas(self,width=420,height=250)
        self.canvas.pack()
        
        self.testwindow = tk.Toplevel(self)
        self.inc = tk.Button(self.testwindow,text="+",command = lambda:self.increment)
        self.inc.grid()
        self.dec = tk.Button(self.testwindow,text=" - ",command = lambda:self.decrement)
        self.dec.grid(row=0,column=1)
    
    def tutorial_map(self):
        self.canvas.
    
    def decrement(self):
        pass
    def increment(self):
        pass

class ToolTip():
    def __init__(self,widget):
        self.widget=widget
        self.tipwindow=None
        self.id=None
        self.x = self.y = 0
    
    def show_tooltip(self,text):
        self.text=text
        if self.tipwindow or not self.text:
            return
        x,y,cx,cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 200
        y = y + cy + self.widget.winfo_rooty()+20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=2,width=15,
                      #fontvar = 'Consolas' if os.name=='nt' else ''
                      font=("Consolas", "12", "normal"))
        label.pack(ipadx=1)
    
    def hide_tooltip(self):
        tw= self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
        
class CharInfo(tk.Frame):# Incomplete 300x700
    def __init__(self,master,height=500,width=420,**args):
        tk.Frame.__init__(self,master,**args)
        self.master=master
        
        self.charInfoFrame = tk.Frame(self,height=height//2,width=420)
        self.charInfoFrame.pack(side=tk.TOP)

        self.msgLogFrame = tk.Frame(self,height=height//2,width=420)
        self.msgLogFrame.pack(side=tk.BOTTOM)
        
        self.style=ttk.Style()
        self.charinfo = ttk.Notebook(self.charInfoFrame,height=height//2,width=420)
        self.style.configure("Notebook",font=self.master.gamefont)

        self.insert_tabs()
        self.charinfo.pack()
        
        self.messages = tk.Text(self.msgLogFrame,height=15,width=47,exportselection=0,font=self.master.gamefont)
        self.messages.insert('end-1c','Game Started\n')
        self.messages.bind("<Key>",lambda e:"break")
        self.messages.bind("<Button-1>",lambda e:"break")
        self.messages.bind("<<Modified>>",lambda e:self.scroll_messages(e))
        self.messages.pack()
    
    def scroll_messages(self,event):
        self.messages.see(tk.END)
        self.messages.edit_modified(0)    
    def insert_tabs(self):
        self.create_stats_tab()
        self.charinfo.add(self.charname,text='Character')
        self.create_equipment_tab()
        self.charinfo.add(self.equipment,text='Equipment')
        self.create_inventory_tab()
        self.charinfo.add(self.inventoryFrame,text='Inventory')
        self.create_spell_tab()        
        self.charinfo.add(self.spellinventoryFrame,text="Spells")
        self.create_options_tab()
        self.charinfo.add(self.helpmenu,text='Help')
        self.charinfo.add(self.optionsmenu,text="Main Menu")
        self.create_map_tab()
        self.charinfo.add(self.mapmenu,text="Floors Explored")
        
    def create_stats_tab(self):
        #create child frame
        self.charname = ttk.Frame(self.charinfo)
        #add to child frame
        for i,stat in enumerate(('Name','Level','Health','Mana','Attack','Defence','Experience','Gold')):
            tk.Label(self.charname,text=stat+':',font=self.master.gamefont).grid(row=i,column=0,sticky='e')
        self.levelvar=tk.StringVar()
        self.attackvar=tk.StringVar()
        self.defencevar=tk.StringVar()
        self.goldvar=tk.StringVar()
        self.nameLabel = tk.Label(self.charname,text=self.master.player_obj.name,font=self.master.gamefont)
        self.nameLabel.grid(row=0,column=1,sticky='w')
        self.levelLabel = tk.Label(self.charname,textvariable=self.levelvar,font=self.master.gamefont)
        self.levelLabel.grid(row=1,column=1,sticky='w')
        self.healthLabel = HorizontalMeterBar(self.charname,self.master.player_obj.currhp,self.master.player_obj.maxhp,'hp',cheight=25,font=self.master.gamefont)
        self.healthLabel.grid(row=2,column=1,sticky='w')
        self.manaLabel = HorizontalMeterBar(self.charname,self.master.player_obj.currmp,self.master.player_obj.maxmp,'mp',cheight=25,font=self.master.gamefont)
        self.manaLabel.grid(row=3,column=1,sticky='w')
        self.attackLabel = tk.Label(self.charname,textvar=self.attackvar,font=self.master.gamefont)
        self.attackLabel.grid(row=4,column=1,sticky='w')
        self.defenceLabel = tk.Label(self.charname,textvar=self.defencevar,font=self.master.gamefont)
        self.defenceLabel.grid(row=5,column=1,sticky='w')
        self.expLabel = HorizontalMeterBar(self.charname,self.master.player_obj.exp,100*self.master.player_obj.level,'exp',cheight=25,font=self.master.gamefont)
        self.expLabel.grid(row=6,column=1,sticky='w')
        self.goldLabel = tk.Label(self.charname,textvar=self.goldvar,font=self.master.gamefont)
        self.goldLabel.grid(row=7,column=1,sticky='w')
        self.stats_updated()        
    def create_equipment_tab(self):
        self.equipment = ttk.Frame(self.charinfo)
        self.portrait = Portrait(self.equipment)
        self.portrait.pack()
    def create_inventory_tab(self):
        self.inventoryFrame = ttk.Frame(self.charinfo)
        self.inventory = SortSearchTreeview(self.inventoryFrame,selectmode='browse')
        self.inventory['columns']=('Attack','Defense','Health')
        self.inventory.column('#0',width=95,anchor=tk.W)
        self.inventory.column('Attack',width=5,anchor='center')
        self.inventory.column('Defense',width=5,anchor='center')
        self.inventory.column('Health',width=5,anchor='center')
        self.inventory.heading('#0',text='Item',sort_by='name')
        self.inventory.heading('Attack',text='Att',sort_by='name')
        self.inventory.heading('Defense',text='Def',sort_by='name')
        self.inventory.heading('Health',text='Recovers',sort_by='name')
        self.inventory.pack(side=tk.TOP,fill=tk.BOTH)
        self.inventory.bind("<Button-1>",self.no_resize)
        self.inventory.bind("<Double-Button-1>",self.on_inventory_double)
        self.inventory_updated()
        
        self.style.configure("Treeview.Heading",font=self.master.gamefont)
        self.style.configure("Treeview.Column",font=self.master.gamefont)
    def create_spell_tab(self):
        self.spellinventoryFrame = ttk.Frame(self.charinfo)
        self.learnedspells = ttk.Treeview(self.spellinventoryFrame,selectmode='browse')
        self.learnedspells['columns']=('one','two','three','four')
        self.learnedspells.column('#0',width=95,anchor=tk.W)
        self.learnedspells.column('one',width=3,anchor='center')
        self.learnedspells.column('two',width=4,anchor='center')
        self.learnedspells.column('three',width=4,anchor='center')
        self.learnedspells.column('four',width=4,anchor='center')
        self.learnedspells.heading('#0',text="Name")
        self.learnedspells.heading('one',text="Slot")
        self.learnedspells.heading('two',text="Target")
        self.learnedspells.heading('three',text="Value")
        self.learnedspells.heading('four',text="MPcost")
        self.learnedspells.pack(fill='both',expand=1)
        self.learnedspells.bind("<Button-1>",self.no_resize)
        self.learnedspells.bind("<Double-Button-1>",self.on_spells_double)
        self.spells_updated()
    def create_options_tab(self):
        self.optionsmenu = ttk.Frame(self.charinfo)
        def get_fg_color():
            color=colorchooser.askcolor(title='Foreground Color')
            self.master.gameboard.board_color = color[1]
            self.master.gameboard.update_colors()
        def get_bg_color():
            color=colorchooser.askcolor(title='Background Color')
            self.master.gameboard.board_fill = color[1]
            self.master.gameboard.update_colors()
            
        tk.Button(self.optionsmenu,text='choose BG color',command=get_bg_color).pack() 
        tk.Button(self.optionsmenu,text='choose FG color',command=get_fg_color).pack()
        tk.Button(self.optionsmenu,text='Save Game').pack()
        
        self.helpmenu = ttk.Frame(self.charinfo)
        tk.Label(self.helpmenu,text='Key',font=self.master.gamefont).pack()
        keystring = f'''{CHAR_DICT['*']} = Player\n{CHAR_DICT['#']} = Wall\n{CHAR_DICT['d']} = Door\n{CHAR_DICT['m']} = Monster\n{CHAR_DICT['g']} = Gold\n{CHAR_DICT['c']} = Chest\n{CHAR_DICT['.']} = Entrance\n{CHAR_DICT['!']} = Exit'''
        tk.Label(self.helpmenu,text=keystring,font=self.master.gamefont,justify=tk.LEFT).pack()   
    def create_map_tab(self):
        self.mapmenu = ttk.Frame(self.charinfo)
        self.tower = TowerMap(self.mapmenu)
        self.tower.pack()
    
    def toggle_top_state(self):
        if self.charinfo.instate(['disabled']):
            self.charinfo.state(['!disabled'])
        else:
            self.charinfo.state(['disabled'])
    
    def on_inventory_double(self,event):
        try:
            inv_id = self.inventory.selection()[0]
            item = ITEMS_DICT[self.inventory.item(inv_id,'text').split("(")[0]]
            self.messages.insert('end',str(self.master.player_obj.use_item(item))+'\n') 
            self.portrait.on_update()
            self.on_update()
        except IndexError:  
            pass
    
    def on_spells_double(self,event):
        try:
            inv_id = self.learnedspells.selection()[0]
            spell= objects.Spell_book.get_spell(self.learnedspells.item(inv_id,'text'))
            self.messages.insert('end',str(self.master.player_obj.equip_spell(spell))+'\n') 
            self.portrait.on_update()
            self.on_update()
        except IndexError:  
            pass

    def inventory_updated(self):
        for row in self.inventory.get_children():
            self.inventory.delete(row)
        for item in self.master.player_obj.inventory:
            if isinstance(item,objects.Potion):
                if item.type=='health':
                    self.inventory.insert('','end',text=item.name,values=("","",f'{item.recovers}HP'))
                elif item.type=='mana': 
                    self.inventory.insert('','end',text=item.name,values=("","",f'{item.recovers}MP'))
            elif isinstance(item,objects.Equipment):
                if item.slot=='weapon':
                    self.inventory.insert('','end',text=item.name,values=(f'{item.bonus[0]} | {item.bonus[1]}',"",""))
                else:
                    self.inventory.insert('','end',text=item.name,values=("",f"{item.bonus}({item.slot})",""))
            elif isinstance(item,objects.Spell_book):
                self.inventory.insert("","end",text=item.name+"(Spell Book)",values=("","",""))
    
    def spells_updated(self):
        for row in self.learnedspells.get_children():
            self.learnedspells.delete(row)
        for spell in self.master.player_obj.learned_spells:
            if isinstance(spell,objects.Spell):
                self.learnedspells.insert('','end',text=spell.name,values=(spell.spellslot,spell.spellvalue[0],spell.spellvalue[1],spell.cost))
   
    def stats_updated(self):
        #self.healthvar.set(str(self.master.player_obj.currhp)+'/'+str(self.master.player_obj.maxhp))
        #self.manavar.set(str(self.master.player_obj.currmp)+'/'+str(self.master.player_obj.maxmp))
        self.healthLabel.max=self.master.player_obj.maxhp
        self.healthLabel.set_value(self.master.player_obj.currhp)
        
        self.manaLabel.max=self.master.player_obj.maxmp
        self.manaLabel.set_value(self.master.player_obj.currmp)
        
        self.levelvar.set(str(self.master.player_obj.level))
        self.attackvar.set(str(self.master.player_obj.attack))
        self.defencevar.set(str(self.master.player_obj.defence))
        #self.expvar.set(str(self.master.player_obj.exp)+'/'+str(100*self.master.player_obj.level) )
        self.expLabel.max=100*self.master.player_obj.level
        self.expLabel.set_value(self.master.player_obj.exp)
        self.goldvar.set(self.master.player_obj.gold)
    
    def no_resize(self,event):
        if self.inventory.identify_region(event.x,event.y) == "separator":
            return "break"
        if self.learnedspells.identify_region(event.x,event.y)=='separator':
            return 'break'
        
    def on_update(self):
        self.inventory_updated()
        self.spells_updated()
        self.stats_updated()
         
    def portait_message_update(self,message):
        self.messages.insert('end-1c',message+'\n')
    
class Visual_Board(tk.Frame):# Incomplete 500x700
    def __init__(self,master,color='#00ff00',fill='black',**args):
        tk.Frame.__init__(self,master,width=700,height=555,**args)#,width=500,height=700,bg='black'
        self.master=master
        self.board_fill=fill
        self.board_color=color
        self.canvas = tk.Canvas(self,width=700,height=555,bg=fill)
        self.canvas.pack()
        self.canvas_items={}
        self.init_floor()

    def update_colors(self):
        self.canvas.config(bg=self.board_fill)
        for item in self.canvas_items:
            self.canvas.itemconfig(self.canvas_items[item],fill=self.board_color)

    def clear_board(self):
        self.canvas.delete('all')
        self.canvas_items.clear()#canvas text ids
        
    def init_floor(self):
        BOX=20#cell size
        self.clear_board()
        board_width=len(self.master.current_floor.floor[0])
        board_height=len(self.master.current_floor.floor)
        center = ((self.canvas.winfo_reqwidth()-4)//2,(self.canvas.winfo_reqheight()-4)//2)
        self.canvas['bg'] = self.board_fill
        if board_width%2==0:
            top_left_corner = (center[0]-(BOX*(board_width//2)),center[1]-(BOX*(board_width//2)))
        else:
            top_left_corner = (center[0]-((BOX*(board_width//2))+10),center[1]-((BOX*(board_width//2))+10))
        
        for row in range(board_height):
            for column in range(board_width):
                x1,y1 = top_left_corner[0]+(BOX*column),top_left_corner[1]+(BOX*row)
                #x2,y2 = x1+BOX,y1+BOX
                self.canvas_items[(row,column)] = self.canvas.create_text(x1+10,y1+10,fill=self.board_color,font=('consolas',16),text=CHAR_DICT[self.master.current_floor.floor[row][column]])
                if self.master.current_floor.player_pos[0]==row and self.master.current_floor.player_pos[1]==column:
                    self.canvas.itemconfig(self.canvas_items[(row,column)],text=CHAR_DICT['*'])
                  
    def create_shop_window(self,s):
        self.shopframe = self.canvas.create_window((self.canvas.winfo_reqwidth()-4)//2,(self.canvas.winfo_reqheight()-4)//2,window=ShopUi(self.master,s))    
        self.master.charinfo.toggle_top_state()     
        
    def create_combat_window(self,ev,event):
        self.combatframe = self.canvas.create_window( (self.master.winfo_reqwidth()),0,anchor=tk.NE,window=Combat_Window(self.master,ev,event))
        self.master.charinfo.toggle_top_state()
                        
    def update_current_map(self,prev):
        if prev in self.master.current_floor.events:
            if self.master.current_floor.events[prev].completed[0]==True:
                self.canvas.itemconfig(self.canvas_items[prev],text=CHAR_DICT['s'])
        else:
            self.canvas.itemconfig(self.canvas_items[prev],text=CHAR_DICT[self.master.current_floor.floor[prev[0]][prev[1]]])
        self.canvas.itemconfig(self.canvas_items[(self.master.current_floor.player_pos[0],self.master.current_floor.player_pos[1])],text=CHAR_DICT['*'])
    
    def gameover_window(self):
        self.master.key_bind_unset()
        self.master.charinfo.messages.insert('end-1c','Game Over...\n')

def center(win):
    screen_width=win.winfo_screenwidth()
    screen_height=win.winfo_screenheight()
    x_offset = int((screen_width/2) - (1050/2))
    y_offset = int((screen_height/2) - (525/2))
    win.geometry(f'+{x_offset}+{y_offset}')

if __name__=="__main__":
    root = tk.Tk()
    root.eval("tk::PlaceWindow %s center" %root.winfo_pathname(root.winfo_id()))
    #root.geometry('250x250')
    root.resizable(1,1)
    root.title("")
    center(root)
    app =Base_Window(root)
    #app =tester(root)
    
    app.mainloop()
    
