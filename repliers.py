v = [
    {
        "identifier": "example-account", #Take a simple name, something that works as a filename
        "refresh_delay": 5,  #delay in seconds between new email checks

        "imap_server": 'imap.example.com',
        "imap_port": 143,
        "imap_ssl_port": 993,
        "imap_use_ssl": True,

        "imap_user": 'user@example.com',
        "imap_password": 'YOURSUPERSAFEPASSWORD',

        "smtp_server": 'smtp.example.com',
        "smtp_port": 465, 
        "smtp_use_ssl": True,

        "smtp_user": 'user@example.com',
        "smtp_password": 'YOURSUPERSAFEPASSWORD',
        

        "blockhours": 12, #The time in hours in which autoresponder does not respond again to the same adress.
        "mymail": 'user@example.com',

        
        "datetime_start": "2020-01-01 10:00", #start responding at date."%Y-%m-%d %H:%M
        "datetime_end": "2022-01-01 10:00", #end responding at date. "%Y-%m-%d %H:%M

        "from_address": ('Out of Office', 'user@example.com'), #Name and Email
        "body": 'Hi, User XYZ is out of office von user@example.com.', #plain text email content
        "body_html": '<h3>Out of office</h3><p>Hi, User XYZ is out of office</p>' #html email content
    },

    {
        #you can just add another account
        "identifier": "example-account", #Take a simple name, something that works as a filename
        "refresh_delay": 5,  #delay in seconds between new email checks

        "imap_server": 'imap.example.com',
        "imap_port": 143,
        "imap_ssl_port": 993,
        "imap_use_ssl": True,

        "imap_user": 'user@example.com',
        "imap_password": 'YOURSUPERSAFEPASSWORD',

        "smtp_server": 'smtp.example.com',
        "smtp_port": 465, 
        "smtp_use_ssl": True,

        "smtp_user": 'user@example.com',
        "smtp_password": 'YOURSUPERSAFEPASSWORD',
        

        "blockhours": 12, #The time in hours in which autoresponder does not respond again to the same adress.
        "mymail": 'user@example.com',

        "datetime_start": "2020-01-01 10:00", #start responding at date."%Y-%m-%d %H:%M
        "datetime_end": "2022-01-01 10:00", #end responding at date. "%Y-%m-%d %H:%M

        "from_address": ('Out of Office', 'user@example.com'), #Name and Email
        "body": 'Hi, User XYZ is out of office von user@example.com.', #plain text email content
        "body_html": '<h3>Out of office</h3><p>Hi, User XYZ is out of office</p>' #html email content
    },

    ]