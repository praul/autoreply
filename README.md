# autoreply
![image](https://user-images.githubusercontent.com/38807639/123596513-9235f800-d7f2-11eb-9fe5-a659a9cb699c.png)

This is python based, mail server independent out-of-office notice for multiple mail accounts.  
**Do you have multiple mail accounts on hosts, that don't support proper out-of-office notices?**  
This could be for you.  

**WARNING:** This answers to any both unread and unanswered mail, even if it is years old (if within selected date range).
             Don’t use on a mailbox with old messages left unread and unanswered just like that. Set date range accordingly.
             
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
- **you need to customize the repliers.py file** It needs to stay a valid python dictionary. If you have errors at startup, this could be a place to look for missing commata or quotes. You can add as many mail accounts as you like

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
 
## Notes & Credit
- Thanks to BertrandBordage for the base version of this script (https://gist.github.com/BertrandBordage/e07e5fe8191590daafafe0dbb05b5a7b)
- Using pythons email and smtplib lead to empty messages on some (office365) mail accounts. For heavens sake, I could not figure it out and therefore used python-emails library, which is missing some features (in-reply-to), but is working stable.
- Using pythons multiprocessing is a quick-and-dirty approach for supporting multiple accounts simultaneously without having to rewrite the base script for this
- I made this basically for myself, so I'm probably not gonna pump this up with feature requests :) 
