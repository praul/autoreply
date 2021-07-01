# autoreply
![image](https://user-images.githubusercontent.com/38807639/123649002-bc56dc80-d829-11eb-8995-5086fba163ca.png)

This is a python based, mail server independent out-of-office notice for multiple mail accounts.  
**Do you have multiple mail accounts on hosts, that don't support proper out-of-office notices?**  
This could be for you. Run this on server, nas, homelab or raspberry. Run this on any device that is on 24/7 and supports python.

See Changelog here: https://github.com/praul/autoreply/wiki/Changelog

**WARNING:** This answers to any both unread and unanswered mail, even if it is years old (if within selected date range).
             Don’t use on a mailbox with old messages left unread and unanswered just like that. Set date range accordingly. Too many both unread and unanswered messages will slow this script down (see note below). So: Clean your mailbox before using this :)
             
             Use at own risk. I am not responsible if this script spams every sender in your inbox :)
             Try interactive first and cancel script if it somehow messes up.
             
This is a very early version of this script. If you run into issues, please let me know.

## Features 
- Checks multiple imap accounts for mails that are both unread and unanswered
- Sends custom plaintext and html replies to the senders.
- Marks the corresponding incoming email as "replied"
- Remembers the senders for a customizable time range, and does not send another reply during this time range - no autoreply pingpong
- Replies only within a customizable date range - you will never forget to disable your out-of-office notice
- python based, should run on any platform
- docker image for amd64 platforms. build yourself for arm and others.

## Usage
- **you need to customize the repliers.py file** It needs to stay a valid python dictionary. All the keys have to remain! If you have errors at startup, this could be a place to look for missing commata or quotes. You can add as many mail accounts as you like

## Usage: Docker Container
- **Image**: Clone this repo and build from dockerfile. Or use praul1/autoreply:latest from docker hub  
  
- **Run**: You need to mount your repliers.py file to /app/repliers.py inside the container. For persistance, mount a writable db folder to /app/db 
- **Run command**: ```docker run -v /etc/localtime:/etc/localtime:ro -v /PATH/TO/repliers.py:/app/repliers.py -v /PATH/TO/db:/app/db praul1/autoreply:latest```
  
- **Docker-Compose**: You can use the supplied docker-compose.yml. Customize path to point to your repliers.py and db folder. 
- The docker-compose file also includes the docker-log viewer "Dozzle" (https://github.com/amir20/dozzle). When launched, you can visit: http://HOST:10101 to view the log of autoreply  

## Usage: Python
- You will need python3 and python-emails (https://python-emails.readthedocs.io/en/latest/)
- ```pip3 install emails```
- All files should be in the same folder. You can then launch the autoresponder with
- ```python3 script.py```
- There should be a writable "db"-folder in script path

## Settings (repliers.py)
- "remember" mode. Set "mode": "remember" in repliers.py. In this mode, emails will NOT be marked as "replied". Instead, autoreply remembers the corresponding messageids. This is way slower than "reply" (default setting). Use this, if you still want to keep track of the replied emails you got during your out-of-office. Keep in mind, this could get slow, as there is no possibility to tell imap which mails to fetch. autoreplyer will always fetch all (unanswered, unread) mails and loop through them. Everytime. On remember mode, minimum refresh rate is 30 seconds.
- "debug" key. Leave it at "False", it will spam your console otherwise
 
## Notes & Credit
- Thanks to BertrandBordage for the base version of this script (https://gist.github.com/BertrandBordage/e07e5fe8191590daafafe0dbb05b5a7b)
- Using pythons email and smtplib lead to empty messages on some (office365) mail accounts. For heavens sake, I could not figure it out and therefore used python-emails library, which is missing some features (in-reply-to), but is working stable.
- Using pythons multiprocessing is a quick-and-dirty approach for supporting multiple accounts simultaneously without having to rewrite the base script for this
- I made this basically for myself, so I'm probably not gonna pump this up with feature requests :) 
- The script does not fetch unread or unanswered emails via date. It simply ignores every email, that is not in the specified date range. It does that like every 5 seconds (everytime it checks for new mails). So..... if you have thousands of both unread and unanswered mails in a mailbox - this could get quite slow. Unneccessarily slow. This is something, that could be improved.
