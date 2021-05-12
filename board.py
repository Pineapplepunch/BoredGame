import random,re,copy,json
import objects
import os
from ast import literal_eval
#http://code.activestate.com/recipes/82965-threads-tkinter-and-asynchronous-io/
#https://www.devdungeon.com/content/colorize-terminal-output-python
'''
char_dict ={
        's':u'\u0000',#0  empty space   pass through
        '#':u'\u25a0',#1  wall          block permanent
        'd':u'\u039e',#2  door          pass through
        'm':u'\u046A',#3  monster       block until kill, event tile
        'g':u'\u00a9',#4  currency      pass through
        'c':u'\u2302',#5  chest         block permanent, event tile
        '?':u'\u0000',#6  trap          pass through
        '.':u'\u0488',#7  entrance      pass through
        '!':u'\u0489',#8  exit          pass through
        '*':u'\u03a8',#9  player        is object
        '$':u'\u2664',#10 shop          block permanent, event tile
}'''
char_dict={
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

char_legend = (
            u'\u0000',
            u'\u25a0',
            u'\u039e',
            u'\u046A',#25e6 | 046A | 03DE
            u'\u00a9',
            u'\u2302',
            u'\u0000',
            u'\u0488',
            u'\u0489',#u20aa
            u'\u03a8')

#ITEMS_LIST=objects.ITEMS_LIST

flag=True

class complexEncoder(json.JSONEncoder):
    def default(self,obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self,obj)

class Board():#(floorarr,player,mob_list,entrance_pos,exit_pos,floor_index)
    #boards_dict={}
    def __init__(self,floorarr,player,mob_list,entrance_pos,exit_pos,floor_index,floor_title):
        self.floor_index=floor_index
        self.mob_list= mob_list
        self.player_obj=player
        self.events={}
        self.player_pos=[None,None]
        self.exit_pos=exit_pos
        self.entrance_pos=entrance_pos
        self.floor_title=floor_title
        self.floor= self.fill_events(floorarr)#creates events returns unmodified boardarr
        self.player_pos[0],self.player_pos[1]= copy.deepcopy(self.entrance_pos[0]),copy.deepcopy(self.entrance_pos[1])
        #initialize shops with player object reference
        for shop in objects.SHOP_DICT.values():
            shop.player=self.player_obj
        #Board.boards_dict['floor'+str(floor_index)]=self
    def fill_events(self,floorarr):
        for i in range(len(floorarr)):
            for j in range(len(floorarr[i])):
                if floorarr[i][j] in ('m','c','g','?','$'):
                    self.create_event(floorarr[i][j],(i,j))
        return floorarr
    def create_event(self,type,coordinate):
        if type =='m':
            pool =[]
            for m in self.mob_list:
                pool.append(objects.MONSTERS_DICT[m])
            if len(pool)>1:
                m = copy.deepcopy(pool[random.randint(0,len(pool)-1)])
            else:
                m = copy.deepcopy(pool[0])
            newEvent = BoardEvent(player=self.player_obj,type=type,monster=m)
            self.events[coordinate]=copy.deepcopy(newEvent)
        elif type =='c':
            if self.floor_index==1:
                bonus=1
            else:
                bonus=0
            c = objects.Chest(max_rarity=random.choice([self.floor_index,self.floor_index-1+bonus]),num_rolls=random.randint(1,3))
            newEvent = BoardEvent(player=self.player_obj,type=type,chest=c)
            self.events[coordinate]=copy.deepcopy(newEvent)
        elif type=='g':
            newEvent = BoardEvent(player=self.player_obj,type=type,chest=self.floor_index+1)
            self.events[coordinate]=copy.deepcopy(newEvent)
        elif type=="?":
            newEvent = BoardEvent(player=self.player_obj,type=type,trap=random.choices(list(objects.TRAPS.items()),weights=(40,30,20,10),k=1 )[0])
            self.events[coordinate]=copy.deepcopy(newEvent)
        elif type=="$":
            if flag:
                s=objects.Shop(self.player_obj,["Small HP Potion","Medium HP Potion","Small MP Potion"])
                newEvent = BoardEvent(player=self.player_obj,type=type,shop=s)
            else:
                newEvent = BoardEvent(player=self.player_obj,type=type,shop=objects.SHOP_DICT['floor'+str(self.floor_index)])
            self.events[coordinate]=newEvent
        
    def move_character(self,direction):
        directions={'w':[-1,0],'s':[1,0],'a':[0,-1],'d':[0,1]}
        newpos = (self.player_pos[0]+directions[direction][0],self.player_pos[1]+directions[direction][1])
        result=["","",""]
        
        if list(newpos)==self.exit_pos:
            self.player_pos[0],self.player_pos[1] = copy.deepcopy(self.entrance_pos[0]),copy.deepcopy(self.entrance_pos[1])
            return [True,'Going Up.','floor']
        elif list(newpos)==self.entrance_pos: 
            self.player_pos[0],self.player_pos[1] = copy.deepcopy(self.exit_pos[0]),copy.deepcopy(self.exit_pos[1])
            return [True,'Going Down.','floor']   
        elif newpos in self.events:
            if self.events[newpos].completed[0] == False:
                result = self.events[newpos].complete_event()
                if self.player_obj.is_dead(): return [False,'You Lose\nGame Over.\n','gameover']
                if result[0]!=False:
                    self.player_pos[0] = newpos[0]
                    self.player_pos[1] = newpos[1]
            if self.events[newpos].completed[0]==True:
                self.player_pos[0] = newpos[0]
                self.player_pos[1] = newpos[1]
        else:
            if not self.floor[newpos[0]][newpos[1]] in ('#'):
                self.player_pos[0] = newpos[0]
                self.player_pos[1] = newpos[1]
        return result
    def convert_event_keys(self):
        converted_events = {}
        for key,value in self.events.items():
            converted_events[str(key)] = value
        return converted_events
    
    def reprJSON(self):
        return dict(
            #player_obj=self.player_obj,
            player_pos=self.player_pos,
            entrance=self.entrance_pos,
            exit=self.exit_pos,
            floor_index=self.floor_index,
            floor_title=self.floor_title,
            mob_list=self.mob_list,
            events=self.convert_event_keys(),
            floor=self.floor
        )
    ##Text Traversal
    
    def show_floor_fancy(self):
        #os.system('cls' if os.name=='nt' else 'clear')
        #os.system('cls||clear')
        os.system('color 2' if os.name=='nt' else '')
        for x in range(len(self.floor)):
            for y in range(len(self.floor[x])):
                if self.player_pos[0]==x and self.player_pos[1]==y:
                    print(char_dict['*'],end=" ")
                else:
                    if (x,y) in self.events:
                        if self.events[(x,y)].completed[0]==True:
                            print(" ",end=" ")
                        else:
                            print(char_dict[self.floor[x][y]],end=" ")
                    else:
                        print(char_dict[self.floor[x][y]],end=" ")
            print()    
    def ask_command(self):
        print("Floor "+str(self.floor_index))
        self.show_floor_fancy()
        command=input("Enter a desired command (Move, char): ")
        res=["",'','']
        if command.lower().startswith('m'):
            dir=""
            if len(command.split()) == 2:
                dir = command.split()[1][0]
            else:
                dir = input("Enter a direction: ")[0]
                while dir not in ('a','w','d','s'):
                    dir = input("Enter a direction: ")
            res = self.move_character(dir)
            if res[2]!="floor":
                print(res[1])
        if command.lower().startswith('c') or command.lower().startswith('p'):
            print(self.player_obj)
        if command.lower() != 'exit' and command.lower().startswith('e'):
            print(self.player_obj.list_equipped()+'\n')
            print(self.equipment_commands())
        if command.lower().startswith('i'):
            print(self.player_obj.list_inventory()+'\n')
            print(self.inventory_commands())
        if command.lower().startswith('b'):
            self.show_floor_regular()
        if command.lower().startswith('q'):
            print('\n'.join([event.__repr__() for event in self.events.values()]))
        
        input('...')
        
        if res[2]=='floor':
            os.system('cls' if os.name=='nt' else 'clear')
            return res[0]
        
        os.system('cls' if os.name=='nt' else 'clear')    
    def equipment_commands(self):
        def conf_callback(type):
            command=input("Unequip "+type+"? (y/n): ")
            if command.lower().startswith('y'):
                return True
            elif command.lower().startswith('n'):
                return False
            else: 
                print("Answer (y/n)")
                conf_callback(type)
        command=input("Select Item to unequip, blank for none(helmet,chest,gloves,pants,shoes,weapon): ")
        if len(command)==0:
            print("Canceled")
            return ""
        if command.lower().startswith('h'):
            if conf_callback('helmet')==True:return self.player_obj.unequip_by_type('helmet')
        if command.lower().startswith('c'):
            if conf_callback('chest')==True:return self.player_obj.unequip_by_type('chest')
        if command.lower().startswith('g'):
            if conf_callback('gloves')==True:return self.player_obj.unequip_by_type('gloves')
        if command.lower().startswith('p'):
            if conf_callback('pants')==True:return self.player_obj.unequip_by_type('pants')
        if command.lower().startswith('s'):
            if conf_callback('shoes')==True:return self.player_obj.unequip_by_type('shoes')
        if command.lower().startswith('w'):
            if conf_callback('weapon')==True:return self.player_obj.unequip_by_type('weapon')
    def inventory_commands(self):
        def conf_callback(item_index):
            item =self.player_obj.inventory[item_index]
            f='Use' if isinstance(item,objects.Potion) else 'Equip'
            f+=f' {item.name}? (y/n)'
            command=input(f)
            if command.lower().startswith('y'):
                return True
            elif command.lower().startswith('n'):
                return False
            else: 
                print("Answer (y/n)")
                conf_callback(item_index)
        command=input("select an item number to use/equip or blank to exit: ")
        if len(str(command))==0:
            print('canceled')
            return ""
        try:
            command=int(command)
        except Exception as e:
            print('please enter a number.')
            return ""
        if conf_callback(command)==True:return self.player_obj.use_item(self.player_obj.inventory[command])       
    def __str__(self):
       return( f'Floor: {self.floor_index},\n{self.mob_list},\n{self.player_pos},\n{self.exit_pos},\n{self.events}' )
      
class BoardEvent():#player,type,[shop|chest|monster|trap]
    def __init__(self,player,type,shop=None,chest=None,monster=None,trap=None,completed=[False,"","event"]):
        self.player=player
        self.type=type
        self.monster=monster
        self.shop=shop
        self.chest=chest
        self.trap=trap
        self.completed=completed
    def complete_event(self):
        if self.type=='m' and self.completed[0]==False:
            if __name__=='__main__':self.completed=[True,''.join(self.combat_event()),"event"]
            else:self.completed=[False," ","combat"]
        elif self.type=='c' and self.completed[0]==False:
            self.completed=[True,self.player.open_chest(self.chest),"event"]
        elif self.type=='g' and self.completed[0]==False:
            self.completed=[True,self.player.get_gold(self.chest),"event"]
        elif self.type=="?" and self.completed[0]==False:
            self.completed=[True,self.player.activate_trap(self.trap),"event"]
        elif self.type=="$" and self.completed[0]==False:
            if __name__=="__main__":print(self.shop_event())
            self.completed=[False," ","shop"]
        return self.completed
    def combat_event(self):
        turn=1
        combatlog=[]
        while self.player.is_dead()==False or self.monster.is_dead()==False:
            combatlog.append(self.player.att_target(self.monster))
            if self.monster.is_dead()==True:break
            combatlog.append(self.monster.att_target(self.player))
            if self.player.is_dead()==True:break
            turn+=1
        if self.monster.is_dead():
            combatlog.append(f'Combat Completed in {turn} turns {self.player.name} Wins!\n{self.player.name} gained {self.monster.exp}EXP and {self.monster.gold} Gold\n')
        if self.player.is_dead():
            combatlog.append(f'Combat Completed in {turn} turns {self.player.name} Loses!\nGame Over\n')
        return combatlog
    def shop_event(self):
        command=input('Do you want to (b)uy or (s)ell?\n(q) for quit\n')
        def buy_callback(item_index):
            f = f'Purchase a(n) {self.shop.shop_inventory[item_index]}(y/n)?\nYou have {self.shop.player.gold} Gold.\n'
            command = input(f)
            if command.lower().startswith('y'):
                return True
            if command.lower().startswith('n'):
                return False
            else:
                print("Answer (y/n)")
                buy_callback(int_index)
        def sell_callback(item_index):
            f = f'Sell your {self.shop.player.inventory[item_index]}(y/n)?\nYou will only get 90% of its price.\n'
            command = input(f)
            if command.lower().startswith('y'):
                return True
            if command.lower().startswith('n'):
                return False
            else:
                print("Answer (y/n)")
                sell_callback(int_index)
        if command.startswith('b'):
            print(self.shop.list_shop_inventory())
            command2 = input("Select a number to buy that item:\nBlank to quit.\n")
            if len(str(command2))==0:
                print("Canceled")
                return ""
            try:
                command2 = int(command2)
            except Exception as e:
                print("Please Enter a number")
                return ""
            if buy_callback(command2)==True:
                return self.shop.player_purchase_by_index(command2)
        if command.startswith('s'):
            print(self.shop.player.list_inventory())
            command2 = input("Select a number to sell that item:\nBlank to quit.\n")
            if len(str(command2))==0:
                print("canceled")
                return ""
            try: command2=int(command2)
            except Exception as e:
                print("Please enter a number")
                return""
            if sell_callback(command2)==True:
                return self.shop.player_sell_item(self.shop.player.inventory[command2])
        if not command.lower().startswith('q'):
            self.shop_event()
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        dict = {
            'm': f'\n\tMonster:\n\t{self.monster}\n\t{self.completed}\n',
            'c': f'\n\tChest:\n\t{self.chest}\n\t{self.completed}\n',
            'g': f'\n\tGold:\n\t{self.chest}\n\t{self.completed}\n',
            '?': f'\n\tTrap:\n\t{self.trap}\n\t{self.completed}\n',
            '$': f'\n\tShop:\n\t{self.shop}\n\t{self.completed}\n'
        }    
        return dict.get(self.type,"None found")
    def reprJSON(self):
        return dict(
            type=self.type,
            monster=self.monster,
            shop=self.shop,
            chest=self.chest,
            trap=self.trap,
            completed=self.completed
        )

#with open('./src/levels.json','r') as file:
#        fileread = json.load(file)

files = os.listdir('./src/levels')
files_loaded=[]
for file in files:
    with open(f'./src/levels/{file}','r') as f:
        files_loaded.append(json.load(f))

def randomize_floor(currindex):
    rand = random.randint(0,len(files_loaded)-1)
    while not currindex in files_loaded[rand]['appearsin']:
        rand = random.randint(0,len(files_loaded)-1)
    return rand

def generate_next_level(current_index,player):
    floor =files_loaded[randomize_floor(current_index+1)]
    return copy.deepcopy(Board(floor['floor'],player,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],current_index+1,floor['name']))

