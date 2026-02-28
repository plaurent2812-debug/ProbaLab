import requests
from config import logger

# Try importing telegram config from environment variables (you need to add these)
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to the configured VIP Telegram channel.
    
    Args:
        text: The message body (can contain emojis and HTML tags).
        parse_mode: The text parsing mode (HTML by default for bolding).
        
    Returns:
        True if the message was sent successfully, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logger.warning("Telegram Bot Token ou Channel ID introuvable. Message non envoyé.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Message Telegram envoyé avec succès.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message Telegram : {e}")
        return False

# Tests can be performed by running this file locally with the env vars set
if __name__ == "__main__":
    # To test locally:
    # export TELEGRAM_BOT_TOKEN="your_token"
    # export TELEGRAM_CHANNEL_ID="@your_channel_name"
    # python Projet_Football/telegram_bot.py
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID:
        print("Envoi d'un message test...")
        success = send_telegram_message("🤖 <b>Test depuis ProbaLab</b>\nCeci est un message de test automatisé.")
        print("Succès :" if success else "Échec")
    else:
        print("Veuillez configurer TELEGRAM_BOT_TOKEN et TELEGRAM_CHANNEL_ID pour tester.")
