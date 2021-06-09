##imports
from random import choice, choices, randint
import re, math, copy, json, os
from ast import literal_eval

# http://code.activestate.com/recipes/82965-threads-tkinter-and-asynchronous-io/
# https://www.devdungeon.com/content/colorize-terminal-output-python

char_dict = {
    's': u'\u0000',  # 0  space
    '#': u'\u25a0',  # 1  wall
    'd': u'\u25D8',  # 2  door
    'm': u'\u203C',  # 3  monster
    'g': u'\u00a9',  # 4  gold
    'c': u'\u2302',  # 5  chest
    '?': u'\u0000',  # 6  trap
    '.': u'\uA71C',  # 7  entrance
    '!': u'\uA71B',  # 8  exit
    '*': u'\u2665',  # 9  player
    '$': u'\u263A',  # 10 shop
    '|': u'\u25a0',  # 11 False wall
}

flag = True


## For Serialization of Objects
class complexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


## add reprJSON to all serializable (tagged for save) objects

class Character():  # (name,maxhp,[attack,defence,gold,exp,hitchance])
    def __init__(self, _name, _maxhp, _attack=0, _defence=0, _gold=0, _exp=0, _hitchance=0.7):
        self.name = _name
        self.maxhp = _maxhp
        self.currhp = _maxhp
        self.attack = _attack
        self.defence = _defence
        self.hitchance = _hitchance
        self.exp = _exp
        self.gold = _gold
        self.effects = []

    def att_target(self, target):
        ishit = choices([True, False], (self.hitchance * 100, 100 - (self.hitchance * 100)), k=1)[0]
        if ishit == True:
            total = self.attack - target.defence if not self.attack - target.defence <= 0 else 0
            target.currhp -= total
            if target.is_dead() == False:
                return f'{self.name} attacked {target.name} and dealt {total} damage\n'
            else:
                return f'{self.name} attacked {target.name} for {total} damage and slayed {target.name}\n'
        else:
            return f'{self.name} tried attacking {target.name}, but missed!\n'

    def is_dead(self):
        return self.currhp <= 0

    ##Status Effects on all characters
    def get_status_effect(self, statuseffect):
        self.effects.append(statuseffect)
        return f"{self.name} has gained {statuseffect.name}!\n{statuseffect.__str__()}\n"

    def count_down_status(self, index):
        self.effects[index].remaining_turns -= 1
        if self.effects[index].remaining_turns <= 0:
            self.expired.append(index)

    def expire_status(self):
        expired_messages = []
        if len(self.expired) > 0:
            for i in self.expired:
                expired = self.effects.pop(i)
                expired_messages.append(f"{expired.name} has expired and is no longer affecting {self.name}")
            return expired_messages

    def effect_over_time(self):
        effect_results = []
        self.expired = []
        for i, effect in enumerate(self.effects):
            if effect.type == 'heal':
                if self.currhp < self.maxhp:
                    self.currhp = self.currhp + effect.value if not (
                                                                                self.currhp + effect.value) > self.maxhp else self.maxhp
                    effect_results.append(f"{self.name} healed {effect.value}\n")
                    self.count_down_status(i)
                else:
                    effect_results.append(f"{self.name}'s HP is full\n")
                    self.count_down_status(i)
            if effect.type == 'damage':
                self.currhp -= effect.value
                effect_results.append(f"{self.name} took {effect.value} {effect.type} by {effect.name}\n")
                if self.is_dead() == True:
                    effect_results.append(f"{self.name} succumbed to {effect.name}\n")
                self.count_down_status(i)
        res = self.expire_status()
        if not res == None: effect_results.extend(res)
        self.expired = []
        # print(effect_results)
        return effect_results

    def __str__(self):
        return f"""Name:{self.name}, MaxHP:{str(self.maxhp)}, CurrHP:{str(self.currhp)}, Attack:{str(self.attack)}, Defence:{str(self.defence)}, Experience:{str(self.gold)}, Gold:{str(self.exp)}"""

    def __repr__(self):
        return self.__str__()

    def reprJSON(self):
        return dict(
            name=self.name,
            maxhp=self.maxhp,
            currhp=self.currhp,
            attack=self.attack,
            defence=self.defence,
            hitchance=self.hitchance,
            exp=self.exp,
            gold=self.gold,
            effects=self.effects
        )


