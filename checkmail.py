#!/usr/bin/env python3

import email
from pathlib import Path
import time
import platform
from datetime import date, datetime
from imapclient import IMAPClient
import logging

from configuration import (
    FAN_RUN_TIME,
    GARAGE_FAN_SWITCH,
    LOG_LEVEL, 
    LOG_FILE,
    HOSTNAME, 
    USERNAME, 
    SENDER, 
    PASSWORD, 
    MAILBOX, 
    SUBSCRIBERS, 
    ALL_SUBSCRIBERS, 
    NEW_MAIL_OFFSET, 
    MAIL_CHECK_FREQ, 
    RENEW_SESSION,
    MY_Q_ADDRESS,
    SWITCH_STATUS_FILE
)

from garage_fan import SwitchRun

class CheckMail:
    def __init__(self, init_time: datetime):
        self.then = init_time

    def run(self, server: IMAPClient) -> None:
        self.update_time()

        # every RENEW_SESSION minutes logout and login to renew session
        self.renew_session(server)

        # number of messages in inbox
        select_info = server.select_folder(MAILBOX)
        logging.debug("%d messages in INBOX" % select_info[b'EXISTS'])

        # number of unreead e-mails in inbox
        folder_status = server.folder_status(MAILBOX, 'UNSEEN')
        newmails = int(folder_status[b'UNSEEN'])
        logging.debug("%d new emails" % newmails)

        # process new mail
        if newmails > NEW_MAIL_OFFSET:
            mail_data = self.process_new_mail(server)
            # process command messages
            self.process_command(mail_data)

        # check to see if switch is still running
        self.check_switch()

        time.sleep(MAIL_CHECK_FREQ)

    def renew_session(self, server: IMAPClient) -> None:
        if self.minutes >= RENEW_SESSION:
            logging.info("renewing session...")
            server.logout()
            server.login(USERNAME, PASSWORD)
            logging.info("session renewed")
            self.then = self.now
    
    def update_time(self):
        self.now = datetime.now()
        duration = (self.now-self.then).total_seconds()
        self.minutes = divmod(duration, 60)[0]

    def process_new_mail(self, server):
        # copy new mail to Commands folder
        server.select_folder(MAILBOX, readonly = False)
        email_ids = server.search(['UNSEEN'])
        logging.debug("copying emails to Commands folder")
        apply_lbl_msg = server.copy(email_ids, 'Commands')

        # gather data from new messages
        mail_data = []
        for msgid, data in server.fetch(email_ids, ['ENVELOPE']).items():
            message = {}
            envelope = data[b'ENVELOPE']
            message["subject"] = envelope.subject.decode()
            from_ = envelope.sender
            message["from"] = from_[0][2].decode("utf-8") + "@" + from_[0][3].decode("utf-8")
            mail_data.append(message)
            logging.info("sender= " + message["from"] + " - subject= " + message["subject"])

        # delete new mail from Inbox if copied to Commands folder
        if apply_lbl_msg is None or apply_lbl_msg == 1:
            logging.debug("deleting message from inbox")
            server.delete_messages(email_ids)
            server.expunge()
        return mail_data

    @staticmethod
    def process_command(mail_data) -> None:
        for command in mail_data:
            subject = command["subject"].lower()
            from_ = command["from"].lower()
            if subject == "camera":
                logging.info("running camera command...")
            if from_ == MY_Q_ADDRESS:
                logging.info("running MyQ command...")
                garage_fan = SwitchRun(GARAGE_FAN_SWITCH, FAN_RUN_TIME, SWITCH_STATUS_FILE)
                garage_fan.start()

    @staticmethod    
    def check_switch():
        file = Path(SWITCH_STATUS_FILE)
        if file.is_file():
            file_time = datetime.fromtimestamp(file.stat().st_ctime)
            on_for = datetime.now() - file_time
            logging.info("garage fan on for = " + str(on_for.total_seconds()) + " seconds")
            if on_for.total_seconds() > (FAN_RUN_TIME*60):
                print("stopping garage fan")
                logging.info("stopping garage fan")
                garage_fan = SwitchRun(GARAGE_FAN_SWITCH, FAN_RUN_TIME, SWITCH_STATUS_FILE)
                garage_fan.stop()



if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s: %(message)s', filename=LOG_FILE, level=LOG_LEVEL)
    server = IMAPClient(host=HOSTNAME, use_uid=True, ssl=True)
    server.login(USERNAME, PASSWORD)
    checkmail = CheckMail(datetime.now())
    logging.info("Running CheckMail...")
    while True:
        try:
            checkmail.run(server)
        except Exception as e:
            logging.info("Exception:")
            logging.info(e)