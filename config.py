import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # ID do grupo onde os alertas serão postados

# Intervalo entre buscas por novas promoções (em minutos)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", 15))

# Desconto mínimo (%) para considerar uma promoção "boa"
MIN_DISCOUNT_PERCENT = int(os.getenv("MIN_DISCOUNT_PERCENT", 20))

DATABASE_PATH = os.getenv("DATABASE_PATH", "promo_bot.db")

# --- Mercado Livre ---
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN")
ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "https://localhost")

# --- Lomadee ---
LOMADEE_APP_TOKEN = os.getenv("LOMADEE_APP_TOKEN")
LOMADEE_SOURCE_ID = os.getenv("LOMADEE_SOURCE_ID")

# --- Awin ---
AWIN_API_TOKEN = os.getenv("AWIN_API_TOKEN")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")