class Player(Character):  # (name,maxhp,maxmp,[level,inventory,learnedspells] )------incomplete
    def __init__(self, _name, _maxhp, _maxmana, _attack=5, _defence=5, _gold=0, _exp=0, _level=1, _floor=0,
                 _hitchance=0.5, _inventory=[], _learnedspells=[]):
        super().__init__(_name, _maxhp=_maxhp, _attack=_attack, _defence=_defence, _gold=_gold, _exp=_exp,
                         _hitchance=_hitchance)
        self.level = _level
        self.floor = _floor
        self.maxmp = _maxmana
        self.currmp = self.maxmp
        self.base_hitchance = self.hitchance
        self.equipped = {
            'weapon': None,
            'head': None,
            'chest': None,
            'hands': None,
            'legs': None,
            'feet': None}
        self.inventory = _inventory
        self.equipped_spells = {
            'level:1': None,
            'level:2': None,
            'level:3': None,
            'level:4': None}
        self.learned_spells = _learnedspells

    ### deal/take damage ###
    def att_target(self, target):
        results = super().att_target(target)
        if 'slayed' in results:
            self.gold += target.gold
            self.exp += target.exp
            return results + self.check_levelup()
        else:
            return results

    def cast_spell(self, spellname):  # --------------------------------------------------implement 4
        spell = Spell_book.get_spell(spellname)
        if spell in self.equipped_spells.values():
            if isinstance(spell, Spell):
                if self.currmp >= spell.cost:
                    self.currmp -= spell.cost
                    if spell.spellvalue[0] == 'self':
                        self.currhp = self.currhp + spell.spellvalue[1] if not self.currhp + spell.spellvalue[
                            1] > self.maxhp else self.maxhp
                        return f'{self.name} cast {spell.name} on themselves\nand regained {spell.spellvalue[1]}HP.'
                    elif spell.spellvalue[0] == 'enemy':
                        # attack target and return values?
                        return 'implement this'
                else:
                    return "Not enough MP to cast!"

    def activate_trap(self, trap):
        self.currhp -= trap[1]
        if self.is_dead() == False:
            return f'{self.name} Stepped on a trap!\nActivated a {trap[0]} trap and took {trap[1]} damage'
        else:
            return f'{self.name} Stepped on a trap!\nActivated a {trap[0]} trap and took FATAL damage'

    def check_levelup(self):
        if self.exp >= 100 * self.level:
            self.exp -= 100 * self.level
            self.level += 1
            self.attack += 1
            self.defence += 1
            if self.currhp == self.maxhp:
                self.currhp += 10
            self.maxhp += 10
            return f'{self.name} leveled up!\n{self.name} gained 10 max hp!\n'
        else:
            return ""

    ### item/equipment/spell management ###
    def get_item(self, item):
        self.inventory.append(item)
        return f'Obtained: {item}\n'

    def use_item(self, item):
        if item in self.inventory:
            if isinstance(item, Potion) == True:
                if item.type == 'health':
                    if self.currhp < self.maxhp:
                        self.currhp = self.currhp + item.recovers if not self.currhp + item.recovers > self.maxhp else self.maxhp
                        self.inventory.remove(item)
                        return f"{self.name} used {item.name} and regained {item.recovers} HP.\n"
                    else:
                        return f'Could not use {item.name}, HP is full'
                elif item.type == 'mana':
                    if self.currmp < self.maxmp:
                        self.currmp = self.currmp + item.recovers if not self.currmp + item.recovers > self.maxmp else self.maxmp
                        self.inventory.remove(item)
                        return f"{self.name} used {item.name} and regained {item.recovers} MP.\n"
                    else:
                        return f'Could not use {item.name}, MP is full'
            elif isinstance(item, Equipment):
                return self.equip_item(item)
            elif isinstance(item, Spell_book):
                return self.learn_spell(item)

    def drop_item(self, item):
        if item in self.inventory:
            self.inventory.reverse()
            try:
                self.inventory.remove(item)
            except:
                pass
            self.inventory.reverse()
            return f'Dropped a {item}...'

    def equip_item(self, item):
        if isinstance(item, Equipment) == True:
            if item.slot == 'weapon':
                if not self.equipped['weapon'] == None:
                    self.unequip_by_type(item.slot)
                self.equipped['weapon'] = item
                self.attack += item.bonus[0]
                self.hitchance = item.bonus[1]
                self.inventory.remove(item)
                return f'Equipped: {item.name}.'
            if item.slot in self.equipped.keys() and not item.slot == 'weapon':
                if not self.equipped[item.slot] == None:
                    self.unequip_by_type(item.slot)
                self.equipped[item.slot] = item
                self.defence += item.bonus
                self.inventory.remove(item)
                return f'Equipped: {item.name}.'
        return False

    def unequip_by_item(self, item):
        self.get_item(item)
        if isinstance(item, Equipment) == True:
            if item.slot == 'weapon':
                self.attack -= item.bonus[0]
                self.hitchance = self.base_hitchance
                self.equipped['weapon'] = None
            if item.slot in self.equipped.keys():
                self.defence -= item.bonus
                self.equipped[item.slot] = None
            return f'Unequipped: {item.name}.'

    def unequip_by_type(self, type):
        e = self.equipped[type]
        if type == 'weapon':
            self.attack -= e.bonus[0]
            self.hitchance = self.base_hitchance
        else:
            self.defence -= e.bonus
        self.get_item(e)
        self.equipped[type] = None
        return f'Unequipped: {e.name}.'

    def no_equipment(self):
        for x in self.equipped.values():
            if x != None: return False
        else:
            return True

    def learn_spell(self, spellbook):  # ---------------------------------------------implemented 1
        if Spell_book.get_spell(spellbook.name) not in self.learned_spells:
            self.learned_spells.append(Spell_book.get_spell(spellbook.name))
            self.inventory.remove(spellbook)
            return f'{self.name} Learned {spellbook.name}!\nDon\'t forget to equip the spell.'
        else:
            return f'{self.name} already knows this spell.'

    def equip_spell(self, spell):  # -------------------------------------------------implemented 2
        if isinstance(spell, Spell) == True:
            if not self.equipped_spells[spell.spellslot] == None:
                if self.equipped_spells[spell.spellslot].name == spell.name:
                    return f'{self.name} already has {spell.name} equipped.'
                p = self.unequip_spell_by_slot(spell.spellslot)
            self.equipped_spells[spell.spellslot] = spell
            try:
                return f'{p} and {self.name} Equipped: {spell.name}'
            except:
                return f'{self.name} Equipped: {spell.name}'

    def unequip_spell_by_slot(self, spell_slot):  # ----------------------------------implemented 3
        spell = self.equipped_spells[spell_slot]
        self.equipped_spells[spell_slot] = None
        return f'{self.name} Unequipped: {spell.name}'

    ### get item/equipment/gold ###
    def open_chest(self, found_chest):
        self.inventory.extend(found_chest.items)
        for gold_chance in found_chest.gold:
            self.gold += gold_chance
        e = ", ".join([item.name for item in found_chest.items])
        return f'Opened Chest and found:\n{found_chest.gold} Gold and {e}.'

    def get_gold(self, multiplier=1):
        randgold = randint(15, 30) * multiplier
        self.gold += randgold
        return f'{self.name} Found {randgold} Gold on the floor.'

    def get_starter_gear(self):
        if self.no_equipment() and len(self.inventory) == 0:
            starter = ['Small HP Potion',
                       'Small HP Potion',
                       'Medium HP Potion',
                       'Talk',
                       'Wooden Sword',
                       'Cloth Bandana',
                       'Plain Shirt',
                       'Simple Gloves',
                       'Plain Pants',
                       'Boots']
            for x in starter:
                self.inventory.append(ITEMS_DICT[x])
            self.inventory.reverse()
            for i in range(6):
                self.equip_item(self.inventory[0])
            self.inventory.reverse()
            self.gold += 25

    ### String checking for debugging purposes ###
    def list_equipped(self):
        estr = "\n"
        for x, y in self.equipped.items():
            estr += f'{x}: {y.__str__()}\n'
        return estr[:-3]

    def list_inventory(self):
        # istr="\n"+"\n".join([i.__str__() for i in self.inventory])
        istr = '\n'
        for index, item in enumerate(self.inventory):
            istr += f'[{index}]- {item.__str__()}\n'
        return istr

    def list_equipped_spells(self):  # ----------------------------------------------implemented
        estr = '\n'
        for x, y in self.equipped_spells.items():
            estr += f'{x}, {y.__str__()}\n'
        return estr[:-1]

    def list_spells(self):  # -------------------------------------------------------implemented
        istr = '\n'
        for index, spell in enumerate(self.learned_spells):
            istr += f'[{index}]- {spell.__str__()}'
        return istr

    def __str__(self):
        return f"""Name:{self.name}
Level:{str(self.level)}
MaxHP:{str(self.maxhp)}        
CurrHP:{str(self.currhp)}  
MaxMP:{str(self.maxmp)}        
CurrMP:{str(self.currmp)}        
Attack:{str(self.attack)}      
HitChance:{int(self.hitchance * 100)}%  
Defence:{str(self.defence)}        
Experience:{str(self.exp)}        
Gold:{str(self.gold)}
"""
        ### Saving and Loading Player

    def reprJSON(self):
        return dict(
            name=self.name,
            maxhp=self.maxhp,
            currhp=self.currhp,
            maxmp=self.maxmp,
            currmp=self.currmp,
            attack=self.attack,
            defence=self.defence,
            base_hitchance=self.base_hitchance,
            hitchance=self.hitchance,
            gold=self.gold,
            exp=self.exp,
            effects=self.effects,
            level=self.level,
            floor=self.floor,
            equipped=self.equipped,
            inventory=self.inventory,
            equipped_spells=self.equipped_spells,
            learned_spells=self.learned_spells)


