"""
Telegram Bot implementation for Supabase data extraction.
"""

import logging
import asyncio
from typing import Dict, Any, Set
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import SupabaseManager

logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot class."""

    def __init__(self, bot_token: str, supabase_url: str, supabase_key: str):
        """Initialize the bot with Telegram token and Supabase credentials."""
        self.bot_token = bot_token
        self.db_manager = SupabaseManager(supabase_url, supabase_key)
        self.application = None
        self.known_booking_ids: Set[str] = set()
        self.subscribers: Set[int] = set()  # Chat IDs for notifications

    async def start(self):
        """Start the bot and begin polling for updates."""
        try:
            # Create application
            self.application = Application.builder().token(
                self.bot_token).build()

            # Add command handlers
            self.application.add_handler(
                CommandHandler("start", self.start_command))
            self.application.add_handler(
                CommandHandler("help", self.help_command))
            self.application.add_handler(
                CommandHandler("bookings", self.bookings_command))
            self.application.add_handler(
                CommandHandler("notifications", self.notifications_command))
            self.application.add_handler(
                CommandHandler("stop_notifications",
                               self.stop_notifications_command))

            # Add message handler for conversational queries
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               self.handle_message))

            # Start polling
            logger.info("Starting bot...")

            # Initialize the application first
            await self.application.initialize()
            await self.application.start()

            # Start the notification monitoring task
            asyncio.create_task(self.monitor_new_bookings())

            # Start polling
            await self.application.updater.start_polling(
                drop_pending_updates=True)
            await self.application.updater.idle()

        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    def start_sync(self):
        """Start the bot synchronously."""
        try:
            # Create application
            self.application = Application.builder().token(
                self.bot_token).build()

            # Add command handlers
            self.application.add_handler(
                CommandHandler("start", self.start_command))
            self.application.add_handler(
                CommandHandler("help", self.help_command))
            self.application.add_handler(
                CommandHandler("bookings", self.bookings_command))
            self.application.add_handler(
                CommandHandler("notifications", self.notifications_command))
            self.application.add_handler(
                CommandHandler("stop_notifications",
                               self.stop_notifications_command))

            # Add message handler for conversational queries
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               self.handle_message))

            # Start polling synchronously
            logger.info("Starting bot...")

            # Start monitoring task in background thread
            import threading
            monitoring_thread = threading.Thread(
                target=self._start_monitoring_sync)
            monitoring_thread.daemon = True
            monitoring_thread.start()

            self.application.run_polling(drop_pending_updates=True)

        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    async def start_command(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not update.message:
            return

        welcome_message = """
🏨 Welcome to the Booking Management Bot!

I can help you manage and monitor your bookings.

Available commands:
• /help - Show this help message
• /bookings - See all current bookings
• /notifications - Enable booking notifications
• /stop_notifications - Disable booking notifications

I'll automatically notify you when new bookings are added to the database!

Example: Type "show bookings" to see all current reservations
        """
        await update.message.reply_text(welcome_message.strip())

    async def help_command(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not update.message:
            return

        help_message = """
📋 **Available Commands:**

• **Basic Commands:**
  - `/start` - Welcome message and overview
  - `/help` - Show this help message

• **Booking Commands:**
  - `/bookings` - View all current bookings
  - `/notifications` - Enable automatic booking alerts
  - `/stop_notifications` - Disable booking alerts

• **Natural Language:**
  - Send messages like "show bookings" or "latest reservations"

**Examples:**
- `/bookings` - See all bookings
- `/notifications` - Get notified of new bookings
- "show me today's bookings"

