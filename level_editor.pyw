#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk,messagebox,filedialog,colorchooser
import os,json
BOX=20
BASE_H_OFFSET=75
BASE_W_OFFSET=640#130


class Editor(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.master=master
        self.pack(fill=tk.BOTH,expand=1)
        self.fn = tk.StringVar()
        
        self.ENEMY_NAMES={}
        try:
            with open('./src/entities.json','r') as f:
                for object in json.load(f):
                    if object['type'] =='enemy':
                        self.ENEMY_NAMES[object['name']]=tk.BooleanVar()
        except:
            pass
        self.make_frames()
            
    def configurables(self):
        def inc_rows():
            if not self.row_value.get()+1 > 30:
                self.row_value.set(self.row_value.get()+1)
                self.on_resize(("increase","row"))
        def dec_rows():
            if not self.row_value.get()-1 < 5:
                self.row_value.set(self.row_value.get()-1)
                self.on_resize(("decrease","row"))
        def inc_cols():
             if not self.col_value.get()+1 > 30:
                self.col_value.set(self.col_value.get()+1)
                self.on_resize(("increase",'col'))
        def dec_cols():
            if not self.col_value.get()-1 < 5:
                self.col_value.set(self.col_value.get()-1)
                self.on_resize(("decrease",'col'))
        
        self.row_value = tk.IntVar()
        self.rows_slider = tk.Scale(self.dimensions_frame,from_=5,to=30,orient=tk.HORIZONTAL,variable=self.row_value,showvalue=0)
        self.inc_row_button = tk.Button(self.dimensions_frame,text=">",command=inc_rows)
        self.dec_row_button = tk.Button(self.dimensions_frame,text="<",command=dec_rows)
        tk.Label(self.dimensions_frame,text='Rows:').grid(column=0,row=0,sticky='e')
        tk.Label(self.dimensions_frame,textvariable=self.row_value,width=2).grid(column=1,row=0,sticky='w')
        self.dec_row_button.grid(column=2,row=0,sticky='w')
        self.rows_slider.grid(column=3,row=0,sticky='w')
        self.inc_row_button.grid(column=4,row=0,sticky='w')
        
        self.col_value = tk.IntVar()
        self.cols_slider = tk.Scale(self.dimensions_frame,from_=5,to=30,orient=tk.HORIZONTAL,variable=self.col_value,showvalue=0)
        self.inc_col_button = tk.Button(self.dimensions_frame,text=">",command=inc_cols)
        self.dec_col_button = tk.Button(self.dimensions_frame,text="<",command=dec_cols)
        tk.Label(self.dimensions_frame,text='Columns:').grid(column=0,row=1,sticky='w')
        tk.Label(self.dimensions_frame,textvariable=self.col_value,width=2).grid(column=1,row=1)
        self.dec_col_button.grid(column=2,row=1,sticky='w')
        self.cols_slider.grid(column=3,row=1,sticky='w')
        self.inc_col_button.grid(column=4,row=1,sticky='w')
        self.entrance=[0,0]
        self.exit=[0,0]
        self.make_options()
        self.rows_slider.bind('<ButtonRelease-1>',self.on_resize)
        self.rows_slider.bind('<ButtonRelease-3>',self.on_resize)
        self.cols_slider.bind('<ButtonRelease-1>',self.on_resize)
        self.cols_slider.bind('<ButtonRelease-3>',self.on_resize)
        
    def validate(self,P):
        if P.isdigit() or P=="":
            return True
        return False
    
    def make_options(self):        
        def limit_chars(*args):
            value = self.fl_lower.get()
            if len(value) > 2:self.fl_lower.set(value[:2])
            value = self.fl_upper.get()
            if len(value) > 2:self.fl_upper.set(value[:2])
        ###create boundry vars, bind to limit callback method
        self.fl_lower = tk.StringVar()
        self.fl_upper = tk.StringVar()
        self.fl_lower.trace('w',limit_chars)
        self.fl_upper.trace('w',limit_chars)
        self.fl_lower.set(1)
        self.fl_upper.set(1)
        ### disallow alphabetical and special characters     
        vcmd=(self.register(self.validate))
        ### define UI components
        tk.Label(self.dimensions_frame,text='Floors:').grid(column=5,row=0,padx=5,sticky='w')
        self.floor_lower_bounds = tk.Entry(self.dimensions_frame,width=2,textvariable=self.fl_lower)
        self.floor_lower_bounds.grid(column=6,row=0,sticky='w')
        tk.Label(self.dimensions_frame,text='-',font=("",16)).grid(column=7,row=0,sticky='w')
        self.floor_upper_bounds = tk.Entry(self.dimensions_frame,width=2,textvariable=self.fl_upper)
        self.floor_upper_bounds.grid(column=8,row=0,sticky='w')
        self.mobselected=[]
        self.show_mobs_button=tk.Button(self.dimensions_frame,text='Select Available Mobs')
        self.show_mobs_button.bind('<Button-1>',self.mobselect)
        self.show_mobs_button.grid(column=5,row=1,padx=5,columnspan=4,sticky='w')
        
        self.bg_color='black'
        self.fg_color='white'
        
        self.bg_select=tk.Button(self.dimensions_frame,width=17,text='Background Color')
        self.bg_select.grid(column=9,row=0)
        self.bg_select.bind('<Button-1>',self.confirm_bg)
        self.fg_select=tk.Button(self.dimensions_frame,width=17,text='Foreground Color')
        self.fg_select.grid(column=9,row=1)
        self.fg_select.bind('<Button-1>',self.confirm_fg)
        
        self.cv = tk.Canvas(self.dimensions_frame,width=20,height=20)
        self.cv_bg = self.cv.create_rectangle(0,0,20,20,fill=self.bg_color,outline="")
        self.cv_fg = self.cv.create_text(10,10,fill=self.fg_color,text=u'\u25a0')
        self.cv.grid(column=10,row=0,rowspan=2)
        
        self.export_button = tk.Button(self.dimensions_frame,width=8,text="Export\nto File")
        self.export_button.grid(column=11,row=0,rowspan=2,sticky='ns')
        self.export_button.bind('<Button-1>',self.export_to_file)
        
        
        self.load_button = tk.Button(self.dimensions_frame,width=8,text="Load\nfrom\nFile")
        self.load_button.bind('<Button-1>',self.load_from_file)
        self.load_button.grid(column=12,row=0,rowspan=2,sticky='ns')
        
        ### Bind validation
        self.floor_lower_bounds.config(validate='key',validatecommand=(vcmd,'%P'))
        self.floor_upper_bounds.config(validate='key',validatecommand=(vcmd,'%P'))
    
    def confirm_bg(self,event):
        self.bg_color=colorchooser.askcolor()[1]
        self.cv.itemconfig(self.cv_bg,fill=self.bg_color)
        
    def confirm_fg(self,event):
        self.fg_color=colorchooser.askcolor()[1]
        self.cv.itemconfig(self.cv_fg,fill=self.fg_color)
    
    def mobselect(self,event):
        def destroy_toplevel():
            tl.destroy()
        tl = tk.Toplevel(self,highlightbackground="black", highlightthickness=4)
        tl.geometry(f"+{self.master.winfo_x()+(event.x)}+{self.master.winfo_y()+event.y}")
        tl.resizable(0,0)
        tl.overrideredirect(True)
        tl.grab_set()
        tk.Label(tl,text='Available Mobs:').grid(padx=30,sticky='w')
        for x in self.ENEMY_NAMES:
            cb = tk.Checkbutton(tl,text=x,variable=self.ENEMY_NAMES[x])
            cb.grid(padx=30,sticky='w')
        tk.Button(tl,text='Confirm',command=destroy_toplevel).grid(padx=30,pady=5,sticky='we')

    def make_frames(self):
        self.dimensions_frame= tk.Frame(self)
        self.grid_frame= tk.Frame(self)
        ###build Sliders###
        self.configurables()
        
        ###Build Grid###
        self.init_grid()
        
        ###build context Menu###
        self.create_ctx_menu()
        
        ### PACKING FRAMES###
        self.dimensions_frame.pack(side=tk.TOP,anchor=tk.NW)
        self.grid_frame.pack(anchor=tk.NW,pady=10,padx=20)
    
    def create_ctx_menu(self):
        self.ctx_menu = tk.Menu(self.canvas,tearoff=0,font=('consolas',8))
        self.ctx_menu.add_command(label='Monster      (m)',command =lambda e='m': self.selected_ctx(e) )
        self.ctx_menu.add_command(label='Chest        (c)',command =lambda e='c': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Door         (d)',command =lambda e='d': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Gold         (g)',command =lambda e='g': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Trap         (?)',command =lambda e='?': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Entrance     (.)',command =lambda e='.': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Exit         (!)',command =lambda e='!': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Shop         ($)',command =lambda e='$': self.selected_ctx(e))
        self.ctx_menu.add_command(label='False wall   (|)',command =lambda e='|': self.selected_ctx(e))
        self.ctx_menu.add_command(label='Clear Everything',command =lambda e='all': self.selected_ctx(e))
        self.canvas.bind('<Button-3>',lambda e:self.show_ctx_menu(e))

    def show_ctx_menu(self,event):
        try:
            self.ctx_menu.tk_popup(event.x_root,event.y_root)
            self.rx = event.x//BOX
            self.ry = event.y//BOX
        finally:
            self.ctx_menu.grab_release()
        
    def selected_ctx(self,command):
        #print(command,self.rx,self.ry)
        command_colors={
            "m":"red",
            "c":"brown",
            "g":'yellow',
            "d":'slate grey',
            "?":'lightgrey',
            "$":'green',
            ".":'blue',
            "!":'aqua',
            '|':'gray18'
            }
        if command=='all':
            for row in range(len(self.square_grid)):
                for col in range(len(self.square_grid[row])):
                    self.values_grid[row][col]='s'
                    self.canvas.itemconfig(self.square_grid[row][col],fill='white')
            return
            
        exists = False
        if command in ('.','!','$'):
            for row in self.values_grid:
                if command in row:
                    exists=True
                else:
                    if command=='.':self.entrance=[self.ry,self.rx]
                    if command=='!':self.exit=[self.ry,self.rx]
        if exists==False:
            self.values_grid[self.ry][self.rx]=command
            self.canvas.itemconfig(self.square_grid[self.ry][self.rx],fill=command_colors[command])

    def init_grid(self):
        winwidth =  BASE_W_OFFSET
        winheight = (self.row_value.get()*BOX) + BASE_H_OFFSET
        if os.name=='nt':
            self.master.geometry(f'{winwidth}x{winheight}')
        else:
            self.master.geometry(f'{winwidth+190}x{winheight+20}')
        
        board_width=(self.col_value.get()*BOX)-1
        board_height=(self.row_value.get()*BOX)-1
        print(board_width,board_height)
        self.canvas = tk.Canvas(self.grid_frame,width=board_width,height=board_height,bg='grey')
        self.canvas.pack(fill=tk.BOTH)
        
        self.square_grid=[]
        self.values_grid=[]
        for row in range(self.row_value.get()):
            self.square_grid.append([])
            self.values_grid.append([])
            for column in range(self.col_value.get()):
                x1,y1=column*BOX,row*BOX
                x2,y2=x1+BOX,y1+BOX
                b = self.canvas.create_rectangle(x1,y1,x2,y2,fill="#FFFFFF")
                self.square_grid[row].append(b)
                self.values_grid[row].append("s")
        self.coords = {'x':0,'y':0,'x2':0,'y2':0}
        self.canvas.bind('<ButtonPress-1>',self.on_square_clicked)
        self.canvas.bind('<ButtonRelease-1>',self.on_square_release)
        
    def on_resize(self,event):
        try:#click button
            if event[0]=="increase":
                if event[1]=='row':
                    self.values_grid.append([])
                    self.square_grid.append([])
                    for col in range(self.col_value.get()):
                        x1,y1=col*BOX,(len(self.square_grid)-1)*BOX
                        x2,y2=x1+BOX,y1+BOX
                        b = self.canvas.create_rectangle(x1,y1,x2,y2,fill="#FFFFFF")
                        self.square_grid[-1].append(b)
                        self.values_grid[-1].append('s')
                elif event[1]=='col':
                    for row in range(self.row_value.get()):
                        x1,y1=(len(self.square_grid[row]))*BOX,row*BOX
                        x2,y2=x1+BOX,y1+BOX
                        b = self.canvas.create_rectangle(x1,y1,x2,y2,fill="#FFFFFF")
                        self.square_grid[row].append(b)
                        self.values_grid[row].append('s')
            elif event[0]=="decrease":
                if event[1]=='row':
                    self.square_grid.pop()
                    self.values_grid.pop()
                if event[1]=='col':
                    for row in range(self.row_value.get()):
                        self.square_grid[row].pop()
                        self.values_grid[row].pop()
        except:#drag bar
            if self.row_value.get() > len(self.square_grid):#print('increased rows')
                for row in range (self.row_value.get()-len(self.square_grid)):
                    self.values_grid.append([])
                    self.square_grid.append([])
                    for col in range(self.col_value.get()):
                        x1,y1=col*BOX,(len(self.square_grid)-1)*BOX
                        x2,y2=x1+BOX,y1+BOX
                        b = self.canvas.create_rectangle(x1,y1,x2,y2,fill="#FFFFFF")
                        self.square_grid[-1].append(b)
                        self.values_grid[-1].append('s')
            elif self.row_value.get() < len(self.square_grid):#print('decreased rows')
                for x in range(len(self.square_grid)-self.row_value.get()):
                    self.square_grid.pop()
                    self.values_grid.pop()
            elif self.col_value.get() > len(self.square_grid[0]):#print('increased cols')
                for row in range(self.row_value.get()):
                    for col in range(self.col_value.get()-len(self.square_grid[row])):
                        x1,y1=(len(self.square_grid[row]))*BOX,row*BOX
                        x2,y2=x1+BOX,y1+BOX
                        b = self.canvas.create_rectangle(x1,y1,x2,y2,fill="#FFFFFF")
                        self.square_grid[row].append(b)
                        self.values_grid[row].append('s')                
            elif self.col_value.get() < len(self.square_grid[0]):#print('decreased cols')
                for row in range(self.row_value.get()):
                    for y in range(len(self.square_grid[0])-self.col_value.get()):
                        self.square_grid[row].pop()
                        self.values_grid[row].pop()      
        self.canvas.config(width=(self.col_value.get()*BOX)-1)
        self.canvas.config(height=(self.row_value.get()*BOX)-1)
        
        winwidth = BASE_W_OFFSET if BASE_W_OFFSET > (self.col_value.get()*BOX)+43 else (self.col_value.get()*BOX)+43  
        winheight = (self.row_value.get()*BOX) + BASE_H_OFFSET+3
        if os.name=='nt':
            self.master.geometry(f'{winwidth}x{winheight}')
        else:
            self.master.geometry(f'{winwidth+190}x{winheight+20}')
            
    def on_square_clicked(self,event):
        self.coords['x'] = event.x//BOX
        self.coords['y'] = event.y//BOX
 
    def on_square_release(self,event):
        self.coords['x2'] = event.x//BOX
        self.coords['y2'] = event.y//BOX
        try:
            self.toggle_cells()
        except Exception as e:
            print(e)
            
    def toggle_cells(self):
        if self.coords['x'] == self.coords['x2'] and self.coords['y']==self.coords['y2']:
            if self.values_grid[self.coords['y']][self.coords['x']]!="#":
                self.values_grid[self.coords['y']][self.coords['x']]="#"
                self.canvas.itemconfig(self.square_grid[self.coords['y']][self.coords['x']],fill='black')
            elif self.values_grid[self.coords['y']][self.coords['x']]!="s":
                self.values_grid[self.coords['y']][self.coords['x']]="s"
                self.canvas.itemconfig(self.square_grid[self.coords['y']][self.coords['x']],fill='white')
        elif self.coords['y'] == self.coords['y2'] and self.coords['x']!= self.coords['x2']:
            if(self.coords['x2']>self.coords['x']):
                for i in range(self.coords['x'],self.coords['x2']+1):
                    if self.values_grid[self.coords['y']][i]!="#":
                        self.values_grid[self.coords['y']][i]="#"
                        self.canvas.itemconfig(self.square_grid[self.coords['y']][i],fill='black')
                    elif self.values_grid[self.coords['y']][i]!="s":
                        self.values_grid[self.coords['y']][i]="s"
                        self.canvas.itemconfig(self.square_grid[self.coords['y']][i],fill='white')
            else:
                for i in range(self.coords['x2'],self.coords['x']+1):
                    if self.values_grid[self.coords['y']][i]!="#":
                        self.values_grid[self.coords['y']][i]="#"
                        self.canvas.itemconfig(self.square_grid[self.coords['y']][i],fill='black')
                    elif self.values_grid[self.coords['y']][i]!="s":
                        self.values_grid[self.coords['y']][i]="s"
                        self.canvas.itemconfig(self.square_grid[self.coords['y']][i],fill='white')     
        elif self.coords['x'] == self.coords['x2'] and self.coords['y']!=self.coords['y2']:
            if(self.coords['y2']>self.coords['y']):
                for i in range(self.coords['y'],self.coords['y2']+1):
                    if self.values_grid[i][self.coords['x']]!="#":
                        self.values_grid[i][self.coords['x']]="#"
                        self.canvas.itemconfig(self.square_grid[i][self.coords['x']],fill='black')
                    elif self.values_grid[i][self.coords['x']]!="s":
                        self.values_grid[i][self.coords['x']]="s"
                        self.canvas.itemconfig(self.square_grid[i][self.coords['x']],fill='white')
            else:
                for i in range(self.coords['y2'],self.coords['y']+1):
                    if self.values_grid[i][self.coords['x']]!="#":
                        self.values_grid[i][self.coords['x']]="#"
                        self.canvas.itemconfig(self.square_grid[i][self.coords['x']],fill='black')
                    elif self.values_grid[i][self.coords['x']]!="s":
                        self.values_grid[i][self.coords['x']]="s"
                        self.canvas.itemconfig(self.square_grid[i][self.coords['x']],fill='white')
           
    def export_to_file(self,event):
        def save(*args):
            if filename.get()=='':
                print('no filename')
            else:
                js_ob = {
                'name':filename.get(),
                'appearsin':[ x for x in range(int(self.fl_lower.get()),int(self.fl_upper.get())+1)],
                'entrance_pos':self.entrance,
                'exit_pos':self.exit,
                'available_mobs':[e for e in self.ENEMY_NAMES if self.ENEMY_NAMES[e].get()==True],
                'floor':self.values_grid,
                'background':self.bg_color,
                'foreground':self.fg_color
                }
                with open('./src/levels/'+filename.get()+'.json','w+') as outfile:
                    json.dump(js_ob,outfile)
                tk.messagebox.Message(title='',message='File Written Successfully').show()
                tl.destroy()
                
        tl = tk.Toplevel(self)
        tl.grab_set()
        tl.resizable(0,0)
        tl.geometry(f"+{self.master.winfo_x()+(event.x)}+{self.master.winfo_y()+event.y}")
        f = tk.Frame(tl)
        f.grid(padx=10,pady=10)
        tk.Label(f,text='Enter a file to save to:').grid(row=0,column=0)
        filename = tk.Entry(f,textvariable=self.fn)
        filename.grid(row=0,column=1)
        tk.Button(f,text='Save',command=save).grid(column=0,row=1,columnspan=2,sticky='we')
        
    def load_from_file(self,event):
        fn = tk.filedialog.askopenfilename(initialdir='./src/levels')
        if not fn.endswith('.json'):
            return
        with open(fn,'r') as f:
            obj = json.load(f)
        command_colors={
            "m":"red",
            "c":"brown",
            "g":'yellow',
            "d":'slate grey',
            "?":'lightgrey',
            "$":'green',
            ".":'blue',
            "!":'aqua',
            "|":'gray18',
            "#":'black',
            's':'white'
            }
        self.fn.set(fn.split('/')[-1][:-5])        #filename
        self.master.title(self.fn.get())
        self.fl_lower.set(obj['appearsin'][0])     #starting floors
        self.fl_upper.set(obj['appearsin'][-1])    #ending floors
        self.col_value.set(len(obj['floor'][0]))   #columns
        self.on_resize("")                      
        self.row_value.set(len(obj['floor']))      #rows
        self.on_resize("")
        self.values_grid=obj['floor']              #floor shape
        for x in self.ENEMY_NAMES:                 #set mobs
            if x in obj['available_mobs']:
                self.ENEMY_NAMES[x].set(True)
        for row in range(len(self.values_grid)):
            for col in range(len(self.values_grid[0])):
                self.canvas.itemconfig(self.square_grid[row][col],fill=command_colors[self.values_grid[row][col]])
        self.bg_color=obj['background']
        self.fg_color=obj['foreground']
        self.cv.itemconfig(self.cv_bg,fill=obj['background'])
        self.cv.itemconfig(self.cv_fg,fill=obj['foreground'])
        return "break"

def OpenNew():
    root = tk.Tk()
    root.eval("tk::PlaceWindow %s center" %root.winfo_pathname(root.winfo_id()))
    root.geometry('250x250')
    #root.resizable(0,0)
    root.title("")
    app =Editor(root)
    app.mainloop()
    
if __name__=="__main__":
    root = tk.Tk()
    root.eval("tk::PlaceWindow %s center" %root.winfo_pathname(root.winfo_id()))
    root.geometry('250x250')
    root.resizable(0,0)
    root.title("")
    app =Editor(root)
    app.mainloop()