class Item():  # (name,rarity,price)
    def __init__(self, _name, _rarity, _price):
        self.name = _name
        self.rarity = _rarity
        self.price = _price

    def __repr__(self):
        return f'Item({self.name}, {self.rarity}, {self.price})'

    def reprJSON(self):
        return dict(name=self.name, rarity=self.rarity, price=self.price)


class Spell_book(Item):  # (name,rarity,price,spellslot,(target,value),cost )--------incomplete can change
    spells_dict = {}

    def __init__(self, _name, _rarity, _price, _spellslot, _spellval, _castcost):
        super().__init__(_name, _rarity, _price)
        self.spellslot = _spellslot
        self.spellvalue = _spellval
        self.cost = _castcost
        Spell_book.spells_dict[self.name] = Spell(_name, _spellslot, _spellval, _castcost)

    def __repr__(self):
        return f'Spell({self.name}, {self.rarity}, {self.price}, {self.spellslot}, {self.spellvalue}, {self.cost})'

    def reprJSON(self):
        return dict(name=self.name, rarity=self.rarity, price=self.price, spellslot=self.spellslot,
                    spellvalue=self.spellvalue, cost=self.cost)

    @classmethod
    def get_spell(cls, name):
        return cls.spells_dict.get(name)


class Spell():  # (name,spellslot,(target,value),cost)-------------------------------incomplete can change
    def __init__(self, _name, _slot, _spellval, _castcost):
        self.name = _name
        self.spellslot = _slot
        self.spellvalue = _spellval
        self.cost = _castcost

    def __repr__(self):
        return f'{self.name}, Target:{self.spellvalue[0]}, For:{self.spellvalue[1]}HP, Cost:{self.cost}MP\n'

    def reprJSON(self):
        return dict(name=self.name, spellslot=self.spellslot, spellvalue=self.spellvalue, cost=self.cost)


class Effect():  # (name,turns,type,valueOfEff)--------------------------------------incomplete can change
    def __init__(self, turns, name, type, value):
        self.name = name
        self.max_turns = turns
        self.remaining_turns = self.max_turns
        self.type = type
        self.value = value

    def __repr__(self):
        return f'{self.name}, {self.value}{self.type}*{self.max_turns}turns'

    def __str__(self):
        return f'{self.name} does {self.value} {self.type}/turn for {self.max_turns} Turns'

    def reprJSON(self):
        return dict(name=self.name, max_turns=self.max_turns, remaining_turns=self.remaining_turns, type=self.type,
                    value=self.value)


class BoardEffect():  # ()-----------------------------------------------------------incomplete
    def __init__(self, effect):
        self.name = effect.name
        self.remaining_steps = effect.max_turns
        self.type = effect.type
        self.value = effect.value

    def __repr__(self):
        return f'{self.name}, {self.value}{self.type}*{self.max_turns} steps'

    def __str__(self):
        return f'{self.name} does {self.value} {self.type} each step per {self.remaining_steps} steps.'

    def reprJSON(self):
        return dict(name=self.name, remaining_steps=self.remaining_steps, type=self.type, value=self.value)


class Potion(Item):  # (name,rarity,price,type,healsfor)
    def __init__(self, _name, _rarity, _price, _type, _recovers):
        super().__init__(_name, _rarity, _price)
        self.type = _type
        self.recovers = _recovers

    def __repr__(self):
        return f'Potion({self.name}, {self.rarity}, {self.price}, {self.type}, {self.recovers})'

    def reprJSON(self):
        return dict(name=self.name, rarity=self.rarity, price=self.price, type=self.type, recovers=self.recovers)


