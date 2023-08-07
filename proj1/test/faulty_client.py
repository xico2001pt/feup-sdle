import subprocess
import argparse
import time
import random
import sys

parser = argparse.ArgumentParser(description='Client for the server')
parser.add_argument('client_data_dir', help='Directory where client data should be stored', type=str)

def main():
    p = parser.parse_args()

    while True:
        process = subprocess.Popen(['python3', 'src/cli.py', p.client_data_dir], stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
        time_to_crash = random.randint(30, 120)
        down_time = random.randint(1, 10)
        time.sleep(time_to_crash)
        print("CRASH")
        process.kill()
        time.sleep(down_time)

if __name__ == '__main__':
    main()