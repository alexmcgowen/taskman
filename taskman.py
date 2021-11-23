# Modules
import sqlite3
import pandas as pd
import os
import warnings
import numpy as np
warnings.filterwarnings("ignore")
import shlex
import datetime
from prettytable import from_db_cursor

# Get Dates
from datetime import date
today_dt = date.today()
tod = today = today_dt.strftime('%Y-%m-%d')
from datetime import timedelta
tom_dt = today_dt + timedelta(days=1)
tom = tomorrow = tom_dt.strftime('%Y-%m-%d')
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Connect & set up Database
con = sqlite3.connect('taskman.db')
cur = con.cursor()

# Create Query function
"""
def query(sql):
        dfr = pd.read_sql_query(sql, con)
        if dfr.size == 0:
                print("\nNo matches, add some tasks or update your filter!\n")
        else:
                results = dfr.to_string(index=False)
                print('\n'+results+'\n')
"""
def query(sql):
        cur.execute(sql)
        mytable = from_db_cursor(cur)
        mytable.align = 'l'
        print('\n')
        print(mytable)
        print('\n')

# Create execute & commit function
def execute(sql):
    cur.execute(sql)
    con.commit()

# Attributes
attributes = ['#:','mid:','p:','due:','@:','desc:','contacts:','tags:']
optTaskCols = ['#:','mid:','due:','@:','desc:','contacts:','tags:']

# Create CMD-to-Column dictionary
cmd2col = {
    '#:':'PID',
    'mid:':'MID',
    'p:':'Priority',
    'due:':'Due',
    '@:':'Status',
    'desc:':'Description',
    'contacts:':'Contacts',
    'tags:':'Tags'
    }

# Create Flags function
def createFlags(cmd,branch):
        flags = cmd[cmd.find(branch):][1:].split(':') # replace ' mod' with a function input!
        c = 0
        KVPs = []
        while c < len(flags):
                if c == 0:
                        k = flags[c].split(' ')[-1]

                elif (c + 1) < len(flags):
                        v = ' '.join(flags[c].split(' ')[:-1])
                        KVPs.append(k+':'+v)
                        k = flags[c].split(' ')[-1]
                else:
                        v = flags[c]
                        KVPs.append(k+':'+v)
                c += 1
        return(KVPs)

# Natural Language Processor
def natLang(ip):
    op = ip
    if ip == 'tod':
        op = tod
    if ip == 'today':
        op = tod
    if ip == 'tom':
        op = tom
    return op

# Modify Task function
"""
def modTask(TID, flags, log):
    for f in flags:
        for a in attributes: # figure out how to deal with adding descriptions...
            if a in f: # need to be able to add project by name or PID
                    ip = f.split(':')[1]
                    val = natLang(ip)
                    execute("update tasks set "+cmd2col[a]+" = '"+val+"' where TID = "+str(TID)+";")
                    if log == True: # log the change with an activity function
                            pass
"""
def modTask(TID, KVPs, log):
    for i in KVPs:
        for a in attributes: # figure out how to deal with adding descriptions...
            if a in i: # need to be able to add project by name or PID
                    ip = i.split(':')[1]
                    val = natLang(ip)
                    execute("update tasks set "+cmd2col[a]+" = '"+val+"' where TID = "+str(TID)+";")
                    if log == True: # log the change with an activity function
                            pass

# Activity Log Function
def activity():
    pass

# Filter Tasks Function
def taskFilter(cmdList):
    filters = cmdList[1:]
    if filters[0] == 'list':
        TIDs = []
        for i in con.execute('select TID from tasks'):
            TIDs.append(i[0])
        TIDs = tuple(TIDs)
    elif ':' in filters[0]:
        TIDs = []
        q = "select TID from tasks where TID > 0"
        for f in filters:
            for a in attributes:
                if a in f:
                        ip = f.split(':')[1]
                        val = natLang(ip)
                        if ',' in val:
                                vals = tuple(val.split(','))
                                q = q + " and "+cmd2col[a]+" in "+str(vals)
                        else:
                                q = q + " and "+cmd2col[a]+" = '"+val+"'" # add an if/else statement for if a comma is in the value
        for i in con.execute(q):
            TIDs.append(i[0])
        TIDs = tuple(TIDs)
    else:
        TIDs = tuple(filters[0].split(','))
    return TIDs