class Equipment(Item):  # (name,rarity,price,slot, def | (att,hitchance) )
    def __init__(self, _name, _rarity, _price, _slot, _equipbonus):
        super().__init__(_name, _rarity, _price)
        self.slot = _slot
        self.bonus = _equipbonus

    def __repr__(self):
        return f'Equipment({self.name}, {self.rarity}, {self.price}, {self.slot}, {self.bonus})'

    def reprJSON(self):
        return dict(name=self.name, rarity=self.rarity, price=self.price, slot=self.slot, bonus=self.bonus)


class Board():  # (floorarr,player,mob_list,entrance_pos,exit_pos,floor_index)
    # boards_dict={}
    def __init__(self, floorarr, player, mob_list, entrance_pos, exit_pos, floor_index, floor_title):
        self.floor_index = floor_index
        self.mob_list = mob_list
        self.player_obj = player
        self.events = {}
        self.player_pos = [None, None]
        self.exit_pos = exit_pos
        self.entrance_pos = entrance_pos
        self.floor_title = floor_title
        self.floor = self.fill_events(floorarr)  # creates events returns unmodified boardarr
        self.player_pos[0], self.player_pos[1] = copy.deepcopy(self.entrance_pos[0]), copy.deepcopy(
            self.entrance_pos[1])
        # initialize shops with player object reference
        for shop in SHOP_DICT.values():
            shop.player = self.player_obj
        # Board.boards_dict['floor'+str(floor_index)]=self

    def fill_events(self, floorarr):
        for i in range(len(floorarr)):
            for j in range(len(floorarr[i])):
                if floorarr[i][j] in ('m', 'c', 'g', '?', '$'):
                    self.create_event(floorarr[i][j], (i, j))
        return floorarr

    def create_event(self, type, coordinate):
        if type == 'm':
            pool = []
            for m in self.mob_list:
                pool.append(MONSTERS_DICT[m])
            if len(pool) > 1:
                m = copy.deepcopy(pool[randint(0, len(pool) - 1)])
            else:
                m = copy.deepcopy(pool[0])
            newEvent = BoardEvent(player=self.player_obj, type=type, monster=m)
            self.events[coordinate] = copy.deepcopy(newEvent)
        elif type == 'c':
            if self.floor_index == 1:
                bonus = 1
            else:
                bonus = 0
            c = Chest(max_rarity=choice([self.floor_index, self.floor_index - 1 + bonus]), num_rolls=randint(1, 3))
            newEvent = BoardEvent(player=self.player_obj, type=type, chest=c)
            self.events[coordinate] = copy.deepcopy(newEvent)
        elif type == 'g':
            newEvent = BoardEvent(player=self.player_obj, type=type, chest=self.floor_index + 1)
            self.events[coordinate] = copy.deepcopy(newEvent)
        elif type == "?":
            newEvent = BoardEvent(player=self.player_obj, type=type,
                                  trap=choices(list(TRAPS.items()), weights=(40, 30, 20, 10), k=1)[0])
            self.events[coordinate] = copy.deepcopy(newEvent)
        elif type == "$":
            if flag:
                s = Shop(self.player_obj, ["Small HP Potion", "Medium HP Potion", "Small MP Potion"])
                newEvent = BoardEvent(player=self.player_obj, type=type, shop=s)
            else:
                newEvent = BoardEvent(player=self.player_obj, type=type,
                                      shop=SHOP_DICT['floor' + str(self.floor_index)])
            self.events[coordinate] = newEvent

    def move_character(self, direction):
        directions = {'w': [-1, 0], 's': [1, 0], 'a': [0, -1], 'd': [0, 1]}
        newpos = (self.player_pos[0] + directions[direction][0], self.player_pos[1] + directions[direction][1])
        result = ["", "", ""]

        if list(newpos) == self.exit_pos:
            self.player_pos[0], self.player_pos[1] = copy.deepcopy(self.entrance_pos[0]), copy.deepcopy(
                self.entrance_pos[1])
            return [True, 'Going Up.', 'floor']
        elif list(newpos) == self.entrance_pos:
            self.player_pos[0], self.player_pos[1] = copy.deepcopy(self.exit_pos[0]), copy.deepcopy(self.exit_pos[1])
            return [True, 'Going Down.', 'floor']
        elif newpos in self.events:
            if self.events[newpos].completed[0] == False:
                result = self.events[newpos].complete_event()
                if self.player_obj.is_dead(): return [False, 'You Lose\nGame Over.\n', 'gameover']
                if result[0] != False:
                    self.player_pos[0] = newpos[0]
                    self.player_pos[1] = newpos[1]
            if self.events[newpos].completed[0] == True:
                self.player_pos[0] = newpos[0]
                self.player_pos[1] = newpos[1]
        else:
            if not self.floor[newpos[0]][newpos[1]] in ('#'):
                self.player_pos[0] = newpos[0]
                self.player_pos[1] = newpos[1]
        return result

    ### Save and Load
    def convert_event_keys(self):
        converted_events = {}
        for key, value in self.events.items():
            converted_events[str(key)] = value
        return converted_events

    def reprJSON(self):
        return dict(
            # player_obj=self.player_obj,
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
        # os.system('cls' if os.name=='nt' else 'clear')
        # os.system('cls||clear')
        os.system('color 2' if os.name == 'nt' else '')
        for x in range(len(self.floor)):
            for y in range(len(self.floor[x])):
                if self.player_pos[0] == x and self.player_pos[1] == y:
                    print(char_dict['*'], end=" ")
                else:
                    if (x, y) in self.events:
                        if self.events[(x, y)].completed[0] == True:
                            print(" ", end=" ")
                        else:
                            print(char_dict[self.floor[x][y]], end=" ")
                    else:
                        print(char_dict[self.floor[x][y]], end=" ")
            print()

    def ask_command(self):
        print("Floor " + str(self.floor_index))
        self.show_floor_fancy()
        command = input("Enter a desired command (Move, char): ")
        res = ["", '', '']
        if command.lower().startswith('m'):
            dir = ""
            if len(command.split()) == 2:
                dir = command.split()[1][0]
            else:
                dir = input("Enter a direction: ")[0]
                while dir not in ('a', 'w', 'd', 's'):
                    dir = input("Enter a direction: ")
            res = self.move_character(dir)
            if res[2] != "floor":
                print(res[1])
        if command.lower().startswith('c') or command.lower().startswith('p'):
            print(self.player_obj)
        if command.lower() != 'exit' and command.lower().startswith('e'):
            print(self.player_obj.list_equipped() + '\n')
            print(self.equipment_commands())
        if command.lower().startswith('i'):
            print(self.player_obj.list_inventory() + '\n')
            print(self.inventory_commands())
        if command.lower().startswith('b'):
            self.show_floor_regular()
        if command.lower().startswith('q'):
            print('\n'.join([event.__repr__() for event in self.events.values()]))

        input('...')

        if res[2] == 'floor':
            os.system('cls' if os.name == 'nt' else 'clear')
            return res[0]

        os.system('cls' if os.name == 'nt' else 'clear')

    def equipment_commands(self):
        def conf_callback(type):
            command = input("Unequip " + type + "? (y/n): ")
            if command.lower().startswith('y'):
                return True
            elif command.lower().startswith('n'):
                return False
            else:
                print("Answer (y/n)")
                conf_callback(type)

        command = input("Select Item to unequip, blank for none(helmet,chest,gloves,pants,shoes,weapon): ")
        if len(command) == 0:
            print("Canceled")
            return ""
        if command.lower().startswith('h'):
            if conf_callback('helmet') == True: return self.player_obj.unequip_by_type('helmet')
        if command.lower().startswith('c'):
            if conf_callback('chest') == True: return self.player_obj.unequip_by_type('chest')
        if command.lower().startswith('g'):
            if conf_callback('gloves') == True: return self.player_obj.unequip_by_type('gloves')
        if command.lower().startswith('p'):
            if conf_callback('pants') == True: return self.player_obj.unequip_by_type('pants')
        if command.lower().startswith('s'):
            if conf_callback('shoes') == True: return self.player_obj.unequip_by_type('shoes')
        if command.lower().startswith('w'):
            if conf_callback('weapon') == True: return self.player_obj.unequip_by_type('weapon')

    def inventory_commands(self):
        def conf_callback(item_index):
            item = self.player_obj.inventory[item_index]
            f = 'Use' if isinstance(item, objects.Potion) else 'Equip'
            f += f' {item.name}? (y/n)'
            command = input(f)
            if command.lower().startswith('y'):
                return True
            elif command.lower().startswith('n'):
                return False
            else:
                print("Answer (y/n)")
                conf_callback(item_index)

        command = input("select an item number to use/equip or blank to exit: ")
        if len(str(command)) == 0:
            print('canceled')
            return ""
        try:
            command = int(command)
        except Exception as e:
            print('please enter a number.')
            return ""
        if conf_callback(command) == True: return self.player_obj.use_item(self.player_obj.inventory[command])

    def __str__(self):
        return (f'Floor: {self.floor_index},\n{self.mob_list},\n{self.player_pos},\n{self.exit_pos},\n{self.events}')


class BoardEvent():  # player,type,[shop|chest|monster|trap]
    def __init__(self, player, type, shop=None, chest=None, monster=None, trap=None, completed=[False, "", "event"]):
        self.player = player
        self.type = type
        self.monster = monster
        self.shop = shop
        self.chest = chest
        self.trap = trap
        self.completed = completed

    def complete_event(self):
        if self.type == 'm' and self.completed[0] == False:
            if __name__ == '__main__':
                self.completed = [True, ''.join(self.combat_event()), "event"]
            else:
                self.completed = [False, " ", "combat"]
        elif self.type == 'c' and self.completed[0] == False:
            self.completed = [True, self.player.open_chest(self.chest), "event"]
        elif self.type == 'g' and self.completed[0] == False:
            self.completed = [True, self.player.get_gold(self.chest), "event"]
        elif self.type == "?" and self.completed[0] == False:
            self.completed = [True, self.player.activate_trap(self.trap), "event"]
        elif self.type == "$" and self.completed[0] == False:
            if __name__ == "__main__": print(self.shop_event())
            self.completed = [False, " ", "shop"]
        return self.completed

    def combat_event(self):
        turn = 1
        combatlog = []
        while self.player.is_dead() == False or self.monster.is_dead() == False:
            combatlog.append(self.player.att_target(self.monster))
            if self.monster.is_dead() == True: break
            combatlog.append(self.monster.att_target(self.player))
            if self.player.is_dead() == True: break
            turn += 1
        if self.monster.is_dead():
            combatlog.append(
                f'Combat Completed in {turn} turns {self.player.name} Wins!\n{self.player.name} gained {self.monster.exp}EXP and {self.monster.gold} Gold\n')
        if self.player.is_dead():
            combatlog.append(f'Combat Completed in {turn} turns {self.player.name} Loses!\nGame Over\n')
        return combatlog

    def shop_event(self):
        command = input('Do you want to (b)uy or (s)ell?\n(q) for quit\n')

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
            if len(str(command2)) == 0:
                print("Canceled")
                return ""
            try:
                command2 = int(command2)
            except Exception as e:
                print("Please Enter a number")
                return ""
            if buy_callback(command2) == True:
                return self.shop.player_purchase_by_index(command2)
        if command.startswith('s'):
            print(self.shop.player.list_inventory())
            command2 = input("Select a number to sell that item:\nBlank to quit.\n")
            if len(str(command2)) == 0:
                print("canceled")
                return ""
            try:
                command2 = int(command2)
            except Exception as e:
                print("Please enter a number")
                return ""
            if sell_callback(command2) == True:
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
        return dict.get(self.type, "None found")

    def reprJSON(self):
        return dict(
            type=self.type,
            monster=self.monster,
            shop=self.shop,
            chest=self.chest,
            trap=self.trap,
            completed=self.completed
        )


class Chest():  # (max_rarity,num_rolls,[predetermined_items,predetermined_gold])
    def __init__(self, max_rarity, num_rolls, predetermined_items=None, predetermined_gold=None):
        self.items = predetermined_items
        self.gold = predetermined_gold
        if self.gold == None:
            self.gold = [self.generate_random_gold()]
        if self.items == None:
            self.items = []
            for x in range(num_rolls):
                self.generate_random_item(max_rarity)

    def generate_random_item(self, max_rarity):
        if max_rarity < 0:
            self.gold.append(0)
            return
        item_type = choices(['usable', 'armor', 'weapon', 'extgold'], weights=(33, 30, 30, 7), k=1)[0]
        # potions   33%
        if item_type == 'usable':
            pool = []
            for item in ITEMS_DICT.values():
                if item.rarity <= max_rarity and item.rarity > -1 and isinstance(item, Potion):
                    pool.append(item)
            self.items.append(choice(pool))
        # armor     30%
        if item_type == 'armor':
            armor = choice(['head', "chest", 'hands', 'legs', 'feet'])
            pool = []
            for item in ITEMS_DICT.values():
                boosted_rarity = choices((max_rarity, max_rarity + 1), weights=(80, 20))[0]
                if not item in self.items:
                    if isinstance(item,
                                  Equipment) and item.rarity <= boosted_rarity and item.rarity > -1 and item.slot != 'weapon':
                        pool.append(item)
            if len(pool) == 0:
                self.generate_random_item(max_rarity)
            else:
                self.items.append(choice(pool))
        # weapon    30%
        if item_type == 'weapon':
            pool = []
            for item in ITEMS_DICT.values():
                boosted_rarity = choices((max_rarity, max_rarity + 1), weights=(80, 20))[0]
                if not item in self.items:
                    if isinstance(item,
                                  Equipment) and item.rarity <= boosted_rarity and item.rarity > -1 and item.slot == 'weapon':
                        pool.append(item)
            if len(pool) == 0:
                self.generate_random_item(max_rarity)
            else:
                self.items.append(choice(pool))
        # more gold 7%
        if item_type == 'extgold':
            self.gold.append(self.generate_random_gold())

    def generate_random_gold(self):
        ranges = [randint(25, 50), randint(50, 75), randint(75, 100), randint(100, 125)]
        return choices(ranges, weights=(20, 50, 35, 5), k=1)[0]

    def __str__(self):
        i = '\n'.join([item.name for item in self.items])
        g = ','.join(str(ga) for ga in self.gold)
        return f'Gold:{g}\nItems:\n{i}'

    def reprJSON(self):
        return dict(items=self.items, gold=self.gold)


class Shop():  # (player,shop_inventory)
    def __init__(self, player, shop_inventory):
        self.player = player
        self.shop_inventory = shop_inventory

    def player_purchase_by_index(self, index):
        return (self.player_purchase_item(self.shop_inventory[index]))

    def player_purchase_item(self, item):
        if self.player.gold >= item.price:
            self.player.gold -= item.price
            self.player.get_item(item)
            self.shop_inventory.remove(item)
            return f'You Purchased a(n) {item.name} for {item.price} Gold\n'
        else:
            return f'You do not have enough gold to buy {item.name}\n'

    def player_sell_item(self, item):
        self.player.gold += math.ceil(item.price * 0.9)
        self.player.drop_item(item)
        self.shop_inventory.append(item)
        return f'{self.player.name} Sold a(n) {item.name} to the store and recieved {math.ceil(item.price * 0.9)} Gold\n'

    def list_shop_inventory(self):
        istr = '\n'
        for index, item in enumerate(self.shop_inventory):
            istr += f'[{str(index) + "]":3} - {item.__str__():70} - {item.price:3} Gold\n'
        return istr

    def __str__(self):
        return f'Shop:{self.list_shop_inventory()}'

    def reprJSON(self):
        return dict(shop_inventory=self.shop_inventory)


class Quest():  # (questgiver,questdesc,(questtarget,questquantity))-----------------incomplete, planned addition
    def __init__(self, qgiver, qdesc, qrequirements):
        pass


def load_json():
    e_dict = {}
    i_dict = {}
    s_dict = {}
    f_arr = []

    with open('./src/entities.json', 'r') as f:
        for object in json.load(f):
            # ref = [x for x in object.values()]
            # print(f'{ref[1]},{ref[2]},{ref[3]},{ref[4]},{ref[5]},{ref[6]},{ref[7]}')
            if object['type'] == 'enemy':
                # enemy.append(Character(ref[1],ref[2],ref[3],ref[4],ref[5],ref[6],ref[7]))
                e_dict[object['name']] = Character(object['name'], object['maxhp'], object['attack'], object['defence'],
                                                   object['gold'], object['exp'], object['hitchance'])
            elif object['type'] == 'usable':
                # items.append(Potion(ref[1],ref[2],ref[3],ref[4],ref[5]) )
                i_dict[object['name']] = Potion(object['name'], object['rarity'], object['price'], object['recovers'],
                                                object['recoverval'])
            elif object['type'] == 'equipment':
                if object['slot'] in ('head', 'chest', 'hands', 'legs', 'feet'):
                    i_dict[object['name']] = Equipment(object['name'], object['rarity'], object['price'],
                                                       object['slot'], object['defence'])
                if object['slot'] == 'weapon':
                    i_dict[object['name']] = Equipment(object['name'], object['rarity'], object['price'],
                                                       object['slot'], (object['attack'], object['hitchance']))
            elif object['type'] == 'spell_book':
                i_dict[object['name']] = Spell_book(object['name'], object['rarity'], object['price'],
                                                    object['spellslot'], (object['target'], object['value']),
                                                    object['manacost'])
    with open('./src/shops.json', 'r') as f:
        shop_list = json.load(f)
        for shop in shop_list:
            items = []
            for item, quantity in shop['shopinventory'].items():
                items.extend([i_dict[item] for x in range(quantity)])
            s_dict['floor' + str(shop['floor'])] = Shop(None, items)
    files = os.listdir('./src/levels')
    for file in files:
        with open(f'./src/levels/{file}', 'r') as f:
            f_arr.append(json.load(f))

    return e_dict, i_dict, s_dict, f_arr


MONSTERS_DICT, ITEMS_DICT, SHOP_DICT, FLOORS_LIST = load_json()
TRAPS = {'Flame': 10, 'Arrow': 15, 'Pitfall': 25, 'Boulder': 50}


### Generate new floor
def randomize_floor(currindex):
    rand = randint(0, len(FLOORS_LIST) - 1)
    while not currindex in FLOORS_LIST[rand]['appearsin']:
        rand = randint(0, len(FLOORS_LIST) - 1)
    return rand


def generate_next_level(current_index, player):
    floor = FLOORS_LIST[randomize_floor(current_index + 1)]
    return copy.deepcopy(
        Board(floor['floor'], player, floor['available_mobs'], floor['entrance_pos'], floor['exit_pos'],
              current_index + 1, floor['name']))


def generate_shop(current_index, player):
    for level in FLOORS_LIST:
        if level['name'] == 'Shop':
            floor = level
    return copy.deepcopy(
        Board(floor['floor'], player, floor['available_mobs'], floor['entrance_pos'], floor['exit_pos'],
              current_index + 1, floor['name']))


def generate_bonus(current_index, player):
    for level in FLOORS_LIST:
        if level['name'] == 'Bonus Room':
            floor = level
    return copy.deepcopy(
        Board(floor['floor'], player, floor['available_mobs'], floor['entrance_pos'], floor['exit_pos'],
              current_index + 1, floor['name']))


### Save Game
def save_game(floor_dict: dict):
    save = '{\n"player":\n' + json.dumps(list(floor_dict.values())[-1].player_obj, cls=complexEncoder, indent=4)
    save += ',\n"floors":\n' + json.dumps(floor_dict, cls=complexEncoder, indent=4) + '\n}'
    with open(f'{list(floor_dict.values())[-1].player_obj.name}_sav.json', 'w') as savefile:
        savefile.writelines(save)


### Load Game
def load_char_from_dict(object: dict):
    p = Player(object['name'], object['maxhp'], object['maxmp'], object['attack'], object['defence'], object['gold'],
               object['exp'], object['level'], object['floor'], object['hitchance'])
    p.base_hitchance = object['base_hitchance']
    for item in object['inventory']:
        p.inventory.append(ITEMS_DICT[item['name']])
    for spell in object['learned_spells']:
        p.learned_spells.append(Spell_book.get_spell(spell['name']))
    for equip in object['equipped'].values():
        p.equipped[equip['slot']] = ITEMS_DICT[equip['name']]
    for equip in object['equipped_spells'].values():
        if equip is not None:
            p.equipped_spells[equip['spellslot']] = Spell_book.get_spell(equip['name'])
    for effect in object['effects']:
        e = Effect(effect['max_turns'], effect['name'], effect['type'], effect['value'])
        e.remaining_turns = effect['remaining_turns']
        p.effects.append(e)
    return p


def load_game(filename):
    floor_arr = {}
    with open(filename, 'r') as loadfile:
        object_arr = json.load(loadfile)
        player = load_char_from_dict(object_arr['player'])
        for floor_number, object in object_arr['floors'].items():
            b = Board(object['floor'], player, object['mob_list'], object['entrance'], object['exit'],
                      object['floor_index'], object['floor_title'])
            b.floor = object['floor']
            b.player_pos[0], b.player_pos[1] = object['player_pos'][0], object['player_pos'][1]
            events = {literal_eval(key): value for key, value in object['events'].items()}
            for key, value in events.items():
                monster_modified = None
                if value['monster'] is not None:
                    monster_modified = copy.deepcopy(MONSTERS_DICT[value['monster']['name']])
                    monster_modified.currhp = value['monster']['currhp']
                b.events[key] = BoardEvent(player, type=value['type'], shop=value['shop'], chest=value['chest'],
                                           monster=monster_modified, trap=value['trap'], completed=value['completed'])
            floor_arr[floor_number] = copy.deepcopy(b)
    return floor_arr


### testing
def color_coding():
    import time
    # os.system(color xy) where x =bg and y=fg
    for x in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'A', 'B', 'C', 'D', 'E', 'F'):
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('color ' + str(x))
        print("this " + str(x))
        time.sleep(2)


