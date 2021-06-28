# autoreply
This is python based, mail server independent out-of-office notice for multiple mail accounts.  
Do you have multiple mail accounts on hosts, that don't support proper out-of-office notices?  
This could be for you.  

## Features 
- Checks multiple imap accounts for mails that are both unread and unanswered
- Sends custom plaintext and html replies to the senders.
- Remembers the senders for a customizable time range, and does not send another reply during this time range
- Replies only within a customizable date range - you never have to remember to disable your out-of-office notice
- python based, should run on any platform

## Usage
- **you need to customize the repliers.py file** It needs to stay a valid python dictionary. If you have errors at startup, this could be a place to look for missing commata or quotes. You can add as many mail accounts as you like

## Usage: Docker Container
- **Image**: Clone this repo and build from dockerfile. Or use praul1/autoreply:latest from docker hub  
- **Run**: You need to mount your repliers.py file to /app/repliers.py inside the container:  ```docker run -v /PATH/TO/repliers.py:/app/repliers.py praul1/autoreply:latest```
- **Docker-Compose**: You can use the supplied docker-compose.yml. Customize path to point to your repliers.py. 
- The docker compose file also includes the docker-log viewer "Dozzle" (https://github.com/amir20/dozzle). When launched, you can visit: <HOST>:10101 to view the log of autoreply  

## Usage Python

 


**Build**  
Clone this repo  
```
cd dockerfile/
docker build -t praul1/autoreply:latest .
```  
or use praul1/autoreply:latest from docker hub  

**Usage:**  
You need a repliers.py file. See example at   

Enter credentials in repliers.py  
Create as many autoresponders as you like. Be sure that it stays a valid python dictionary list.  

**Run:**  
Mount bind repliers.py to /app/repliers.py  
    ```docker run -v /PATH/TO/repliers.py:/app/repliers.py praul1/autoreply:latest```  
or use docker-compose.yml.  
