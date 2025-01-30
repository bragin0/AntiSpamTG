Telegram Bot for Managing User Messages

The bot manages user messages in chats, limiting the frequency of message sending and deleting messages if they are sent earlier than 1 hour (using timedelta(hours=1)).

How to Modify the Limit:
To decrease the time limit, change the timedelta(hours=1) parameter to the desired number of hours in the code.

Setup:
Replace API_TOKEN with your bot’s token.
Set your ADMIN_ID so only you can manage the chats.

Install Dependencies:

aiogram==2.23 
aiofiles==24.1.0 
aioschedule==0.5.2 
APScheduler==3.6.3