class combat():  ### uses DOT and HOT, Implement in window_design.py
    def __init__(self, monster, player):
        self.monster = monster
        self.player = player
        self.turns = 0
        self.turn_order = []
        self.combat_log = []
        self.complete = False

    def determine_turn_order(self):
        if self.turns == 0:
            # self.start_button.configure(text="Fight")
            # self.start_button.configure(height=2)
            first = choices((self.monster, self.player), weights=[40, 60])[0]
            self.turn_order.append(first)
            if first == self.monster:
                self.turn_order.append(self.player)
            else:
                self.turn_order.append(self.monster)
            self.combat_log.append(f'{first.name} Strikes First!\n')

    def advance_turn(self):
        # print(self.turn_order[self.turns%2].name+'\'s attacks '+self.turn_order[(self.turns+1)%2].name)
        self.combat_log.append(self.turn_order[self.turns % 2].att_target(self.turn_order[(self.turns + 1) % 2]))
        self.combat_log.extend(self.turn_order[self.turns % 2].effect_over_time())

        self.turns += 1
        # return self.check_win(self.turn_order[(self.turns+1)%2])

    def check_win(self, target):
        if target.is_dead():
            if self.monster.is_dead():
                self.combat_log.append(
                    f"Combat Completed in {self.turns} turns\n{self.player.name} wins!\n{self.player.name} gained {self.monster.exp}EXP and {self.monster.gold} Gold\n")

            elif self.player.is_dead():
                self.combat_log.append(f'Combat Completed in {self.turn} turns {self.player.name} loses!\nGame Over\n')
            return True
            # self.message.config(text=self.combat_log[-1])
            # self.b_frame.pack_forget()
            # HoverButton(self.lowerframe,text='Combat Complete',activebackground='green',activeforeground='white',command=lambda e=self.player.is_dead():self.complete(e)).pack(fill=tk.BOTH,expand=1)
        return False

    def ask_move(self):
        choice = input("Choose An Option\nFight(f)\nItem(i)\nSpell(s)\nRun(r)\n")
        if choice.lower().startswith('i'):
            self.combat_log.append(self.ask_item())
            self.advance_turn()
        if choice.lower().startswith('s'):
            self.ask_spell()
            self.advance_turn()
        if choice.lower().startswith('f'):
            self.advance_turn()
        return self.check_win(self.turn_order[(self.turns + 1) % 2])

    def ask_spell(self):
        print(self.player.list_equipped_spells() + '\n')

    def ask_item(self):
        print(self.player.list_inventory() + "\n")

        def conf_callback(item_index):
            item = self.player.inventory[item_index]
            f = 'Use' if isinstance(item, Potion) else 'Equip'
            f += f' {item.name}? (y/n)'
            command = input(f)
            if command.lower().startswith('y'):
                return True
            elif command.lower().startswith('n'):
                return False
            else:
                print("Answer (y/n)")
                conf_callback(item_index)

        command = input("select an item number to use/equip or blank to exit: ")
        if len(str(command)) == 0:
            print('canceled')
            return ""
        try:
            command = int(command)
        except Exception as e:
            print('please enter a number.')
            return ""
        if conf_callback(command) == True:
            self.turns += 1

            return self.player.use_item(self.player.inventory[command])


