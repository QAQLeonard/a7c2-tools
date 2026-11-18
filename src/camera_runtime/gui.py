"""Small Windows front end. Worker commands remain independently reviewable."""
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog,messagebox,ttk

BASE=Path(__file__).resolve().parent

def main():
    root=tk.Tk();root.title('A7C II · FL2 / FL3 preview');root.geometry('780x620')
    root.minsize(720,540);q=queue.Queue();running=[False]
    work=tk.StringVar();backup=tk.StringVar();battery=tk.StringVar();version=tk.StringVar()
    wrap=ttk.Frame(root,padding=22);wrap.pack(fill='both',expand=True)
    ttk.Label(wrap,text='A7C II · FL2 / FL3',font=('Microsoft JhengHei UI',22,'bold')).pack(anchor='w')
    ttk.Label(wrap,text='A7C II 2.01 | firmware origin not checked | development build, not yet verified on a camera',wraplength=700).pack(anchor='w',pady=(5,14))
    ttk.Label(wrap,text='Firmware modified outside this repository may conflict. Back up first; if FL23 is already enabled it will not be installed again.',wraplength=700).pack(anchor='w',pady=(0,12))
    controls=[]
    for title,var in [('Body workspace folder (choose an empty folder the first time)',work),('Second backup (an empty folder on another drive is recommended)',backup)]:
        ttk.Label(wrap,text=title).pack(anchor='w')
        row=ttk.Frame(wrap);row.pack(fill='x',pady=(3,9))
        entry=ttk.Entry(row,textvariable=var);entry.pack(side='left',fill='x',expand=True)
        def choose(v=var):
            path=filedialog.askdirectory()
            if path:v.set(path)
        button=ttk.Button(row,text='Browse',command=choose);button.pack(side='left',padx=(8,0));controls.extend([entry,button])
    row=ttk.Frame(wrap);row.pack(fill='x',pady=(0,12))
    ttk.Label(row,text='Current camera battery: ').pack(side='left')
    entry=ttk.Entry(row,width=7,textvariable=battery);entry.pack(side='left')
    ttk.Label(row,text='%   Writing needs at least 50%; keep USB connected throughout.').pack(side='left');controls.append(entry)
    row=ttk.Frame(wrap);row.pack(fill='x',pady=(0,8))
    ttk.Label(row,text='Camera firmware version (as shown on the camera version page): ').pack(side='left')
    entry=ttk.Entry(row,width=8,textvariable=version);entry.pack(side='left');controls.append(entry)
    status=tk.StringVar(value='Read the instructions first and make sure drivers for both USB identities are ready.')
    ttk.Label(wrap,textvariable=status,wraplength=700).pack(anchor='w',pady=(0,8))
    progress=ttk.Progressbar(wrap,mode='indeterminate');progress.pack(fill='x')
    buttons=ttk.Frame(wrap);buttons.pack(fill='x',pady=12)
    log=tk.Text(wrap,height=13,wrap='word',state='disabled',font=('Microsoft JhengHei UI',10));log.pack(fill='both',expand=True)
    def run(command):
        if running[0]:return
        if not work.get():messagebox.showinfo('Choose workspace','Choose a body workspace folder first.');return
        cmd=[sys.executable,'-u',str(BASE/'app.py'),command,'--workspace',work.get()]
        if command=='prepare':
            if not backup.get():messagebox.showinfo('Choose backup folder','Choose a second backup folder first.');return
            if version.get().strip()!='2.01':messagebox.showinfo('Camera firmware version','This tool supports 2.01 only; check the camera version page and enter it first.');return
            cmd+=['--backup-copy',backup.get(),'--firmware-version',version.get().strip()]
        if command=='install':
            try:value=int(battery.get())
            except ValueError:value=-1
            if not 50<=value<=100:messagebox.showinfo('Confirm battery','Enter the actual battery level; at least 50% is required.');return
            cmd+=['--battery-percent',str(value)]
        if command=='install':
            messagebox.showwarning('Firmware compatibility warning','Firmware origin is not verified. Firmware modified outside this repository may conflict with FL23 and stop the camera from starting normally. Keep this computer\'s backups.')
        running[0]=True;progress.start(12);status.set('Working; do not unplug the cable, power off or close the window.')
        for c in controls:c.configure(state='disabled')
        def worker():
            try:
                env=dict(os.environ,PYTHONIOENCODING='utf-8')
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                with subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
                                      encoding='utf-8',errors='replace',env=env,cwd=BASE,creationflags=flags) as process:
                    for line in process.stdout:q.put(('log',line))
                    q.put(('done',process.wait()))
            except Exception as exc:q.put(('log',str(exc)+'\n'));q.put(('done',1))
        threading.Thread(target=worker,daemon=True).start()
    for title,command in [('1 Back up and check','prepare'),('2 Install preview','install'),('3 Verify after restart','verify')]:
        button=ttk.Button(buttons,text=title,command=lambda c=command:run(c));button.pack(side='left',padx=(0,7));controls.append(button)
    def tick():
        try:
            while True:
                kind,value=q.get_nowait()
                if kind=='log':log.configure(state='normal');log.insert('end',value);log.see('end');log.configure(state='disabled')
                else:
                    running[0]=False;progress.stop()
                    for c in controls:c.configure(state='normal')
                    status.set('Done. Read the results and next steps below.' if value==0 else 'Stopped. Keep the workspace and check the state using the error message; do not blindly re-run writes.')
        except queue.Empty:pass
        root.after(100,tick)
    def close():
        if running[0]:messagebox.showinfo('Still working','The read/write process has not finished; wait for the result.')
        else:root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);tick();root.mainloop()
if __name__=='__main__':main()
