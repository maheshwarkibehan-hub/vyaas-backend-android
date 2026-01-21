import serial
import subprocess
import time
import os
import signal

# Change COM port
PORT = "COM7"   # apne Arduino ka port
BAUD = 9600

# Path to your agent
PROJECT_DIR = r"C:\Users\mahes\OneDrive\Desktop\vyaasaiupdated\Backend"
AGENT_COMMAND = ["python", "agent.py", "console"]

process = None  # store running process


def start_agent():
    global process
    if process is None:
        print("Starting Vyaas agent...")
        process = subprocess.Popen(
            AGENT_COMMAND,
            cwd=PROJECT_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        print("Agent already running.")


def stop_agent():
    global process
    if process is not None:
        print("Stopping agent (Ctrl + C)...")
        process.send_signal(signal.CTRL_BREAK_EVENT)
        time.sleep(1)
        process = None
    else:
        print("Agent is not running.")


def main():
    print("Listening to Arduino...")

    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)

    while True:
        line = ser.readline().decode().strip()

        if not line:
            continue

        print("Arduino →", line)

        if line == "RUN_AGENT":
            start_agent()

        elif line == "STOP_AGENT":
            stop_agent()


if __name__ == "__main__":
    main()
