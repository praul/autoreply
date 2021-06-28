

from email import message_from_bytes
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
from os import execlp
from subprocess import call
from textwrap import dedent
from time import sleep
import sqlite3
from datetime import datetime, timedelta
import time
import sys
import emails

__author__ = 'praul'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AutoReplyer:
    con = None
    cur = None
    v = None
    timeout = None
    intime = True

    def __init__(self, v):               
        self.v = v
        self.timeout = self.v["refresh_delay"]
        self.login_imap()
        self.run()
        
    
    def login_imap(self):
        if self.v["imap_use_ssl"]:
            self.imap = IMAP4_SSL(self.v["imap_server"], self.v["imap_ssl_port"])
        else:
            self.imap = IMAP4(self.v["imap_server"], self.v["imap_port"])
        self.imap.login(self.v["imap_user"], self.v["imap_password"])
    
    def close_imap(self):
        self.imap.logout()
    
    def cprint(self, text):
        print(bcolors.OKGREEN + self.v["mymail"] + bcolors.ENDC +  ": " + str(text) )

    def sender_check(self, sender):
        self.cprint ('------> Incoming mail from ' + sender + '. Checking history....')
        
        #Check for mail from self
        if (sender in self.v["mymail"]):
            self.cprint ('Mail from self. Not sending any mail')
            return False

        #Check for noreply
        if ('noreply' in sender ):
            self.cprint ('Mail from noreply. Not sending any mail')
            return False

        #Check for recent incoming mails from this adress
        self.db_connect()
        send = True; breakdate = datetime.now() - timedelta(hours=self.v["blockhours"])
        for row in self.cur.execute("SELECT id,date FROM senders WHERE mail=?", (sender,)):
            then = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")            
            self.cprint ('Found ' + sender + ' at ' + str(row[1]) + ' - ID ' + str(row[0]))
            if (then < breakdate):  #If older: Delete
                self.cprint ('Last entry ' + str(row[0]) +  ' from ' + sender + ' is old. Delete...' )
                self.cur.execute("DELETE FROM senders WHERE id=?", (str(row[0])))
            elif (then >= breakdate): #If Recent: Reject
                self.cprint ('Recent entry found. Not sending any mail' )
                send = False
        
        if (send == False): return False      
        return True
    
    def datetime_check(self):
        start = datetime.strptime(self.v["datetime_start"], "%Y-%m-%d %H:%M")  
        end = datetime.strptime(self.v["datetime_end"], "%Y-%m-%d %H:%M")  
        if (datetime.now() >= start and datetime.now() <= end):
            if (self.intime == False):
                self.timeout = self.v["refresh_delay"]
                self.cprint('In date range. Autoreply responding...')
                self.intime = True
            return True
        else:
            if (self.intime == True):
                self.timeout = 60 #increase Timeout 
                self.cprint('Not in date range. Autoreply sleeping...')
                self.intime = False
            return False

    def sender_memorize(self,sender):
        self.db_connect()
        self.cprint ('Memorizing ' + sender)
        self.cur.execute("INSERT INTO senders (mail, date) values (?, ?)", (sender, datetime.now() ) )
        self.con.commit()
        self.con.close()
        

    def db_connect(self):
        db = "./db/autoreply-" + self.v["identifier"] + ".db"
        self.con = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.con.cursor()
        

    def create_table(self):
        self.db_connect()
        try: self.cur.execute('''CREATE TABLE senders (id INTEGER PRIMARY KEY, mail text, date datetime)''')  
        except: pass      
        self.con.commit(); self.con.close()    
    
    def create_auto_reply(self, original):  
        message = emails.html(  html= self.v["body_html"],
                                text= self.v["body"],
                                subject= 'Re: ' + original['Subject'],
                                mail_from= self.v["from_address"],                             
                             )
        return message


    def send_auto_reply(self, original):
        sender_full = original['From']
        try: sender = (sender_full.split('<'))[1].split('>')[0]
        except: sender = sender_full
             
        #Check if a response needs to be sent
        if (self.sender_check(sender) != True): return
        self.cprint('Sending a response...')
        
        #Send with basic error prevention
        success = False
        for i in range(10):
            if (success != True):
                message = self.create_auto_reply(original)
                try:
                    r = message.send(   to= (sender),
                                    smtp= {'host': self.v["smtp_server"], 'port': self.v["smtp_port"], 'ssl': self.v["smtp_use_ssl"], 'user': self.v["smtp_user"], 'password': self.v["smtp_password"]}
                                )
                    assert r.status_code == 250
                    success = True
                except:
                    self.cprint ('Error on send: ' + str(r))
                    if (r.status_code == 550):
                        self.cprint('Mailbox unavailable')
                        return
                    self.cprint('  Wait 10s and retry...')
                    time.sleep(10) 
        
        if (success==True): 
            self.cprint('Successfully replied')
            self.sender_memorize(sender)
        

    def reply(self, mail_number):
        self.imap.select(readonly=True)
        _, data = self.imap.fetch(mail_number, '(RFC822)')
        self.imap.close()
        
        self.send_auto_reply(message_from_bytes(data[0][1]))
        self.imap.select(readonly=False)
        self.imap.store(mail_number, '+FLAGS', '\\Answered')
        self.imap.close()

    def check_mails(self):
        self.imap.select(readonly=False)
        _, data = self.imap.search(None, '(UNSEEN UNANSWERED)')
        self.imap.close()
        for mail_number in data[0].split():
            self.reply(mail_number)
            time.sleep(1) #Rate Limit

    def run(self):
        self.create_table()
        self.cprint ('Autoreply started... Blocking rebounds for ' + str(self.v["blockhours"]) + ' hours')        
        
        try:
            while True:
                if (self.datetime_check() == True): self.check_mails()
                sleep(self.v["refresh_delay"])
        except: 
            e = sys.exc_info()[0]
            print (e)

        
    
        
      
            
