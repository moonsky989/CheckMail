import pywemo
import time
import logging
from pathlib import Path
from multiprocessing import Process
log = logging.getLogger(__name__)

class SwitchRun:
    def __init__(self, ip_address: str, run_time: int, status_file: str):
        self.process = None
        self.address = ip_address
        self.run_time = run_time * 60
        self.status_file = status_file

    def start(self) -> None:
        self.process = Process(target=self.run)
        self.process.start()

    def run(self):
        url = pywemo.setup_url_for_address(self.address)
        device = pywemo.discovery.device_from_description(url)
        log.info(device)

        # start fan
        device.on()
        Path(self.status_file).touch()
        log.info("run - fan on")

        # run fan for FAN_RUN_TIME
        time.sleep(self.run_time)

        # stop fan
        device.off()
        Path(self.status_file).unlink()
        log.info("run - fan off")

    def stop(self):
        url = pywemo.setup_url_for_address(self.address)
        device = pywemo.discovery.device_from_description(url)
        log.info(device)

        # stop fan
        device.off()
        file = Path(self.status_file)
        if file.is_file():
            file.unlink()
        log.info("stop - fan off")

    def running(self) -> bool:
        # check if a process exists
        if self.process:
            # if so, check that it is running
            self.process.join(timeout=0)
            # if running, return true
            if self.process.is_alive():
                return True
            # otherwise, set process to None
            else:
                self.process = None
        return False


if __name__ == '__main__':
    from configuration import LOG_FILE, LOG_LEVEL, GARAGE_FAN_SWITCH, FAN_RUN_TIME, SWITCH_STATUS_FILE
    logging.basicConfig(format='%(asctime)s: %(message)s', filename=LOG_FILE, level=LOG_LEVEL)
    garage_fan = SwitchRun(GARAGE_FAN_SWITCH, FAN_RUN_TIME, SWITCH_STATUS_FILE)
    garage_fan.start()