def generate_shop(current_index,player):
    for level in files_loaded:
        if level['name']=='Shop':
            floor=level
    return copy.deepcopy(Board(floor['floor'],player,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],current_index+1,floor['name']))

def generate_bonus(current_index,player):
    for level in files_loaded:
        if level['name']=='Bonus Room':
            floor=level
    return copy.deepcopy(Board(floor['floor'],player,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],current_index+1,floor['name']))


'''
def randomize_floor(currindex):
    rand = random.randint(0,len(fileread)-1)
    while not currindex in fileread[rand]['appearsin']:
        rand = random.randint(0,len(fileread)-1)
    return(rand)
    
def generate_levels(start_floor,end_floor,player):
    barr={}
    for i in range(start_floor,end_floor+1):
        floor = fileread[randomize_floor(i)]
        f = copy.deepcopy(Board(floor['floor'],player,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],i))
        barr['floor'+str(i)] = f
    return barr

def generate_next_level(current_index,player):
    floor =fileread[randomize_floor(current_index+1)]
    return copy.deepcopy(Board(floor['floor'],player,floor['available_mobs'],floor['entrance_pos'],floor['exit_pos'],current_index+1))
'''   

def color_coding():
    import time
    #os.system(color xy) where x =bg and y=fg
    for x in (0,1,2,3,4,5,6,7,8,9,'A','B','C','D','E','F'):
        os.system('cls' if os.name=='nt' else 'clear')
        os.system('color '+str(x))
        print("this "+str(x))
        time.sleep(2)

