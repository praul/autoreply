import email
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
import sqlite3
from datetime import date, datetime, timedelta
import time
import sys
import re
import emails

__author__ = 'praul'


class AutoReplyer:
    db_con = None
    db_cur = None
    
    program_timeout = None
    program_date_active = None
    program_timezone = None
   
    mail_ignorelist = []
    mail_isloggedin = False
    mail_lastcheck = None
    
    v = None
    debug = False
    version = '0.52'

    class Mailmessage:
        msg = None
        msg_id = None
        msg_sender = None
        msg_date = None
        msg_number = None

        has_msg_id = False
        sent = False
        debug = False

        def __init__(self, data, mail_number, debug=False):
            self.msg_number = mail_number
            self.msg = self.get_message(data)
            self.msg_id = self.get_messageid(self.msg) 
            self.sender = self.get_sender(self.msg)

        def get_message(self, data):
            msg = email.message_from_bytes(data[0][1])
            return msg

        def get_messageid(self, msg):
            for header in ['Message-ID']:
                if (msg[header] is not None):
                    messageid = str(msg[header]).replace('<', '').replace('>','').replace("\n", "").replace("\r", "")
                    self.has_msg_id = True
                    return messageid
            return 'no-message-id'
           
        def get_sender(self,msg):
            sender_full = msg['From']
            try: sender = (sender_full.split('<'))[1].split('>')[0]
            except: sender = sender_full
            return str(sender)
    
    def __init__(self, v):               
        self.v = v
        self.program_timeout = self.v["refresh_delay"]
        try: self.v["mode"] = self.v["mode"]
        except: self.v["mode"] = 'reply'
        try: self.debug = self.v['debug']
        except: self.debug = False       

        self.mail_lastcheck = datetime.utcnow() - timedelta(minutes=20)
        
        self.run()

    def debug_print(self, text):
        if self.debug: self.out(str(text))
        return
    
    def out(self, text):
        print(self.color() + self.v["mymail"] + self.color(True) +  ": " + str(text) )
        return

    def color(self, end = False):
        colors = { 'HEADER': '\033[95m', 'OKBLUE': '\033[94m', 'OKCYAN': '\033[96m', 'OKGREEN': '\033[92m', 'WARNING': '\033[93m', 'FAIL': '\033[91m', 'ENDC': '\033[0m', 'BOLD': '\033[1m', 'UNDERLINE': '\033[4m',        }
        if (end == True): return colors['ENDC']
        return colors[self.v["color"]]  

    def connect_imap_login(self):         
        try:
            if self.v["imap_use_ssl"]:
                self.imap = IMAP4_SSL(self.v["imap_server"], self.v["imap_ssl_port"])
            else:
                self.imap = IMAP4(self.v["imap_server"], self.v["imap_port"])
            self.imap.login(self.v["imap_user"], self.v["imap_password"])
            self.mail_isloggedin = True
        except:
            self.mail_isloggedin = False
        return
    
    def connect_imap_logout(self):
        try: self.imap.logout()
        except: pass
        self.mail_isloggedin = False
        return

    def connect_imap_reconnect(self):
        self.connect_imap_logout()
        self.connect_imap_login()
        return self.mail_isloggedin
    
    def check_sender(self, message):
        sender = message.sender
        self.out('Mail from ' + sender + '. Checking...')   
        
        if (sender in self.v["mymail"] or 'noreply' in sender or 'mailer-daemon' in sender or 'no-reply' in sender or 'No-Reply' in sender):
            self.out('Mail from self or noreply. Not sending any mail')
            return False
    
        self.db_connect(); send = True; breakdate = datetime.utcnow() - timedelta(hours=self.v["blockhours"])
        for row in self.db_cur.execute("SELECT id,date FROM senders WHERE mail=?", (sender,)):
            then = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")            
            self.out('Found ' + sender + ' at ' + str(row[1]) + ' - ID ' + str(row[0]))
            if (then < breakdate):  #If older: Delete
                self.out('Last entry, ID' + str(row[0]) +  ' from ' + sender + ' is old. Delete...' )
                self.db_cur.execute("DELETE FROM senders WHERE id=?", ( str(row[0]), ))
            elif (then >= breakdate): #If Recent: Reject
                self.out('Recent entry found. Not sending any mail' )
                self.db_con.close()
                return False
        
        self.db_con.close()
        return True
                
    def check_mail_datetime(self,message):
        msg = message.msg
        for header in ['date']:
            try: 
                datestring = msg[header]
                dateobj = datetime.strptime(datestring, '%a, %d %b %Y %H:%M:%S %z')
                dateobj = (dateobj - dateobj.utcoffset()).replace(tzinfo=None)
                start = self.mail_lastcheck
                end = datetime.strptime(self.v["datetime_end"], "%Y-%m-%d %H:%M")
            except:
                self.debug_print('New mail but could not determine date. Assuming as new...')
                return True

            if (dateobj >= start and dateobj <= end): 
                self.debug_print('New mail within date range.' + str(dateobj) + ' UTC')
                return True
            else: 
                self.debug_print ('Message not within date range. Message Date ' + str(dateobj) + ' UTC')
                return False
 
    def check_program_datetime(self):
        try:
            start = datetime.strptime(self.v["datetime_start"], "%Y-%m-%d %H:%M")  
            end = datetime.strptime(self.v["datetime_end"], "%Y-%m-%d %H:%M")
        except:
            return True
        
        if (datetime.utcnow() >= start and datetime.utcnow() <= end):
            if (self.program_date_active == False or self.program_date_active == None):
                self.program_timeout = self.v["refresh_delay"]
                self.out('In date range. Autoreply is now responding...')
                self.connect_imap_login()
                self.program_date_active = True
            return True
        else:
            if (self.program_date_active == True or self.program_date_active == None):
                self.program_timeout = 60 #increase Timeout 
                self.out('Not in date range. Autoreply is now sleeping...')
                self.connect_imap_logout()
                self.program_date_active = False
            return False
    
    def check_mail_messageid(self, message):
        self.debug_print('Checking Message ID: ' + message.msg_id )
    
        if (message.msg_id in self.mail_ignorelist):
           self.debug_print('Found in memory:' + message.msg_id )
           return False
 
        self.db_connect()
        for row in self.db_cur.execute("SELECT id, date FROM messages WHERE messageid=?", (message.msg_id,)):       
            self.debug_print('Found :' +message.msg_id + ' at ID ' + str(row[0]))
            try: 
                if ((datetime.utcnow() - timedelta(hours=24)) < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")):
                    self.mail_ignorelist.append(message.msg_id)
                    self.debug_print('Entry is recent. Adding to ignorelist')
                    self.debug_print(str(self.mail_ignorelist))
            except: pass
            self.db_con.close()
            return False
    
        self.out('New Message: ' + message.msg_id)
        self.db_con.close()
        return True

    def save_sender(self,message):
        self.db_connect()
        self.out('Memorizing ' + message.sender)
        self.db_cur.execute("INSERT INTO senders (mail, date) values (?, ?)", (message.sender, datetime.utcnow() ) )
        self.db_con.commit()
        self.db_con.close()   
        return 
    
    def save_email(self, message):
        if (self.v['mode'] != 'remember' or message.has_msg_id == False):
            if (self.v['mode'] != 'remember'): self.debug_print ('Autoreply in reply-mode. Marking mail as "answered"')
            if (message.has_msg_id == False): self.debug_print ('No MessageID. Marking mail as "answered"')
            self.imap.select(readonly=False)
            self.imap.store(message.msg_number, '+FLAGS', '\\Answered')
            self.imap.close()
        
        if (message.has_msg_id == True):        
            self.db_connect()
            self.out('Memorizing Message ' + message.msg_id + ' ' + datetime.utcnow().strftime("%Y-%m-%d %H:%M") )
            self.db_cur.execute("INSERT INTO messages (messageid, date) values (?, ?)", (message.msg_id, datetime.utcnow(),) )
            self.mail_ignorelist.append(message.msg_id)
            self.out('Current size of ram-ignorelist: ' + str(len(self.mail_ignorelist)))
            self.db_con.commit()
            self.db_con.close()
        return    
           
    def db_connect(self):
        db = "./db/autoreply-" + self.v["identifier"] + ".db"
        self.db_con = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.db_cur = self.db_con.cursor()
        return

    def db_create_table(self):
        self.db_connect()
        try: self.db_cur.execute('''CREATE TABLE senders (id INTEGER PRIMARY KEY, mail text, date datetime)''')  
        except: pass  
        try: self.db_cur.execute('''CREATE TABLE messages (id INTEGER PRIMARY KEY, messageid text, date datetime)''')  
        except: pass          
        try: self.db_cur.execute( "ALTER TABLE messages ADD COLUMN date datetime")
        except: pass
        
        self.db_con.commit(); self.db_con.close() 
        return   
    
    def create_reply(self, message, debug = False):  
        if (debug == False): subject = message.msg['Subject'].replace('\r', '').replace('\n', '')
        else: subject = re.sub(r"[^a-zA-Z0-9]+", ' ', message.msg['Subject'])

        reply = emails.html(  html= self.v["body_html"],
                              text= self.v["body"],
                              subject= 'Re: ' + subject,
                              mail_from= self.v["from_address"],                             
                             )
        return reply

    def send_reply(self, message):      
        self.out('Sending a response...')

        success = False; r = None  
        for i in range(3):
            if (success != True):
                
                try:
                    reply = self.create_reply(message)
                    r = reply.send(   to= (message.sender),
                                        smtp= {
                                            'host': self.v["smtp_server"], 
                                            'port': self.v["smtp_port"], 
                                            'ssl': self.v["smtp_use_ssl"], 
                                            'user': self.v["smtp_user"], 
                                            'password': self.v["smtp_password"]
                                            }
                                     )
                    assert r.status_code == 250
                    success = True
                except:
                    self.out('Error on sending mail')
                    print(r)
                    try:
                        if (r.status_code == 550):
                            self.out('Mailbox unavailable')
                            return
                    except:
                        self.out ('Trying different subject')
                        reply = self.create_reply(message, True)

                    self.out('  Wait 10s and retry...')
                    time.sleep(10) 
        
        
        if (success==True): 
            self.out('Successfully replied')   
            message.sent = True 
        else: self.out('Could not respond')   
        
        return success  

    def handle_reply(self, mail_number):
        data = self.fetch_mails(mail_number)
        if (data == False): return
        message = self.Mailmessage(data, mail_number, self.debug)

        if (self.check_mail_datetime(message) == True):
            if (self.check_mail_messageid(message) == True): #Shall autoreply respond? Email new, unknown and sender not blocked
                if (self.check_sender(message) == True):
                    self.send_reply(message)
                    self.save_sender(message)
                self.save_email(message)  
                if (message.sent == True): time.sleep(2)   
        
        self.mail_ignorelist = self.mail_ignorelist[-500:] #Limit size of ignorelist
        return
         
    def fetch_mails(self, mail_number):
        try:
            self.imap.select(readonly=True)
            _, data = self.imap.fetch(mail_number, '(RFC822)')
            self.imap.close()
        except:   
            self.out ('Error on Imap Fetch') 
            self.connect_imap_reconnect()
            self.out ('Connected: ' + str(self.mail_isloggedin))
            return False
        return data

    def check_mails_search(self):
        default = 'UNSEEN UNANSWERED'
        yesterday = (datetime.utcnow() - timedelta(hours=24)).strftime("%d-%b-%Y")
        search = '('+ default + ' SINCE ' + yesterday + ')'
        self.debug_print('IMAP SEARCH COMMAND: ' + search)
        return search
  
    def check_mails(self):
        try:
            self.imap.select(readonly=False)
            _, data = self.imap.search(None, self.check_mails_search())
            self.imap.close()    
        except:
            self.out ('Error on Imap Search. Reconnecting') 
            self.connect_imap_reconnect()
            self.out ('Connected: ' + str(self.mail_isloggedin))
            return 

        for mail_number in data[0].split():            
            self.handle_reply(mail_number)
        
        self.mail_lastcheck = datetime.utcnow() - timedelta(minutes=20)
        return


    def run(self):
        self.db_create_table()
        self.out('Autoreply ' + self.version + ' started in ' + self.v["mode"] + '-mode ... Blocking re-replies for ' + str(self.v["blockhours"]) + ' hours')        
        self.out('Autoreply works in UTC timezone. Message dates will be converted. Please check, if you set your start- and enddates in UTC. It is now ' + str(datetime.utcnow()) + ' UTC')
        try: self.out('Response active from ' + str(self.v["datetime_start"]) + ' UTC until ' + str(self.v["datetime_end"]) + ' UTC' )
        except: self.out('No date range found. Autreply is active')
        time.sleep(5)
       
    
        if (self.debug == True):
            while True:
                if (self.check_program_datetime() == True): self.check_mails()
                if (int(self.v["refresh_delay"]) < 30 and self.v["mode"] == 'remember'): self.v["refresh_delay"] = 30 #take some load of server on remember mode
                time.sleep(self.v["refresh_delay"])
        else:        
            while True:
                try:
                    if (self.check_program_datetime() == True): self.check_mails()
                    if (int(self.v["refresh_delay"]) < 30 and self.v["mode"] == 'remember'): self.v["refresh_delay"] = 30 #take some load of server on remember mode
                    time.sleep(self.v["refresh_delay"])
                except: 
                    self.out(sys.exc_info()[0])
                    self.program_date_active = None
                    time.sleep(10)
        
        
        
            
           
        

    
        


        

        
    
        
      
            
