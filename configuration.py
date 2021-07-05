import logging

LOG_LEVEL = logging.INFO
LOG_FILE = "/app/logs/checkmail.log"

HOSTNAME = "imap.gmail.com"
USERNAME = "username"
SENDER = "username@gmail.com"
PASSWORD = "password"
MAILBOX = "Inbox"

SUBSCRIBERS = {"person1": "person1@gmail.com", "person2": "person2@gmail.com"}
ALL_SUBSCRIBERS = ",".join(SUBSCRIBERS.values())

NEW_MAIL_OFFSET = 0  # number of unread mail before new incoming mail 
MAIL_CHECK_FREQ = 5  # check mail every 5 seconds
RENEW_SESSION = 10  # minutes before renewing server session

MY_Q_ADDRESS = "notification@myq.com"
FAN_RUN_TIME = 5  # minutes to run garage fan
GARAGE_FAN_SWITCH = "192.168.0.18"
SWITCH_STATUS_FILE = "on.status"