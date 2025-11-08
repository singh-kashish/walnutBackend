# main.py
from dotenv import load_dotenv
from app import app, init_queue

def main():
    load_dotenv()
    init_queue()
    app.run(host="0.0.0.0", port=5020)

if __name__ == "__main__":
    main()
