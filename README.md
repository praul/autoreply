# autoreply
python based out of office notice for multiple mail accounts

**Build**
git clone repo
    `cd dockerfile/`
    `docker build -t praul1/autoreply:latest .`
or use praul1/autoreply:latest from docker hub

**Usage:**
You need a repliers.py file. See example at 

Enter credentials in repliers.py
Create as many autoresponders as you like. Be sure that it stays a valid python dictionary list.

**Run:**
Mount bind repliers.py to /app/repliers.py
    `docker run -v /PATH/TO/repliers.py:/app/repliers.py praul1/autoreply:latest`
or use docker-compose.yml.

