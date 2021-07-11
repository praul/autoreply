![image](https://user-images.githubusercontent.com/38807639/124927237-b36ec380-dffe-11eb-8362-016549534195.png)


This is a python based, mail server independent out-of-office notice for multiple mail accounts.  
**Do you have multiple mail accounts on hosts, that don't support proper out-of-office notices?**  
This could be for you. Run this on server, nas, homelab or raspberry. Run this on any device that is powered on 24/7 and supports python.

See Changelog here: https://github.com/praul/autoreply/wiki/Changelog
             
**Use at own risk. Try interactive first and cancel script if it somehow messes up.**
             
I run this 24/7 on a vserver for multiple mail accounts without problems, but please note: 
This is a early version of this script. If you run into issues, please let me know. 

## Features 
- Checks multiple imap accounts for mails that are both unread and unanswered
- Sends custom plaintext and html replies to the senders (over smtp).
- Remembers the incoming mail as processed (remember-mode, see below) or marks the corresponding incoming email as "replied" (reply-mode).
- Remembers the senders for a customizable time range, and does not send another reply during this time range - no autoreply pingpong
- Replies only within a customizable date range - you will never forget to disable your out-of-office notice
- python based, should run on any platform
- docker image for amd64 platforms. build yourself for arm and others.

## Usage
- **you need to create a repliers.py file from repliers.py.example and customize it.** It needs to stay a valid python dictionary. All the keys have to remain! If you have errors at startup, this could be a place to look for missing commata or quotes. You can add as many mail accounts as you like. 
- **USE UTC DATETIMES as of 0.5** for your autoreply begin and end datetimes.

## Usage: Docker Container
- **Image**: Clone this repo and build from dockerfile. Or use praul1/autoreply:latest from docker hub  
- **Docker-Compose** (recommended): You can use the supplied docker-compose.yml. Customize path to point to your repliers.py and db folder. 
- The docker-compose file also includes the docker-log viewer "Dozzle" (https://github.com/amir20/dozzle). When launched, you can visit: http://HOST:10101/show?name=autoreply_autoreply to view the log of autoreply. 
- 
- **Run**: You need to mount your repliers.py file to /app/repliers.py inside the container. Also, mount a writable db folder to /app/db 
- **Run command**: ```docker run -v /etc/localtime:/etc/localtime:ro -v /PATH/TO/repliers.py:/app/repliers.py -v /PATH/TO/db:/app/db praul1/autoreply:latest```
  
## Usage: Python
- You will need python3 and python-emails (https://python-emails.readthedocs.io/en/latest/)
- ```pip3 install emails```
- All files should be in the same folder. You can then launch the autoresponder with
- ```python3 script.py```
- There has to be a writable "db"-folder in script path


## Settings (repliers.py)
- **remember-mode**. Set ```"mode": "remember",``` in repliers.py. In this mode, emails will NOT be marked as "replied". Instead, autoreply remembers the corresponding messageids. This is way slower than "reply" (default setting). Use this, if you still want to keep track, to which emails **you** actually replied. If you get thousands of emails everyday, this will be slow. On remember mode, minimum refresh rate is set automatically to 30 seconds. If you want faster replies, you can go for "reply" mode.
- "debug" key. Leave it at "False", it will spam your console otherwise


## Backgrounds on preventing reply errors
There are two bad scenarios when it comes to autoreplies. **Here are some infos on how autoreply tries to prevent them:**

#### Replying more than once
- In "remember" mode, autoreply saves the corresponding messageids and compares every mail against them. If this should somehow fail, it marks the mail as answered as a fallback. Since autoreply only fetches unanswered mails, autoreply won't respond to this message again
- If sending a message somehow fails, autoreply tries again for a small, limited number of times. It then remembers/marks the mail. 
- autoreply always remembers and compares messageids, even in "reply" mode. This allows for switching between the two settings.
- When starting up, autoreply only processes emails that were received during the last 20 minutes. If you were in "remember" mode, somehow crashed the database and have unread and unanswered mails in your inbox, autoreply will respond to them, possibly again. The 20 minute time window was chosen to cope with possible downtimes.

#### Not replying at all
- If sending a message somehow fails, autoreply tries again for a small, limited number of times. If no response was possible then, autoreply stops trying.
- If you are getting mails that were somehow delayed and have a timestamp older than 20 minutes, autoreply will ignore them. If this happens to you (a lot), you can up the treshold at line 346 ```self.mail_lastcheck = datetime.utcnow() - timedelta(minutes=20)```
- Older versions produced an error with some characters in mail subjects. Since 0.51 autoreply catches these errors, regexes every char out that is not a regular character or a space and tries again.


## Password security and data protection
- Your username and password will be in repliers.py, plain and unencrypted. On multi-user machines, take care that only the appropriate user has read access.
- autoreply collects the following data in autoreply-IDENTIFIER.db: 
  - email adress of sender and received date. These entries will be automatically removed, if the entry is older than the specified blockhours
  - messageid of email and received date. These entries will not be purged automatically
- The console output will contain personal data, like email adresses of the senders and messageids. When using a web-log-viewer, like dozzle (used in example docker-compose.yml), password protect it (either directly over dozzle: https://github.com/amir20/dozzle#environment-variables-and-configuration) or via your reverse-proxy.

## Notes & Credit
- Thanks to BertrandBordage for the base version of this script (https://gist.github.com/BertrandBordage/e07e5fe8191590daafafe0dbb05b5a7b). Code is now almost completely rewritten, but this was a good starting point.
- Using pythons email and smtplib lead to empty messages on some (office365) mail accounts. For heavens sake, I could not figure it out and therefore used python-emails library, which is missing some features (in-reply-to), but is working stable.
- Using pythons threading is a quick-and-dirty approach for supporting multiple accounts simultaneously without having to rewrite the base script for this
- I made this basically for myself, so I'm probably not gonna pump this up with feature requests :) 
- If you start this script and have both unanswered and unread mails in your inbox, autoreply will answer to those, that were received up to 20 minutes ago. It does so to prevent unanswered mails on restart or downtime.
- On my imap accounts, connection gets dropped after 24hours. autoreply then automatically reconnects.