'''
def combat(e1,e2):
    turn=1
    combatlog=[]
    while e1.is_dead()==False or e2.is_dead()==False:
        combatlog.append(e1.att_target(e2))
        if e2.is_dead()==True:break
        combatlog.append(e2.att_target(e1))
        if e1.is_dead()==True:break
        turn+=1
    if e2.is_dead():
        combatlog.append(f'Combat Completed in {turn} turns {e1.name} Wins!\n{e1.name} gained {e2.exp}EXP and {e2.gold} Gold\n')
    if e1.is_dead():
        combatlog.append(f'Combat Completed in {turn} turns {e1.name} Loses!\nGame Over\n')
    return combatlog
 '''


def shop_commands(s):
    command = input('Do you want to (b)uy or (s)ell?\n')

    def buy_callback(item_index):
        f = f'Purchase a(n) {s.shop_inventory[item_index]}(y/n)?\nYou have {s.player.gold} Gold.\n'
        command = input(f)
        if command.lower().startswith('y'):
            return True
        if command.lower().startswith('n'):
            return False
        else:
            print("Answer (y/n)")
            buy_callback(int_index)

    def sell_callback(item_index):
        f = f'Sell your {s.player.inventory[item_index]}(y/n)?\nYou will only get 90% of its price.\n'
        command = input(f)
        if command.lower().startswith('y'):
            return True
        if command.lower().startswith('n'):
            return False
        else:
            print("Answer (y/n)")
            sell_callback(int_index)

    if command.startswith('b'):
        print(s.list_shop_inventory())
        command2 = input("Select a number to buy that item:\nBlank to quit.\n")
        if len(str(command2)) == 0:
            print("Canceled")
            return ""
        try:
            command2 = int(command2)
        except Exception as e:
            print("Please Enter a number")
            return ""
        if buy_callback(command2) == True:
            return s.player_purchase_by_index(command2)
    if command.startswith('s'):
        print(s.player.list_inventory())
        command2 = input("Select a number to sell that item:\nBlank to quit.\n")
        if len(str(command2)) == 0:
            print("canceled")
            return ""
        try:
            command2 = int(command2)
        except Exception as e:
            print("Please enter a number")
            return ""
        if sell_callback(command2) == True:
            return s.player_sell_item(s.player.inventory[command2])