# Help Text
help_text = '''
PROGRAM COMMANDS
----------------
   help      print this menu
   clear     clear the terminal
   exit      exit the program

TASK LIST COMMANDS
------------------
   query     query the database
             > query:select count(*) from tasks
             
   list      list tasks that meet filter criteria
             > task p:1 @:Next list
             
   search    list tasks that match a string
             > task search:read

TASK COMMANDS
-------------
   add       add a task
             > task add Oil Change due:tod
             
   mod[ify]  change filtered task attributes
             > task due:tod mod due:tom
             
   done      mark a task as complete
             > task 1,2 done
             
   delete    mark a task as deleted
             > task #:2 delete

PROJECT COMMANDS
----------------
   add       create a project
             > project add Japan Trip
             
   list      list all projects
             > project list
'''

# Create Tables (Setup Routine)
def setup(con,cur):
        cur.execute('''
        create table if not exists tasks (
            TID integer primary key,
            Task text not null,
            PID integer not null,
            MID integer,
            Priority integer not null,
            Due text,
            Status text,
            Closed text,
            Description text,
            Contacts text,
            Tags text);
        ''')

        cur.execute('''
        create table if not exists projects (
            PID integer primary key,
            Project text not null,
            Status text);
        ''')

        for i in con.execute("select count(*) from projects where Project = 'Inbox';"): # Ensure there is an 'Inbox' project on the table
            c = i
        if c[0] == 0:
            cur.execute("insert into projects values (0,'Inbox','')")
            con.commit()

        cur.execute('''
        create table if not exists meetings (
            MID integer primary key,
            Meeting text not null);
        ''')

        cur.execute('''
        create table if not exists calendar (
            EID integer primary key,
            MID integer,
            Datetime text,
            Notes text);
        ''')

        cur.execute('''
        create table if not exists comments (
            CID integer primary key,
            TID integer not null,
            Datetime text,
            Comment text);
        ''')

        cur.execute('''
        create table if not exists activities (
            AID integer primary key,
            TID integer,
            CID integer,
            EID integer,
            PID integer,
            MID integer,
            Datetime text not null,
            Action text not null,
            Attribute text,
            Change text);
        ''')

        con.commit()
        
setup(con,cur)

# Main Loop
print('+---------+')
print('| TASKMAN |')
print('+---------+\n')

run = True
while run == True:
        valid = False
        cmd = input('> ')
        cmdList = cmd.split(' ')
        if cmdList[0] == 'help':
                valid = True
                print(help_text)
        if cmd[0:6] == "query:":
                valid = True
                query(cmd.split(":")[1])
        if cmdList[0] == 'clear':
                valid = True
                os.system('cls' if os.name == 'nt' else 'clear')
        if cmd == 'format':
                valid = True
                confirm = input("Are you SURE you want to format the database (y/n)? ")
                if confirm == 'y':
                        con.close() #close db connection
                        os.remove('taskman.db') # delete database
                        con = sqlite3.connect('taskman.db')
                        cur = con.cursor()
                        setup(con,cur) # recreate database
        if cmd == 'exit':
                valid = True
                con.close()
                print("Goodbye")
                quit()

# SEARCH BLOCK
        if cmd[0:12] == "task search:":
                valid = True
                string = cmd.split(':')[1]
                query("select * from tasks where lower(Task) like lower('%"+string+"%') or lower(Description) like lower('%"+string+"%') or lower(Contacts) like lower('%"+string+"%') or lower(Tags) like lower('%"+string+"%')")
        
