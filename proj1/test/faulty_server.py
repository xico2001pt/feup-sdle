import subprocess
import time
import random
import logging

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

def main():
    while True:
        p = subprocess.Popen(["python3", "src/server.py"])
        time_to_crash = random.randint(30, 120)
        down_time = random.randint(1, 10)
        time.sleep(time_to_crash)
        logging.error("Server crashed")
        time.sleep(down_time)
        p.kill()

if __name__ == '__main__':
    main()