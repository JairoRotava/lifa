# Monitor de arquivos Licel para apresentacao de dados

import tkinter as tk
from tkinter import ttk
#import ttkthemes

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from matplotlib.backend_bases import key_press_handler

from matplotlib.figure import Figure

import glob
import os
import fames
import fames.files
import fames.report
import tempfile

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Title, icon, size
        self.title("FAMES Monitor")
        #self.iconbitmap('images/codemy.ico')
        self.geometry('700x450')

        #('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')        
        #ttk.Style().theme_use('xpnative')
        
        import os

        # Find the directory we executed the script from:
        execution_dir = os.getcwd()
        # Find the directory in which the current script resides:
        file_dir = os.path.dirname(os.path.realpath(__file__))

        # Load  theme
        self.tk.call('lappend', 'auto_path', os.path.join(file_dir, 'awthemes-10.4.0'))
        self.tk.call('package', 'require', 'awlight')

        #s = ttk.Style()
        #print(s.theme_names())
        #ttk.Style().theme_use('awlight')

        # Create Status Variable
        self.status = True
        self.status_bar = tk.StringVar()
        self.status_bar.set("Monitoring folder not selected")
        self.monitor_dir = None
        self.temp_dir = os.path.join(file_dir, 'temp')
        #self.temp_dir = tempfile.mkdtemp()
        print("Temporary folder:: " + self.temp_dir)
        self.dados = None
        self.files = []
        self.processed_files = []
        #slider = tk.StringVar()
        #slider.set('0')
        self.scale_pos = tk.IntVar()

        content = ttk.Frame(self)
        content.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=4, pady=4)
        

        self.fig = Figure(figsize=(9, 5), dpi=100, layout='constrained')
        
        self.dashboard = fames.report.create_simple_dashboard(self.fig)

        self.canvas = FigureCanvasTkAgg(self.fig, content)  # A tk.DrawingArea.
        #self.canvas.draw()
        #self.canvas.draw()
        #canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.canvas.get_tk_widget().grid(column=0, row=0, padx=4, pady=4, columnspan=6, sticky=(tk.N, tk.S, tk.E, tk.W))
		
        #canvas = tk.Canvas(self).grid(column=0, row=0, sticky=(tk.W))
		
        self.button = ttk.Button(content, text="Select Folder", command=self.select_folder)
        self.button.grid(column=0, row=1, sticky=(tk.W))
        #self.scale = ttk.Scale(content, orient=tk.HORIZONTAL, from_=0, to_=2, length=300, command=lambda s:slider.set('%d' % float(s))).grid(column=1, row=1, sticky=(tk.W))
        self.scale = tk.Scale(content, orient=tk.HORIZONTAL, from_=1, to_=1, command=self.scale_event, tickinterval=1, length=300, variable=self.scale_pos)
        self.scale.grid(column=1, row=1, sticky=(tk.W))
        self.scale.config(state='disabled')
        #self.scale_label = ttk.Label(content, textvariable=slider)
        #self.scale_label.grid(column=2, row=1)
        self.label = ttk.Label(content, textvariable=self.status_bar)
        self.label.grid(column=0, row=2, sticky=(tk.W), columnspan=4)

        #print(self.scale)
        
		
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=3)
        content.columnconfigure(2, weight=3)
        content.columnconfigure(3, weight=1)
        content.rowconfigure(0, weight=1)

        # Create some widgets
        #self.my_label = tk.Label(self, text="Hello World!", font=("Helvetica", 42))
        #self.my_label.pack(pady=20)

        #self.my_button = tk.Button(self, text="Change Text", command=self.change)
        #self.my_button.pack(pady=20)

        # Create a frame outside this function
        #My_frame(self)
        self.refresh_files()

    def scale_event(self, v):
        #fames.report.update_simple_dashboard(self.dashboard, self.dados, int(v)-1)
        #self.canvas.draw_idle()
        self.update_dash(int(v)-1)
        
    def update_scale(self):
        if self.scale.get() == self.scale.cget('to'):
            end_of_scale = True
        else:
            end_of_scale = False

    
        tick_interval = 1
        if (len(self.dados.index)/1) > 10:
            tick_interval = int((len(self.dados.index)/10))
        
        self.scale.config(state='normal', from_=1, to=len(self.dados.index), tickinterval=tick_interval)
        
        # mantem curso no fim da escala caso ela estava antes do update.
        if end_of_scale:
            self.scale.set(self.scale.cget('to'))
        #if self.scale.get() == len(self.dados.index) - 1:
        #    self.scale.set(len(self.dados.index))     





    def select_folder(self):
        #self.monitor_dir = tk.filedialog.askdirectory()
        new_dir = tk.filedialog.askdirectory()
        if os.path.isdir(new_dir):
            self.monitor_dir = new_dir
            self.status_bar.set("Monitoring {}".format(self.monitor_dir))
            #self.temp_dir = './temp'
            self.files = []
            self.processed_files = []
            if self.find_new_files():
                self.update_scale()
                # Atualiza grafico
                #fames.report.update_simple_dashboard(self.dashboard, self.dados)
                #self.canvas.draw()
                self.update_dash(self.scale.get()-1)
                



    def update_dash(self, v=-1):
        fames.report.update_simple_dashboard(self.dashboard, self.dados, v)
        self.canvas.draw_idle()

    def change(self):
        if self.status == True:
            self.my_label.config(text="Goodbye World!")
            self.status = False
        else:
            self.my_label.config(text="Hello World!")
            self.status = True

    def refresh_files(self):
        if self.monitor_dir is not None:
            if self.find_new_files():
                self.update_scale()
                self.update_dash(self.scale_pos.get()-1)
        self.after(5000, self.refresh_files)

    def find_new_files(self):
        # Procura por novos aquivos
        print("Checking for new files in {}".format(self.monitor_dir))
        files = glob.glob(os.path.join(self.monitor_dir,'a???????.??????'))
        new_file = False
        for file in files:
            if os.path.isfile(file):
                if file not in self.files:
                    processed_file = os.path.join(self.temp_dir,os.path.basename(file) + '.fames')
                    self.files.append(file)
                    print(file, processed_file)
                    #fames.files.process_licel(file, processed_file)
                    try:
                        #fames.files.process_licel(file, processed_file)
                        fames.files.process_emissions(file, processed_file)
                    except:
                        print("Error processing {}".format(file))
                    else:
                        self.processed_files.append(processed_file)
                        new_file = True



        if new_file:
            #print(f'New file(s) found')
            #pega lista de arquivos fames
            #processed_files = glob.glob(os.path.join(self.temp_dir,'*.fames'))  
            self.dados = fames.files.read_processed(self.processed_files)
            #print(self.dados['start_time'])
            #scale.configure(to=len(dados.index), tickinterval=len(dados.index)-1)
            # Plota
            #global scale_var
            # mantem apresenetação de ultima aquisiacao
            #print(scale.get(), len(dados.index))
            #if scale.get() == len(dados.index)-1:
            #    scale.set(len(dados.index))

            #fames.report.update_simple_dashboard(dashboard, dados, scale_var.get() -1)
            #canvas.draw()
        return new_file    
        #root.after(5000, update_function) # run itself again after 100 ms

#class My_frame(tk.Frame):
#    def __init__(self, parent):
#        super().__init__(parent)

        # Put this sucker on the screen
        #self.pack(pady=20)
        # Create a few buttons
        #self.my_button1 = tk.Button(self, text="Change", command=parent.change)
        #self.my_button2 = tk.Button(self, text="Change", command=parent.change)
        #self.my_button3 = tk.Button(self, text="Change", command=parent.change)

        #self.my_button1.grid(row=0, column=0, padx=10)
        #self.my_button2.grid(row=0, column=1, padx=10)
        #self.my_button3.grid(row=0, column=2, padx=10)

# Define and instantiate our app
if __name__ == "__main__":
    app = App()
    app.mainloop()