# TASK ADD BLOCK
        if cmdList[0] == 'task' and cmdList[1] == 'add':
                valid = True
                flags = cmdList[2:]
                task = ''
                cont = True
                for f in flags:
                        if ':' not in f and cont == True:
                                task = task + ' ' + f
                        else:
                                cont = False
                task = task[1:]
                for i in con.execute('select count(*) from tasks;'):
                    count = i
                TID = count[0] + 1
                execute("insert into tasks values ("+str(TID)+",'"+task+"',0,-1,1,'','Open','','','','')")
                #query("select * from tasks where TID = '"+str(TID)+"'") # confirm correct info on start
                flags = cmd.split(' ') # CHANGE FLAGS TO KVPS FROM NEW FUNCTION
                KVPs = createFlags(cmd,'add')
                #modTask(TID,flags,False) # false means don't log these changes
                modTask(TID,KVPs,False) # false means don't log these changes
                print('created task:')
                query("select TID, Task, Project, MID, Priority, Due, p.Status, Description, Contacts, Tags from tasks t left join projects p on t.PID = p.PID where TID = '"+str(TID)+"'")
                
# TASK LIST BLOCK
        if cmdList[0] == 'task' and cmdList[1] != 'add' and ' list' in cmd:
                valid = True
                TIDs = taskFilter(cmdList)
                if len(TIDs) == 1:
                        TIDs = '('+str(TIDs[0])+')'
                query("select TID, Task, Project, MID, Priority, Due, t.Status, Description, Contacts, Tags from tasks t left join projects p on t.PID = p.PID where t.Status not in ('Done','Deleted') and TID in "+str(TIDs))
                
# TASK MODIFY BLOCK
        #if cmdList[0] == 'task' and cmdList[1] != 'add' and (' mod' in cmd or ' modify' in cmd):
        #        valid = True
        #        filters = cmd[:cmd.find(' mod')].split(' ')
        #        TIDs = taskFilter(filters)
        #        flags = cmd[cmd.find(' mod'):].split(' ')
        #        for TID in TIDs:
        #            modTask(TID,flags,False)

        if cmdList[0] == 'task' and cmdList[1] != 'add' and (' mod' in cmd or ' modify' in cmd):
                valid = True
                filters = cmd[:cmd.find(' mod')].split(' ')
                TIDs = taskFilter(filters)
                KVPs = createFlags(cmd,' mod')
                for TID in TIDs:
                    modTask(TID,KVPs,False)

# TASK DONE BLOCK
        if cmdList[0] == 'task' and cmdList[1] != 'add' and ' done' in cmd:
                valid = True
                filters = cmd[:cmd.find(' done')].split(' ')
                TIDs = taskFilter(filters)
                for TID in TIDs:
                        execute("update tasks set Status = 'Done' where TID = "+str(TID)+";")
                        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        execute("update tasks set Closed = '"+now+"' where TID = "+str(TID)+";")

# TASK DELETE BLOCK
        if cmdList[0] == 'task' and cmdList[1] != 'add' and ' delete' in cmd:
                valid = True
                filters = cmd[:cmd.find(' delete')].split(' ')
                TIDs = taskFilter(filters)
                for TID in TIDs:
                        execute("update tasks set Status = 'Deleted' where TID = "+str(TID)+";")
                        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        execute("update tasks set Closed = '"+now+"' where TID = "+str(TID)+";")
                
# PROJECT ADD BLOCK
        if cmdList[0] == 'project' and cmdList[1] == 'add':
                valid = True
                words = cmdList[2:]
                pName = ''
                for w in words:
                        pName = pName + ' ' + w
                for i in con.execute('select count(*) from projects;'):
                    count = i
                PID = count[0]
                execute("insert into projects values ("+str(PID)+",'"+pName+"','')")
                print('created project:')
                query("select PID, Project from projects where PID = '"+str(PID)+"'")
                
# PROJECT LIST BLOCK
        if cmdList[0] == 'project' and cmdList[1] == 'list':
                valid = True
                query('select PID, Project from projects')

# ELSE BLOCK
        if valid == False:
                print("\nCommand not recognized, try again or use 'help' command.\n")
        
            
