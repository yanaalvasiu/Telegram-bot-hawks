#!/usr/bin/env python3
"""
Main entry point for the Telegram bot application.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from bot import TelegramBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot."""
    try:
        # Get required environment variables
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not supabase_key:
            raise ValueError("SUPABASE_KEY environment variable is required")
        
        # Initialize and start the bot
        telegram_bot = TelegramBot(bot_token, supabase_url, supabase_key)
        telegram_bot.start_sync()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    # Create and run the main function
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
