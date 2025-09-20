# Overview

This is a Telegram bot application that provides booking management and monitoring functionality through integration with a Supabase database. The bot allows users to view current bookings, receive automatic notifications when new bookings are created, and interact with booking data through natural language commands. The application serves as a real-time booking management interface through Telegram's messaging platform.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Architecture
The application follows a modular design with separation of concerns:
- **TelegramBot class**: Handles all Telegram-specific operations including command processing, message handling, and user interactions
- **SupabaseManager class**: Manages database connections and operations, abstracting Supabase client interactions
- **Main entry point**: Coordinates application startup, environment configuration, and error handling

# Recent Changes

Latest modifications on August 27, 2025:
- **Transformed to Booking Management Bot**: Changed focus from generic database operations to booking-specific functionality
- **Added Automatic Notifications**: Implemented real-time monitoring for new bookings with subscriber alerts
- **Updated Commands**: Replaced generic table commands with booking-focused commands
- **Enhanced Natural Language Processing**: Added booking-specific natural language understanding

## Command Processing
The bot implements a booking-focused command interface with handlers for:
- `/start` and `/help` for user onboarding
- `/bookings` for viewing all current bookings and reservations
- `/notifications` for enabling automatic booking alerts
- `/stop_notifications` for disabling booking alerts
- Message handler for booking-related conversational queries
- **Real-time monitoring**: Automatic background task that checks for new bookings every 30 seconds

## Database Integration
The system uses Supabase's Python client for database operations with connection pooling and error handling. The SupabaseManager provides an abstraction layer that could be extended to support other database backends in the future.

## Configuration Management
Environment-based configuration using dotenv for secure credential management, separating sensitive data from code.

## Error Handling and Logging
Comprehensive logging system with structured error handling across all components, enabling debugging and monitoring of bot operations.

# External Dependencies

## Core Services
- **Telegram Bot API**: Primary interface for user interactions through the python-telegram-bot library
- **Supabase**: Database backend providing PostgreSQL database services with real-time capabilities and built-in authentication

## Python Libraries
- **python-telegram-bot**: Official Telegram bot framework for handling updates, commands, and messages
- **supabase-py**: Official Python client for Supabase database operations
- **python-dotenv**: Environment variable management for configuration
- **asyncio**: Asynchronous programming support for concurrent bot operations

## Environment Variables
- `TELEGRAM_BOT_TOKEN`: Authentication token for Telegram Bot API access
- `SUPABASE_URL`: Supabase project URL endpoint
- `SUPABASE_KEY`: Supabase API key for database authentication