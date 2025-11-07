from typing import Union
from dotenv import load_dotenv
import os
from supabase import Client, create_client
from db.config import config
print('url>',config.url)
print('key',config.key)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERV_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase : Client = create_client(SUPABASE_URL, SUPABASE_KEY)
admin_client: Union[Client, None] = None if config.service_key is None else create_client(SUPABASE_URL, SUPABASE_SERV_KEY)
supabase = supabase if admin_client is None else admin_client
