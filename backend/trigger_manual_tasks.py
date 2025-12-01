import sys
import os
import time

# Add the current directory to sys.path to ensure app module can be imported
sys.path.append(os.getcwd())

from app.worker import fetch_news_task, analyze_news_task

def trigger_tasks():
    print("Triggering fetch_news_task...")
    fetch_task = fetch_news_task.delay()
    print(f"Triggered fetch_news_task with ID: {fetch_task.id}")

    # Wait a bit to ensure fetch starts before analyze (though analyze checks DB)
    time.sleep(2)

    print("Triggering analyze_news_task...")
    analyze_task = analyze_news_task.delay()
    print(f"Triggered analyze_news_task with ID: {analyze_task.id}")

if __name__ == "__main__":
    trigger_tasks()