def sav_floor(f:Board):
    sav = json.dumps(f.reprJSON(),cls=complexEncoder,indent=4)
    with open('floorsav.json','w') as f:
        f.writelines(sav)

def sav_floor_arr(fa:dict):
    sav = '{\"player\":'+json.dumps(fa['floor-5'].player_obj,cls=complexEncoder,indent=4)
    sav+=',\n\"floors\":'+json.dumps(fa,cls=complexEncoder,indent=4)+"}"
    with open('gamesav.json','w') as f:
        f.writelines(sav)

def load_floor_arr():
    floor_arr={}
    with open('gamesav.json','r') as f:
        object_arr = json.load(f)
        player = objects.char_from_dict(object_arr['player'])
        for floor_number,object in object_arr['floors'].items():
            print(floor_number,object)
            b = Board(object['floor'],player,object['mob_list'],object['entrance'],object['exit'],object['floor_index'],object['floor_title'])
            b.floor=object['floor']
            b.player_pos[0],b.player_pos[1] = object['player_pos'][0],object['player_pos'][1]
            events = {literal_eval(key):value for key,value in object['events'].items()}
            for key,value in events.items():
                monster_modified = None
                if value['monster'] is not None:
                    monster_modified = copy.deepcopy(objects.MONSTERS_DICT[value['monster']['name']])
                    monster_modified.currhp = value['monster']['currhp']    
                b.events[key] = BoardEvent(player,type=value['type'],shop=value['shop'],chest=value['chest'],monster=monster_modified,trap=value['trap'],completed=value['completed'])
            floor_arr[floor_number]= copy.deepcopy(b) 
    return floor_arr

