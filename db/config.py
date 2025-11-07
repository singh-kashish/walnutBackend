import os
import sys
from typing import Union
from dotenv import load_dotenv

_ = load_dotenv()  # loads from .env or .env.local automatically


class Config:
    url: str
    key: str
    service_key: Union[str, None]

    def __init__(self) -> None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        self.service_key = os.environ.get("SUPABASE_SERVICE_KEY")

        if url is None or key is None:
            sys.exit('Missing "SUPABASE_URL" or "SUPABASE_ANON_KEY" in environment vars')

        self.url = url
        self.key = key


config = Config()
