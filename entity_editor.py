import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import json
import os
from functools import partial

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

class SortSearchTreeview(ttk.Treeview):
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

class Editor(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.pack(fill=tk.BOTH,expand=1)
        if os.name=='nt':
                self.master.geometry('750x250')
        else:
                self.master.geometry('1000x250')
        self.panels = ttk.Notebook(self)
        HoverButton(self.panels,text='Save All',command=self.save_all,activebackground='lightblue').place(x=695,y=0)
        
        self.ENTITIES=[]
        try:
            with open('./src/entities.json','r') as f:
                for object in json.load(f):
                    self.ENTITIES.append(object)
        except:
            pass
        
        
        self.create_iframe()
        self.create_sframe()
        self.create_mframe()
        self.panels.pack(fill=tk.BOTH,expand=1)
   
    def create_mframe(self):
        self.mframe = tk.Frame(self.panels)
        self.panels.add(self.mframe,text='Monsters')
        form = tk.Frame(self.mframe)
        form.pack(side=tk.TOP,fill=tk.BOTH,expand=1)
        
        tk.Label(form,text="Enemy Name:",anchor='w').grid(row=0,column=0,sticky='w')
        self.m_name_input=tk.Entry(form)
        self.m_name_input.grid(row=0,column=1,sticky='we',columnspan=3)
        
        tk.Label(form,text="Max HP:",anchor='e').grid(row=1,column=0,sticky='w')
        self.m_maxhp = ttk.Spinbox(form,from_=0,to=1000,width=24,format="%.0f HP")
        self.m_maxhp.set(f"{0:0.0f} HP")
        self.m_maxhp.grid(row=1,column=1,sticky='w',columnspan=3)
        
        tk.Label(form,text="Attack:",anchor='e').grid(row=2,column=0,sticky='w')
        self.m_attack = ttk.Spinbox(form,from_=0,to=1000,width=8,format='%.0f Att')
        self.m_attack.set(f"{0:0.0f} Att")
        self.m_attack.grid(row=2,column=1,sticky='w')
        
        tk.Label(form,text="Hit%:",anchor='e').grid(row=2,column=2,sticky='w')
        self.m_hitchance = ttk.Spinbox(form,from_=0,to=100,increment=5,width=7,format="%.0f%%")
        self.m_hitchance.set(f'{0:4.0f}%')
        self.m_hitchance.grid(row=2,column=3,sticky='w')
        
        tk.Label(form,text="Defence:",anchor='w').grid(row=3,column=0,sticky='w')
        self.m_defence = ttk.Spinbox(form,from_=0,to=1000,width=24,format="%.0f Def")
        self.m_defence.set(f'{0:0.0f} Def')
        self.m_defence.grid(row=3,column=1,sticky='w',columnspan=3)

        tk.Label(form,text="Gold:",anchor='w').grid(row=4,column=0,sticky='w')
        self.m_gold = ttk.Spinbox(form,from_=0,to=1000,width=8,format="%.0f Gol")
        self.m_gold.set(f'{0:0.0f} Gol')
        self.m_gold.grid(row=4,column=1,sticky='w',columnspan=3)
        
        tk.Label(form,text="Exp:",anchor='w').grid(row=4,column=2,sticky='w')
        self.m_exp = ttk.Spinbox(form,from_=0,to=1000,width=7,format='%.0f Exp')
        self.m_exp.set(f'{0:0.0f} Exp')
        self.m_exp.grid(row=4,column=3,sticky='w')
        
        def add_new():
            temp = {
                'type':'enemy',
                'name':self.m_name_input.get().strip(),
                'maxhp':int(self.m_maxhp.get().split(' ')[0]),
                'attack':int(self.m_attack.get().split(" ")[0]),
                'defence':int(self.m_defence.get().split(" ")[0]),
                'gold':int(self.m_gold.get().split(" ")[0]),
                'exp':int(self.m_exp.get().split(" ")[0]),
                'hitchance':int(self.m_hitchance.get().split("%")[0])/100}
            for e in temp.values():
                if e=='' or e==0:
                    print('empty monster')
                    return
            for e in self.ENTITIES:
                if temp['name'] == e['name']:
                    print('Monster with name exists')
                    return
            self.ENTITIES.append(temp)
            self.clear_m_details()
            self.load_monsters()
        def save_edited():
            for x in self.ENTITIES:
                if x['name'] == self.m_list.item(self.m_id,'text'):
                    x['name']=self.m_name_input.get().strip()
                    x['maxhp']=int(self.m_maxhp.get().split(' ')[0])
                    x['attack']=int(self.m_attack.get().split(' ')[0])
                    x['defence']=int(self.m_defence.get().split(' ')[0])
                    x['gold']=int(self.m_gold.get().split(' ')[0])
                    x['exp']=int(self.m_exp.get().split(' ')[0])
                    x['hitchance']=int(self.m_hitchance.get().split("%")[0])/100
                    self.clear_m_details()
                    self.load_monsters()
                    return
        def delete_selected():
            vals = self.m_list.item(self.m_id,'values')
            temp = {
                'type':'enemy',
                'name':self.m_list.item(self.m_id,'text'),
                'maxhp':int(vals[0]),
                'attack':int(vals[1]),
                'defence':int(vals[3]),
                'gold':int(vals[4]),
                'exp':int(vals[5]),
                'hitchance':int(vals[2])/100}
            self.ENTITIES.remove(temp)
            self.clear_m_details()
            self.load_monsters()
            
        self.new_m_button= tk.Button(form,text='Add Enemy',width=10,command=add_new)
        self.new_m_button.grid(row=0,column=4,sticky='we')
        self.edit_m_button= tk.Button(form,text='Edit Enemy',width=10,state='disabled',command=save_edited)
        self.edit_m_button.grid(row=0,column=5,sticky='we')
        self.delete_m_button= tk.Button(form,text='Delete Enemy',width=10,state='disabled',command=delete_selected)
        self.delete_m_button.grid(row=0,column=6,sticky='we')
        self.cancel_m_button= tk.Button(form,text='Cancel',width=10,state='disabled',command=self.clear_m_details)
        self.cancel_m_button.grid(row=0,column=7,sticky='we')

        self.create_m_treeview()
        
    def create_iframe(self):
        def option_changed(event):
            self.item_val_label.config(text=words[self.i_type.get()])
            
            
            try:
                self.hc_label.grid_forget()
                self.i_hitchance.grid_forget()
                self.as_label.grid_forget()
                self.i_armor_slot.grid_forget()        
                self.ht_label.grid_forget()
                self.i_heal_type.grid_forget()
            except:
                pass
            
            if self.i_type.get()=='Weapon':
                self.hc_label.grid(row=3,column=0,sticky='we')
                self.i_hitchance.grid(row=3,column=1,sticky='w')
                self.item_val.config(format="%.0f Att")
                self.item_val.set(f'{0:0.0f} Att')           
            elif self.i_type.get()=='Armor':
                self.as_label.grid(row=3,column=0,sticky='we')
                self.i_armor_slot.grid(row=3,column=1,sticky='we')
                self.item_val.config(format="%.0f Def")
                self.item_val.set(f'{0:0.0f} Def') 
            elif self.i_type.get()=="Potion":
                self.ht_label.grid(row=3,column=0,sticky='we')
                self.i_heal_type.grid(row=3,column=1,sticky='we')
                self.item_val.config(format="%.0f ")
                self.item_val.set(f'{0:0.0f}') 
            else:
                pass
        
        words={
            "Potion":"Heals For:",
            "Armor":"Defense:",
            "Weapon":"Attack:",}
        self.iframe = tk.Frame(self.panels)
        self.panels.add(self.iframe,text='Items')

        form = tk.Frame(self.iframe,height=100)
        form.pack(side=tk.TOP,fill='both',expand=1)
        
        tk.Label(form,text='Name:',width=8,anchor='w').grid(row=0,column=0,sticky='we')
        self.i_name_input=tk.Entry(form)
        self.i_name_input.grid(row=0,column=1,sticky='we')
        tk.Label(form,text="Rarity:",anchor='w').grid(row=0,column=2,sticky='w')
        self.i_rarity = ttk.Spinbox(form,from_=0,to=5,width=2)
        self.i_rarity.set(0)
        self.i_rarity.grid(row=0,column=3,sticky='w')
        tk.Label(form,text="Price:",anchor='w').grid(row=0,column=4,sticky='w')
        self.i_cost = ttk.Spinbox(form,from_=0,to=9999,width=5)
        self.i_cost.set(0)
        self.i_cost.grid(row=0,column=5,sticky='w')

        tk.Label(form,text='Type:',anchor='w').grid(row=1,column=0,sticky='we')
        self.i_type=tk.StringVar()
        self.i_type.set("Armor")
        self.option = ttk.Combobox(form,state='readonly',textvariable=self.i_type,values=("Armor",'Potion',"Weapon"))
        self.option.bind("<<ComboboxSelected>>",option_changed)
        self.option.grid(row=1,column=1,sticky='we')
          
        self.item_val_label = tk.Label(form,text=words[self.i_type.get()],anchor='w')
        self.item_val_label.grid(row=2,column=0,sticky='we')
        self.item_val = ttk.Spinbox(form,from_=0,to=500,width=24)
        self.item_val.set(f'{0:0.0f} Def') 
        self.item_val.grid(row=2,column=1,sticky='w')
        
        self.hc_label = tk.Label(form,text="Hit Chance:",anchor='w',width=9)
        self.i_hitchance = ttk.Spinbox(form,width=7,from_=0,to=100,increment=5,format='%.0f%%')        
        self.i_hitchance.set(f'{0:0.0f}%')
        self.as_label = tk.Label(form,text="Armor Slot:",anchor='w',width=9)
        self.i_armor_slot = ttk.Combobox(form,width=4,state='readonly',values=("head","chest","arms","legs","feet"))
        self.i_armor_slot.set('Head')
        self.ht_label=tk.Label(form,text="Heals:",anchor='w',width=9)
        self.i_heal_type = ttk.Combobox(form,state='readonly',width=4,values=("HP","MP"))
        self.i_heal_type.set("HP")
        self.as_label.grid(row=3,column=0,sticky='we')
        self.i_armor_slot.grid(row=3,column=1,sticky='we')
        
        def add_item():
            type = 'usable' if self.i_type.get()=='Potion' else 'equipment'
            temp = {
                'type':type,
                'name':self.i_name_input.get().strip(),
                'rarity':int(self.i_rarity.get().split(' ')[0]),
                'price':int(self.i_cost.get().split(" ")[0]),
            }
            if self.i_type.get()=='Armor':
                temp['slot'] = self.i_armor_slot.get().lower()
                temp['defence'] = int(self.item_val.get().split(' ')[0])
            if self.i_type.get()=='Weapon':
                temp['slot']='weapon'
                temp['attack']=int(self.item_val.get().split(' ')[0])
                temp['hitchance'] = int(self.i_hitchance.get().split("%")[0])/100
            if self.i_type.get()=='Potion':
                temp['recovers'] = 'health' if self.i_heal_type.get()=='HP' else 'mana'
                temp['recoverval']=int(self.item_val.get().split(' ')[0])
            if temp['name']=='':
                print('Empty name')
                return
            for i in self.ENTITIES:
                if temp['name']==i['name']:
                    print('item already exists')
                    return
            self.clear_i_details()
            self.ENTITIES.append(temp)
            self.load_items()
        def save_edited():
            for x in self.ENTITIES:
                if x['name'] == self.i_list.item(self.i_id,'text'):
                    x['name']=self.i_name_input.get().strip()
                    x['type']= 'usable' if self.i_type.get()=='Potion' else 'equipment'
                    x['rarity']=int(self.i_rarity.get().split(' ')[0])
                    x['price']=int(self.i_cost.get().split(' ')[0])
                    if self.i_type.get()=='Armor':
                        x['slot'] = self.i_armor_slot.get().lower()
                        x['defence'] = int(self.item_val.get().split(' ')[0])
                    if self.i_type.get()=='Weapon':
                        x['slot']='weapon'
                        x['attack']=int(self.item_val.get().split(' ')[0])
                        x['hitchance'] = int(self.i_hitchance.get().split("%")[0])/100
                    if self.i_type.get()=='Potion':
                        x['recovers'] = 'health' if self.i_heal_type.get()=='HP' else 'mana'
                        x['recoverval']=int(self.item_val.get().split(' ')[0])
                    self.clear_i_details()
                    self.load_items()
                    return
        def delete_item():###Finish Changing
            vals = self.i_list.item(self.i_id,'values')
            type = 'usable' if self.i_type.get()=='Potion' else 'equipment'
            temp = {
                'type':type,
                'name':self.i_list.item(self.i_id,'text'),
                'rarity':int(vals[0]),
                'price':int(vals[1]),
                }
            if self.i_type.get()=='Armor':
                temp['slot'] = vals[3]
                temp['defence'] = int(vals[2].split(' ')[0])
            if self.i_type.get()=='Weapon':
                temp['slot']='weapon'
                temp['attack']=int(vals[2].split(' ')[0])
                temp['hitchance'] = int(vals[3].split("%")[0])/100
            if self.i_type.get()=='Potion':
                temp['recovers'] = vals[3]
                temp['recoverval']=int(vals[2])
            self.ENTITIES.remove(temp)
            self.clear_i_details()
            self.load_items()
        
        
        def alert():    
            print('Name: '+self.i_name_input.get())
            print(f'Rarity: {self.i_rarity.get()}')
            print(f'Cost: {self.i_cost.get()}')
            print(f'Type: {self.i_type.get()}')
            if self.i_type.get()=='Armor':
                print(f'Defence:{self.item_val.get()}')
                print(f'Slot:{self.i_armor_slot.get()}')
            if self.i_type.get()=='Weapon':
                print(f'Attack:{self.item_val.get()}')
                print(f'HitChance:{self.i_hitchance.get()}')
            if self.i_type.get()=='Potion':
                print(f'Heals for:{self.item_val.get()}')
                print(f'Heals: {self.i_heal_type.get()}')
        
        self.create_i_treeview()
                
        
        self.new_i_button= tk.Button(form,text='Add Item',width=9,command=add_item)
        self.new_i_button.grid(row=0,column=6,sticky='we')
        self.edit_i_button= tk.Button(form,text='Edit Item',width=9,state='disabled',command=save_edited)
        self.edit_i_button.grid(row=0,column=7,sticky='we')
        self.delete_i_button= tk.Button(form,text='Delete Item',width=9,state='disabled',command=delete_item)
        self.delete_i_button.grid(row=0,column=8,sticky='we')
        self.cancel_i_button= tk.Button(form,text='Cancel',width=9,state='disabled',command=self.clear_i_details)
        self.cancel_i_button.grid(row=0,column=9,sticky='we')
        
    def create_sframe(self):
        def option_changed(event):
            self.targ_val_label.config(text=words[self.s_target.get()])
            
        words={
            "self":'Heals:',
            "enemy":'Deals:'
        }
        
        self.sframe = tk.Frame(self.panels)
        self.panels.add(self.sframe,text='SpellBooks')
        form = tk.Frame(self.sframe)
        form.pack(side=tk.TOP,fill=tk.BOTH,expand=1)
        
        tk.Label(form,text='Name:',width=8,anchor='w').grid(row=0,column=0,sticky='we')
        self.s_name_input=tk.Entry(form)
        self.s_name_input.grid(row=0,column=1,sticky='we')
        tk.Label(form,text="Rarity:",anchor='w').grid(row=0,column=2,sticky='w')
        self.s_rarity = ttk.Spinbox(form,from_=5,to=10,width=2)
        self.s_rarity.set(5)
        self.s_rarity.grid(row=0,column=3,sticky='w')
        tk.Label(form,text="Price:",anchor='w').grid(row=0,column=4,sticky='w')
        self.s_cost = ttk.Spinbox(form,from_=0,to=9999,width=5)
        self.s_cost.set(0)
        self.s_cost.grid(row=0,column=5,sticky='w')

        tk.Label(form,text='Spell Slot:',anchor='w').grid(row=1,column=0,sticky='we')
        self.s_slot=tk.StringVar()
        self.s_slot.set("level:1")
        self.slot_option = ttk.Combobox(form,state='readonly',textvariable=self.s_slot,values=("level:1",'level:2',"level:3","level:4"))
        self.slot_option.grid(row=1,column=1,sticky='we')

        tk.Label(form,text='Target:',anchor='w').grid(row=2,column=0,sticky='we')
        self.s_target=tk.StringVar()
        self.s_target.set("self")
        self.target_option = ttk.Combobox(form,state='readonly',textvariable=self.s_target,values=("self",'enemy'))
        self.target_option.bind("<<ComboboxSelected>>",option_changed)
        self.target_option.grid(row=2,column=1,sticky='we')

        self.targ_val_label = tk.Label(form,text="Heals:",anchor='w')
        self.targ_val_label.grid(row=3,column=0,sticky='w')
        self.s_value = ttk.Spinbox(form,from_=0,to=9999,width=24,format='+%0.0f')
        self.s_value.set(f'+{0:0.0f}')
        self.s_value.grid(row=3,column=1,sticky='w')

        tk.Label(form,text="MP Cost:",anchor='w').grid(row=4,column=0,sticky='w')
        self.s_mpcost = ttk.Spinbox(form,from_=0,to=9999,width=24)
        self.s_mpcost.set(0)
        self.s_mpcost.grid(row=4,column=1,sticky='w')

        
        def add_spellbook():
            temp={
                'type':'spell_book',
                'name':self.s_name_input.get(),
                'rarity':self.s_rarity.get(),
                'price':self.s_cost.get(),
                'spellslot':self.s_slot.get(),
                'target':self.s_target.get(),
                'value':self.s_value.get()[1:],
                'manacost':self.s_mpcost.get(),    
            }
            for e in temp.values():
                if e=='' or e==0:
                    print('empty spell')
                    return
            for e in self.ENTITIES:
                if temp['name'] == e['name']:
                    print('spell with name exists')
                    return
            self.clear_s_details()
            self.ENTITIES.append(temp)
            self.load_spells()
        def save_edited():
            for x in self.ENTITIES:
                if x['name'] == self.s_list.item(self.s_id,'text'):
                    x['name']=self.s_name_input.get()
                    x['rarity']=self.s_rarity.get()
                    x['price']=self.s_cost.get()
                    x['spellslot']=self.s_slot.get()
                    x['target']=self.s_target.get()
                    x['value']=self.s_value.get()[1:]
                    x['manacost']=self.s_mpcost.get()
                    return
            self.clear_s_details()        
        def delete_spellbook():
            vals = self.s_list.item(self.s_id,'values')
            temp = {
                'type':'spell_book',
                'name':self.s_list.item(self.s_id,'text'),
                'rarity':int(vals[0]),
                'price':int(vals[1]),
                'spellslot':vals[2],
                'target':vals[3],
                'value':int(vals[4][1:]),
                'manacost':int(vals[5])}
            print(temp in self.ENTITIES)
            self.ENTITIES.remove(temp)
            self.clear_s_details()
            self.load_spells()
            
            
        
        self.new_s_button= tk.Button(form,text='Add Item',width=9,command=add_spellbook)
        self.new_s_button.grid(row=0,column=6,sticky='we')
        self.edit_s_button= tk.Button(form,text='Edit Item',width=9,state='disabled',command=save_edited)
        self.edit_s_button.grid(row=0,column=7,sticky='we')
        self.delete_s_button= tk.Button(form,text='Delete Item',width=9,state='disabled',command=delete_spellbook)
        self.delete_s_button.grid(row=0,column=8,sticky='we')
        self.cancel_s_button= tk.Button(form,text='Cancel',width=9,state='disabled',command=self.clear_s_details)
        self.cancel_s_button.grid(row=0,column=9,sticky='we')
        
        self.create_s_treeview()
    
    def create_m_treeview(self):
        def no_resize(event):
            if self.m_list.identify_region(event.x,event.y)== 'separator':
                return 'break'
        def get_details(event):
            try:
                self.m_id=inv_id = self.m_list.selection()[0]
                vals = self.m_list.item(inv_id,'values')
                self.m_name_input.delete(0, 'end')
                self.m_name_input.insert('end',self.m_list.item(inv_id,'text'))
                self.m_maxhp.set(f'{int(vals[0]):0.0f} HP')
                self.m_attack.set(f'{int(vals[1]):0.0f} Att')
                self.m_hitchance.set(f'{int(vals[2][:4]):0.0f}%')
                self.m_defence.set(f'{int(vals[3]):0.0f} Def')
                self.m_gold.set(f'{int(vals[4]):0.0f} Gol')
                self.m_exp.set(f'{int(vals[5]):0.0f} Exp')
                self.new_m_button.config(state='disabled')
                self.edit_m_button.config(state='normal')
                self.delete_m_button.config(state='normal')
                self.cancel_m_button.config(state='normal')
                self.cancel_m_button.config(command=clear_details)
            except IndexError:
                pass
        def clear_details():
            self.clear_m_details()
                
        self.m_list = SortSearchTreeview(self.mframe,selectmode='browse')
        self.m_list.pack(side='left',fill='x',expand=1)
        vsb = ttk.Scrollbar(self.mframe,orient='vertical',command=self.m_list.yview)
        vsb.pack(side='right',fill='y')
        self.m_list.configure(yscrollcommand=vsb.set)
        headings = ('Name','Health',"Attack","Hit%","Defence","Gold","Exp")
        self.m_list['columns']=('1','2','3','4','5','6')
        self.m_list.column('#0',width=60)
        self.m_list.column('1',width=10)
        self.m_list.column('2',width=10)
        self.m_list.column('3',width=10)
        self.m_list.column('4',width=10)
        self.m_list.column('5',width=10)
        self.m_list.heading("#0",text=headings[0],anchor=tk.W)
        self.m_list.heading("1",text=headings[1],anchor=tk.W)
        self.m_list.heading("2",text=headings[2],anchor=tk.W)
        self.m_list.heading("3",text=headings[3],anchor=tk.W)
        self.m_list.heading("4",text=headings[4],anchor=tk.W)
        self.m_list.heading("5",text=headings[5],anchor=tk.W)
        self.m_list.heading("6",text=headings[6],anchor=tk.W)
        self.load_monsters()
        
        self.m_list.bind("<Button-1>",no_resize)
        self.m_list.bind("<Double-Button-1>",get_details)
            
    def create_i_treeview(self):
        def no_resize(event):
            if self.i_list.identify_region(event.x,event.y)== 'separator':
                return 'break'
        def get_details(event):
            try:
                words={
                    "Potion":"Heals For:",
                    "Armor":"Defense:",
                    "Weapon":"Attack:",}
                try:
                    self.hc_label.grid_forget()
                    self.i_hitchance.grid_forget()
                    self.as_label.grid_forget()
                    self.i_armor_slot.grid_forget()
                    self.ht_label.grid_forget()
                    self.i_heal_type.grid_forget()
                except:
                    pass
                self.i_id=inv_id = self.i_list.selection()[0]
                vals = self.i_list.item(inv_id,'values')
                if len(vals)==0:
                    return
                self.i_name_input.delete(0, 'end')
                self.i_name_input.insert('end',self.i_list.item(inv_id,'text'))
                self.i_rarity.set(f'{int(vals[0]):0.0f}')
                self.i_cost.set(f'{int(vals[1]):0.0f}')
                if self.i_list.parent(inv_id)=='p':
                    self.i_type.set('Potion')
                    self.item_val_label.config(text=words[self.i_type.get()])
                    ext=""
                    self.ht_label.grid(row=3,column=0,sticky='we')
                    self.i_heal_type.grid(row=3,column=1,sticky='we')
                    self.item_val.config(format="%.0f ")
                if self.i_list.parent(inv_id)=='a':
                    self.i_type.set('Armor')
                    self.item_val_label.config(text=words[self.i_type.get()])
                    ext=" Def"
                    self.i_armor_slot.set(vals[3])
                    self.as_label.grid(row=3,column=0,sticky='we')
                    self.i_armor_slot.grid(row=3,column=1,sticky='we')
                    self.item_val.config(format="%.0f Def")
                if self.i_list.parent(inv_id)=='w':
                    self.i_type.set('Weapon')
                    self.item_val_label.config(text=words[self.i_type.get()])
                    ext=" Att"
                    self.hc_label.grid(row=3,column=0,sticky='we')
                    self.i_hitchance.grid(row=3,column=1,sticky='w')
                    self.item_val.config(format="%.0f Att")
                    self.i_hitchance.set(f'{int(vals[3].split("%")[0]):0.0f}%')
                    
                    
                
                self.item_val.set(f'{int(vals[2].split(" ")[0]):0.0f}{ext}')
                
                
                self.new_i_button.config(state='disabled')
                self.edit_i_button.config(state='normal')
                self.delete_i_button.config(state='normal')
                self.cancel_i_button.config(state='normal')
                self.cancel_i_button.config(command=clear_details)
            except IndexError:
                pass
        def clear_details():
            self.clear_i_details()
        
        self.i_list = SortSearchTreeview(self.iframe,selectmode='browse')
        self.i_list.pack(side='left',fill='x',expand=1)
        vsb = ttk.Scrollbar(self.iframe,orient='vertical',command=self.i_list.yview)
        vsb.pack(side='right',fill='y')
        self.i_list.configure(yscrollcommand=vsb.set)
        headings=["Rarity","Price"]
        self.i_list['columns']=("one","two","three","four")
        self.i_list.column('#0',width=100)
        self.i_list.heading('#0',text="Type/Name",anchor=tk.W)
        
        self.i_list.column("one",width=5)
        self.i_list.column("two",width=5)
        self.i_list.column("three",width=5)
        self.i_list.column("four",width=5)
        
        self.i_list.heading("one",text=headings[0],anchor=tk.W)
        self.i_list.heading("two",text=headings[1],anchor=tk.W)
        self.i_list.heading("three",text="Info 1",anchor=tk.W)
        self.i_list.heading("four",text="Info 2",anchor=tk.W)

        
        self.i_list.insert("","end","p",text="Potion")
        self.i_list.insert("","end","w",text="Weapon")
        self.i_list.insert("","end","a",text="Armor")
        
        self.i_list.bind("<Button-1>",no_resize)
        self.i_list.bind("<Double-Button-1>",get_details)
        
        
        #self.i_list.insert("","end","s",text="Spell")
        self.load_items()
     
    def create_s_treeview(self):
        def no_resize(event):
            if self.s_list.identify_region(event.x,event.y)== 'separator':
                return 'break'
        def get_details(event):
            try:
                self.s_id=inv_id = self.s_list.selection()[0]
                vals = self.s_list.item(inv_id,'values')
                
                self.s_name_input.delete(0, 'end')
                self.s_name_input.insert('end',self.s_list.item(inv_id,'text'))
                self.s_rarity.set(f'{int(vals[0]):0.0f}')
                self.s_cost.set(f'{int(vals[1]):0.0f}')
                self.s_slot.set(vals[2])
                self.s_target.set(vals[3])
                self.s_value.set(f'+{int(vals[4])}')
                self.s_mpcost.set(f'{int(vals[5])}') 
                
                if vals[3]=='enemy':
                    self.targ_val_label.config(text='Deals:')
                else:
                    self.targ_val_label.config(text='Heals:')
                
                self.new_s_button.config(state='disabled')
                self.edit_s_button.config(state='normal')
                self.delete_s_button.config(state='normal')
                self.cancel_s_button.config(state='normal')
                self.cancel_s_button.config(command=clear_details)
            except IndexError:
                pass
        def clear_details():
            self.clear_s_details()
        
        
        self.s_list = SortSearchTreeview(self.sframe,selectmode='browse')
        self.s_list.pack(side='left',fill='x',expand=1)
        vsb = ttk.Scrollbar(self.sframe,orient='vertical',command=self.s_list.yview)
        vsb.pack(side='right',fill='y')
        self.s_list.configure(yscrollcommand=vsb.set)
        headings=["Rarity","Price"]
        self.s_list['columns']=("one","two","three","four",'five','six')
        self.s_list.column('#0',width=150)
        self.s_list.heading('#0',text="Name",anchor=tk.W)
        
        self.s_list.column("one",width=5)
        self.s_list.column("two",width=5)
        self.s_list.column("three",width=5)
        self.s_list.column("four",width=5)
        self.s_list.column("five",width=5)
        self.s_list.column("four",width=5)
        
        self.s_list.heading("one",text=headings[0],anchor=tk.W)
        self.s_list.heading("two",text=headings[1],anchor=tk.W)
        self.s_list.heading("three",text="Slot",anchor=tk.W)
        self.s_list.heading("four",text="Target",anchor=tk.W)
        self.s_list.heading("five",text="Value",anchor=tk.W)
        self.s_list.heading("six",text="MP Cost",anchor=tk.W)
        self.s_list.bind("<Button-1>",no_resize)
        self.s_list.bind("<Double-Button-1>",get_details)
        
        self.load_spells()
        
    def load_items(self):
        for row in self.i_list.get_children():
            self.i_list.delete(row)
        self.i_list.insert("","end","p",text="Potion")
        self.i_list.insert("","end","w",text="Weapon")
        self.i_list.insert("","end","a",text="Armor")
        for ind,ent in enumerate(self.ENTITIES):
            if ent['type']=='equipment':
                if ent['slot']=='weapon':
                    self.i_list.insert("w","end",ind,text=ent['name'],values=(ent['rarity'],ent['price'],f"{ent['attack']} Att",f"{ent['hitchance']*100:0.0f}% Hit") )
                else:
                    self.i_list.insert('a','end',ind,text=ent['name'],values=(ent['rarity'],ent['price'],f"{ent['defence']} Def",f"{ent['slot']}"))
            if ent['type']=='usable':
                self.i_list.insert('p','end',ind,text=ent['name'],values=(ent['rarity'],ent['price'],f"{ent['recoverval']}",ent['recovers']))
            '''if ent['type']=='spell_book':
                e='+' if ent['target']=='self' else '-'  
                self.i_list.insert('s','end',ind,text=ent['name'],values=(ent['rarity'],ent['price'],f"{ent['spellslot']}",ent['target'],f"{e}{ent['value']}HP",f"-{ent['manacost']}MP"))
            '''    
    def load_monsters(self):
        for row in self.m_list.get_children():
            self.m_list.delete(row)
        for ind,ent in enumerate(self.ENTITIES):
            if ent['type']=='enemy':
                self.m_list.insert("",ind,text=ent['name'],values=(ent['maxhp'],ent['attack'],f"{ent['hitchance']*100:0.0f}",ent['defence'],ent['gold'],ent['exp']) )
    def load_spells(self):
        for row in self.s_list.get_children():
            self.s_list.delete(row)
        for ind,ent in enumerate(self.ENTITIES):
                if ent['type']=='spell_book':
                    self.s_list.insert("",ind,text=ent['name'],values=(ent['rarity'],ent['price'],ent['spellslot'],ent['target'],ent['value'],ent['manacost']) )
    
    def save_all(self):#sort before saving
        def get_type(json):
            try:
                return json['type']
            except KeyError:
                return ''        
        self.ENTITIES.sort(key=get_type)
        json_list = json.dumps(self.ENTITIES,indent=4)
        with open ('./src/entities.json','w+') as file:
            file.writelines(json_list)

    def clear_m_details(self):
        self.m_name_input.delete(0, 'end')
        self.m_maxhp.set(f'{0:0.0f} HP')
        self.m_attack.set(f'{0:0.0f} Att')
        self.m_hitchance.set(f'{0:0.0f}%')
        self.m_defence.set(f'{0:0.0f} Def')
        self.m_gold.set(f'{0:0.0f} Gol')
        self.m_exp.set(f'{0:0.0f} Exp')
        self.new_m_button.config(state='normal')
        self.edit_m_button.config(state='disabled')
        self.delete_m_button.config(state='disabled')
        self.cancel_m_button.config(state='disabled')
    
    def clear_i_details(self):
        self.i_name_input.delete(0, 'end')
        self.i_rarity.set(f'{0:0.0f}')
        self.i_cost.set(f'{0:0.0f}')
        try:
            self.hc_label.grid_forget()
            self.i_hitchance.grid_forget()
            self.as_label.grid_forget()
            self.i_armor_slot.grid_forget()
            self.ht_label.grid_forget()
            self.i_heal_type.grid_forget()
        except:
            pass
        
        self.i_type.set('Armor')
        self.item_val_label.config(text="Defence")
        self.i_armor_slot.set('head')
        self.as_label.grid(row=3,column=0,sticky='we')
        self.i_armor_slot.grid(row=3,column=1,sticky='we')
        self.item_val.config(format="%.0f Def")
        self.item_val.set(f'{0:0.0f} Def')
                
        
        self.new_i_button.config(state='normal')
        self.edit_i_button.config(state='disabled')
        self.delete_i_button.config(state='disabled')
        self.cancel_i_button.config(state='disabled')    
    
    def clear_s_details(self):###TODO
        self.s_name_input.delete(0, 'end')
        self.s_rarity.set(f'{5:0.0f}')
        self.s_cost.set(f'{0:0.0f}')
        self.s_slot.set("level:1")
        self.s_target.set('self')
        self.s_value.set(f'+{0}')
        self.s_mpcost.set(f'{0}') 
        self.targ_val_label.config(text='Heals:')
        self.new_s_button.config(state='normal')
        self.edit_s_button.config(state='disabled')
        self.delete_s_button.config(state='disabled')
        self.cancel_s_button.config(state='disabled')
    

if __name__=="__main__":
    root = tk.Tk()
    root.resizable(0,0)
    app = Editor(root)
    app.mainloop()