if __name__ == '__main__':
    # import copy
    p = Player('james', 100, 100)
    p.get_starter_gear()
    p.get_item(ITEMS_DICT['Light Fire'])
    p.learn_spell(ITEMS_DICT['Light Fire'])
    p.equip_spell(p.learned_spells[0])
    c = Chest(0, 2)
    e = Effect(4, 'poison', 'damage', 5)
    e2 = Effect(2, 'fire', 'damage', 10)
    e3 = Effect(3, 'polish', 'heal', 10)
    # p.get_status_effect(e)
    '''
    com = combat(copy.deepcopy(MONSTERS_DICT['Slime']),p)
    com.determine_turn_order()
    res = com.ask_move()

    while res ==False:
        res = com.ask_move() 
    for e in com.combat_log:
        print(e)
        '''
    floor_arr = {}
    for x in range(-6, 1):
        floor_arr[f'floor{x + 1}'] = generate_next_level(x, p)
    #save_game(floor_arr)

    arr = load_game(p.name + '_sav.json')
    print(arr)
    
    '''
    p.exp+=100
    p.check_levelup()

    print(p)
    print(p.open_chest(c))
    print(p.get_item(ITEMS_DICT['Light Heal']))
    print(p.get_item(ITEMS_DICT['Light Fire']))
    print(p.use_item(ITEMS_DICT['Light Heal']))
    print(p.use_item(ITEMS_DICT['Light Fire']))
    print(p.equip_spell(p.learned_spells[0]))
    #print(p.equip_spell(p.learned_spells[1]))
    p.currhp=1
    print(p.currhp)
    print(p.cast_spell('Light Heal'))
    print(p.currhp)
    print(p.cast_spell('Light Heal'))
    print(p.currhp)
    print(p.cast_spell('Light Heal'))
    print(p.currhp)
    print(p.cast_spell('Light Heal'))
    print(p.currhp)
    print(p.cast_spell('Light Heal'))
    print(p.currhp)
    print(p.currmp)'''