I'll automatically alert you when new bookings are created! 🔔
        """
        await update.message.reply_text(help_message.strip(),
                                        parse_mode='Markdown')

    async def bookings_command(self, update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
        """Handle /bookings command to show all current bookings."""
        if not update.message:
            return

        try:
            bookings = await self.db_manager.get_all_bookings()
            if bookings:
                formatted_bookings = self._format_bookings_for_display(
                    bookings)
                await update.message.reply_text(formatted_bookings,
                                                parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    "📅 No bookings found in the database.")

        except Exception as e:
            logger.error(f"Error retrieving bookings: {e}")
            await update.message.reply_text(
                f"❌ Error retrieving bookings: {str(e)}\n\nPlease check your database connection."
            )

    async def notifications_command(self, update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
        """Handle /notifications command to enable booking notifications."""
        if not update.message:
            return

        chat_id = update.message.chat_id

        if chat_id in self.subscribers:
            await update.message.reply_text(
                "🔔 You're already subscribed to booking notifications!")
        else:
            self.subscribers.add(chat_id)
            await update.message.reply_text(
                "✅ Booking notifications enabled! I'll alert you when new bookings are created.",
                parse_mode='Markdown')
        logger.info(f"User {chat_id} subscribed to notifications")

    async def stop_notifications_command(self, update: Update,
                                         context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_notifications command to disable booking notifications."""
        if not update.message:
            return

        chat_id = update.message.chat_id

        if chat_id in self.subscribers:
            self.subscribers.remove(chat_id)
            await update.message.reply_text("🔕 Booking notifications disabled."
                                            )
        else:
            await update.message.reply_text(
                "🔕 You weren't subscribed to notifications.")
        logger.info(f"User {chat_id} unsubscribed from notifications")

    def _start_monitoring_sync(self):
        """Start monitoring in a separate thread for synchronous bot."""
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitor_new_bookings())
        except Exception as e:
            logger.error(f"Error in sync monitoring: {e}")

    async def monitor_new_bookings(self):
        """Monitor for new bookings and send notifications."""
        logger.info("Starting booking monitoring...")

        while True:
            try:
                # Get current bookings
                current_bookings = await self.db_manager.get_all_bookings()

                # Check for new bookings
                if current_bookings:
                    current_ids = {
                        str(booking.get('id', ''))
                        for booking in current_bookings
                    }

                    # Find new booking IDs
                    new_booking_ids = current_ids - self.known_booking_ids

                    if new_booking_ids and self.known_booking_ids:  # Don't notify on first run
                        # Get details of new bookings
                        new_bookings = [
                            b for b in current_bookings
                            if str(b.get('id', '')) in new_booking_ids
                        ]

                        # Send notifications to subscribers
                        for booking in new_bookings:
                            await self._notify_new_booking(booking)

                    # Update known booking IDs
                    self.known_booking_ids = current_ids

                # Wait before next check (30 seconds)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in booking monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _notify_new_booking(self, booking: Dict[str, Any]):
        """Send notification about a new booking to all subscribers."""
        try:
            booking_info = self._format_single_booking(booking)
            message = f"🎆 **New Booking Alert!**\n\n{booking_info}"

            # Send to all subscribers
            for chat_id in self.subscribers.copy(
            ):  # Use copy to avoid modification during iteration
                try:
                    if self.application and self.application.bot:
                        await self.application.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')
                except Exception as e:
                    logger.error(
                        f"Failed to send notification to {chat_id}: {e}")
                    # Remove invalid chat IDs
                    self.subscribers.discard(chat_id)

        except Exception as e:
            logger.error(f"Error formatting booking notification: {e}")

    async def handle_message(self, update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages."""
        if not update.message or not update.message.text:
            return

        message_text = update.message.text.lower()

        # Simple natural language processing for bookings
        if any(word in message_text for word in
               ['show', 'get', 'fetch', 'retrieve', 'see', 'list']):
            if any(word in message_text for word in
                   ['booking', 'bookings', 'reservation', 'reservations']):
                # Show bookings
                try:
                    bookings = await self.db_manager.get_all_bookings()

                    if not bookings:
                        await update.message.reply_text(
                            "📅 No bookings found in the database.")
                        return

                    formatted_bookings = self._format_bookings_for_display(
                        bookings)
                    await update.message.reply_text(formatted_bookings,
                                                    parse_mode='Markdown')

                except Exception as e:
                    logger.error(
                        f"Error in natural language booking query: {e}")
                    await update.message.reply_text(
                        f"❌ I couldn't retrieve bookings: {str(e)}\n\nTry using `/bookings` instead."
                    )
            else:
                await update.message.reply_text(
                    "I understand you want to see some data. Try:\n\n"
                    "• `/bookings` - to see all bookings\n"
                    "• 'show bookings' or 'list reservations'\n"
                    "• `/notifications` - to get notified of new bookings")

        elif any(word in message_text
                 for word in ['count', 'how many', 'total']):
            if any(word in message_text for word in
                   ['booking', 'bookings', 'reservation', 'reservations']):
                try:
                    count = await self.db_manager.count_bookings()
                    await update.message.reply_text(
                        f"📊 There are **{count}** total bookings in the database.",
                        parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Error counting bookings: {e}")
                    await update.message.reply_text(
                        f"❌ I couldn't count bookings: {str(e)}")
            else:
                await update.message.reply_text(
                    "I can help you count bookings. Try:\n\n"
                    "• 'How many bookings?' \n"
                    "• 'Count reservations'\n"
                    "• `/bookings` - to see all bookings")

        else:
            # Default response for unrecognized messages
            await update.message.reply_text(
                "I'm not sure how to help with that. Try:\n\n"
                "• `/help` - See available commands\n"
                "• `/bookings` - View all bookings\n"
                "• 'show bookings' - Natural language queries\n"
                "• `/notifications` - Get alerts for new bookings")

    def _format_data_for_display(self, data: list, table_name: str) -> str:
        """Format database data for Telegram display."""
        if not data:
            return f"No data found in table '{table_name}'."

        message = f"📊 **Data from '{table_name}' (showing {len(data)} rows):**\n\n"

        for i, row in enumerate(data[:10], 1):  # Limit to 10 rows
            message += f"**Row {i}:**\n"

            # Format each field in the row
            for key, value in row.items():
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 50:
                    str_value = str_value[:47] + "..."

                message += f"• *{key}*: {str_value}\n"

            message += "\n"

            # Telegram message length limit
            if len(message) > 3000:
                message += "... (truncated due to length limit)\n"
                break

        if len(data) > 10:
            message += f"\n*Note: Showing first 10 rows out of {len(data)} total rows.*"

        return message

    def _format_bookings_for_display(self, bookings: list) -> str:
        """Format booking data for Telegram display."""
        if not bookings:
            return "📅 No bookings found."

        message = f"📅 **Current Bookings ({len(bookings)} total):**\n\n"

        for i, booking in enumerate(bookings[:10], 1):  # Limit to 10 bookings
            booking_info = self._format_single_booking(booking)
            message += f"**Booking {i}:**\n{booking_info}\n\n"

            # Telegram message length limit
            if len(message) > 3000:
                message += "... (showing first 10 bookings)\n"
                break

        if len(bookings) > 10:
            message += f"\n*Showing 10 of {len(bookings)} total bookings.*"

        return message

    def _format_single_booking(self, booking: Dict[str, Any]) -> str:
        """Format a single booking for display - only room number, date, time, and package."""
        # Extract only the required fields
        room = booking.get('room_number', booking.get('room', 'N/A'))
        date = booking.get(
            'date', booking.get('check_in', booking.get('checkin_date','N/A')))
        time = booking.get('time', booking.get('booking_time', 'N/A'))
        package = booking.get('package', booking.get('package_type', 'N/A'))

        booking_info = f"• *Room*: {room}\n"
        booking_info += f"• *Date*: {date}\n"
        booking_info += f"• *Time*: {time}\n"
        booking_info += f"• *Package*: {package}"

        return booking_info
