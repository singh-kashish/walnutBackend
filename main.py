from dotenv import load_dotenv

from app import app
from process_transaction import queue

_ = load_dotenv()

def main():
    queue.start()
    app.run()


if __name__ == "__main__":
	  main()