def load_floor():
    with open('floorsav.json','r') as f:
        object = json.load(f)
        player = objects.char_from_dict(object['player_obj'])
        b = Board(object['floor'],player,object['mob_list'],object['entrance'],object['exit'],object['floor_index'],object['floor_title'])
        b.floor=object['floor']
        b.player_pos[0],b.player_pos[1] = object['player_pos'][0],object['player_pos'][1]
        events = {literal_eval(key):value for key,value in object['events'].items()}
        for key,value in events.items():
            monster_modified = None
            if value['monster'] is not None:
                monster_modified = copy.deepcopy(objects.MONSTERS_DICT[value['monster']['name']])
                monster_modified.currhp = value['monster']['currhp']    
            b.events[key] = BoardEvent(player,type=value['type'],shop=value['shop'],chest=value['chest'],monster=monster_modified,trap=value['trap'],completed=value['completed'])
        return b
        
"""def __init__(self,floorarr,player,mob_list,entrance_pos,exit_pos,floor_index,floor_title):
        self.events={}
        self.player_pos[0],self.player_pos[1]= copy.deepcopy(self.entrance_pos[0]),copy.deepcopy(self.entrance_pos[1])
        #initialize shops with player object reference
        """
 
if __name__=="__main__":
    #os.system('color 2')    
   
    name = input("Enter Name: ")
    p = objects.Player(name,100,100)
    p.get_starter_gear()
    #board = generate_next_level(3,p)
    #sav_floor(board)
    #print(board)
    #load_floor()
    floor_arr={}
    for x in range(-6,1):
        floor_arr[f'floor{x+1}'] = generate_next_level(x,p)
    sav_floor_arr(floor_arr)
    load_floor_arr()
    
    #for x in range(-6,4):
    #    print(generate_next_level(x,p).floor_title, f"Floor {x+1}")
    #print(generate_shop(5,p).floor_title,f"Floor 5")
    
    #for x in range(5,9):
    #    print(generate_next_level(x,p).floor_title, f"Floor {x+1}")
    
    
#    sav = json.dumps(board.__dict__,indent=4)
    
    
    #print(generate_bonus(10,p).floor_title,f"Floor 10")
    #s = fileread[5]
    #board = Board(s['floor'],p,s['available_mobs'],s['entrance_pos'],s['exit_pos'],5)
    #res=None
    #while res==None:
    #    res=board.ask_command()
    #color_coding()
    #boards = generate_levels(1,10,p)
    #for i in range(1,11):
    #    current_floor=boards['floor'+str(i)]
    #    res=None
    #    while res == None :
    #        res = current_floor.ask_command()
    #    for x in boards.values():
    #       x.player_pos=x.entrance_pos   
    
    pass    
    