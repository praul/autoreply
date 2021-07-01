import email
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
import sqlite3
from datetime import datetime, timedelta
import time
import sys
import emails

__author__ = 'praul'


class AutoReplyer:
    con = None
    cur = None
    v = None
    timeout = None
    intime = True
    ignorelist = []
    override_memorize = False
    debug = False

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
            self.debug = debug
            self.msg_number = mail_number
            self.msg = self.get_message(data)
            self.msg_id = self.get_messageid(self.msg) 
            self.sender = self.get_sender(self.msg)
        
        def debug_print(self, text):
            if self.debug: print(str(text))   

        def get_message(self, data):
            msg = email.message_from_bytes(data[0][1])
            return msg

        def get_messageid(self, msg):
            self.debug_print('Getting MessageID...')
            for header in ['Message-ID']:
                self.debug_print(msg[header])
                if (msg[header] is not None):
                    messageid = str(msg[header]).replace('<', '').replace('>','').replace("\n", "").replace("\r", "")
                    self.debug_print ('MessageID is ' + messageid)
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
        self.timeout = self.v["refresh_delay"]
        try: self.v["mode"] = self.v["mode"]
        except: self.v["mode"] = 'reply'
        try: self.debug = self.v['debug']
        except: self.debug = False
        
        self.connect_imap_login()
        self.run()

    def debug_print(self, text):
        if self.debug: self.out(str(text))
    
    def out(self, text):
        print(self.color() + self.v["mymail"] + self.color(True) +  ": " + str(text) )

    def color(self, end = False):
        colors = { 'HEADER': '\033[95m', 'OKBLUE': '\033[94m', 'OKCYAN': '\033[96m', 'OKGREEN': '\033[92m', 'WARNING': '\033[93m', 'FAIL': '\033[91m', 'ENDC': '\033[0m', 'BOLD': '\033[1m', 'UNDERLINE': '\033[4m',        }
        if (end == True): return colors['ENDC']
        return colors[self.v["color"]]  

    def connect_imap_login(self):
        if self.v["imap_use_ssl"]:
            self.imap = IMAP4_SSL(self.v["imap_server"], self.v["imap_ssl_port"])
        else:
            self.imap = IMAP4(self.v["imap_server"], self.v["imap_port"])
        self.imap.login(self.v["imap_user"], self.v["imap_password"])
    
    def connect_imap_logout(self):
        self.imap.logout()
    
    def check_sender(self, message):
        sender = message.sender
        self.out('Mail from ' + sender + '. Checking...')   
        
        if (sender in self.v["mymail"] or 'noreply' in sender or 'mailer-daemon' in sender):
            self.out('Mail from self or noreply. Not sending any mail')
            return False
    
        self.db_connect(); send = True; breakdate = datetime.now() - timedelta(hours=self.v["blockhours"])
        for row in self.cur.execute("SELECT id,date FROM senders WHERE mail=?", (sender,)):
            then = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")            
            self.out('Found ' + sender + ' at ' + str(row[1]) + ' - ID ' + str(row[0]))
            if (then < breakdate):  #If older: Delete
                self.out('Last entry, ID' + str(row[0]) +  ' from ' + sender + ' is old. Delete...' )
                self.cur.execute("DELETE FROM senders WHERE id=?", (str(row[0])))
            elif (then >= breakdate): #If Recent: Reject
                self.out('Recent entry found. Not sending any mail' )
                self.con.close()
                return False
        
        self.con.close()
        return True
                
    def check_mail_datetime(self,message):
        msg = message.msg
        for header in ['date']:
            try: 
                datestring = msg[header]
                dateobj = datetime.strptime(datestring, '%a, %d %b %Y %H:%M:%S +%z')
                start = datetime.now() - timedelta(minutes = 20)
                #start = datetime.strptime(self.v["datetime_start"], "%Y-%m-%d %H:%M")  
                end = datetime.strptime(self.v["datetime_end"], "%Y-%m-%d %H:%M")
                self.debug_print ('Message not within date range. Message Date ' + str(datestring) )
            except:
                return True

            if (dateobj >= start and dateobj <= end): 
                self.out(str(dateobj) + ' Mail within date range.')
                return True
            else: 
                return False
 
    def check_program_datetime(self):
        try:
            start = datetime.strptime(self.v["datetime_start"], "%Y-%m-%d %H:%M")  
            end = datetime.strptime(self.v["datetime_end"], "%Y-%m-%d %H:%M")
        except:
            return True
        
        if (datetime.now() >= start and datetime.now() <= end):
            if (self.intime == False):
                self.timeout = self.v["refresh_delay"]
                self.out('In date range. Autoreply is now responding...')
                self.intime = True
            return True
        else:
            if (self.intime == True):
                self.timeout = 60 #increase Timeout 
                self.out('Not in date range. Autoreply is now sleeping...')
                self.intime = False
            return False
    
    def check_mail_messageid(self, message):
        self.debug_print('Checking Message ID: ' + message.msg_id )
    
        if (message.msg_id in self.ignorelist):
            self.debug_print('Found in memory:' + message.msg_id )
            return False
 
        self.db_connect(); send = True
        for row in self.cur.execute("SELECT id, messageid FROM messages WHERE messageid=?", (message.msg_id,)):       
            self.debug_print('Found :' +message.msg_id + ' at ID ' + str(row[0]))
            self.ignorelist.append(message.msg_id)
            self.con.close()
            return False
    
        self.out('New Message: ' + message.msg_id)
        self.con.close()
        return send

    def save_sender(self,message):
        self.db_connect()
        self.out('Memorizing ' + message.sender)
        self.cur.execute("INSERT INTO senders (mail, date) values (?, ?)", (message.sender, datetime.now() ) )
        self.con.commit()
        self.con.close()    
    
    def save_email(self, message):
        if (self.v['mode'] != 'remember' or message.has_msg_id == False):
            if (self.v['mode'] != 'remember'): self.debug_print ('Autoreply in reply-mode. Marking mail as "answered"')
            if (message.has_msg_id == False): self.debug_print ('No MessageID. Marking mail as "answered"')
            self.imap.select(readonly=False)
            self.imap.store(message.msg_number, '+FLAGS', '\\Answered')
            self.imap.close()
        
        if (message.has_msg_id == True):        
            self.db_connect()
            self.out('Memorizing Message ' + message.msg_id)
            self.cur.execute("INSERT INTO messages (messageid) values (?)", (message.msg_id,) )
            self.ignorelist.append(message.msg_id)
            self.con.commit()
            self.con.close()    
           
    def db_connect(self):
        db = "./db/autoreply-" + self.v["identifier"] + ".db"
        self.con = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.con.cursor()

    def db_create_table(self):
        self.db_connect()
        try: self.cur.execute('''CREATE TABLE senders (id INTEGER PRIMARY KEY, mail text, date datetime)''')  
        except: pass  
        try: self.cur.execute('''CREATE TABLE messages (id INTEGER PRIMARY KEY, messageid text)''')  
        except: pass          
        self.con.commit(); self.con.close()    
    
    def create_reply(self, message):  
        reply = emails.html(  html= self.v["body_html"],
                              text= self.v["body"],
                              subject= 'Re: ' + message.msg['Subject'],
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
                    self.out('Error on send: ' + str(r))
                    try:
                        if (r.status_code == 550):
                            self.out('Mailbox unavailable')
                            return
                    except:
                        pass
                    self.out('  Wait 10s and retry...')
                    time.sleep(10) 
        
        
        if (success==True): 
            self.out('Successfully replied')   
            message.sent = True 
        else: self.out('Could not respond')      

    def handle_reply(self, mail_number):
        data = self.fetch_mails(mail_number)
        if (data == False): return
        message = self.Mailmessage(data, mail_number, self.debug)

        if (self.check_mail_datetime(message) == True and self.check_mail_messageid(message) == True): #Shall autoreply respond? Email new, unknown and sender not blocked
            if (self.check_sender(message) == True):
                self.send_reply(message)
                self.save_sender(message)
            self.save_email(message)  
            if (message.sent == True): time.sleep(2)     
         
    def fetch_mails(self, mail_number):
        try:
            self.imap.select(readonly=True)
            _, data = self.imap.fetch(mail_number, '(RFC822)')
            self.imap.close()
        except:   
            self.out ('Error on Imap Search') 
            return False
        return data
  
    def check_mails(self):
        try:
            self.imap.select(readonly=False)
            _, data = self.imap.search(None, '(UNSEEN UNANSWERED)')
            self.imap.close()     
        except:
            self.out ('Error on Imap Search') 
            return 

        for mail_number in data[0].split():            
            self.handle_reply(mail_number)


    def run(self):
        self.db_create_table()
        self.out('Autoreply started in ' + self.v["mode"] + '-mode ... Blocking re-replies for ' + str(self.v["blockhours"]) + ' hours')        
        try: self.out('Response active from ' + str(self.v["datetime_start"]) + ' until ' + str(self.v["datetime_end"]) )
        except: self.out('No date range found. Autreply is active')
       
        '''
        while True:
            if (self.check_program_datetime() == True): self.check_mails()
            if (int(self.v["refresh_delay"]) < 30 and self.v["mode"] == 'remember'): self.v["refresh_delay"] = 30 #take some load of server on remember mode
            time.sleep(self.v["refresh_delay"])
        '''
        
        
        while True:
            try:
                if (self.check_program_datetime() == True): self.check_mails()
                time.sleep(self.v["refresh_delay"])
            except: 
                e = sys.exc_info()[0]
                print (e)
                self.connect_imap_logout()
                time.sleep(10)
                self.connect_imap_login()
        

    
        


        

        
    
        
      
            
