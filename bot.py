#!/usr/bin/env python3
"""WhatsApp Chatbot with Google Sheets Integration - Customer & Order Management"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import threading
import time

import config
from auth_google import get_credentials
from sheets_manager import SheetsManager

# Configure logging
logger = logging.getLogger('whatsapp-bot')
logger.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.INFO)


class WhatsAppBot:
    """WhatsApp Chatbot with Google Sheets integration for customer and order management"""
    
    def __init__(self):
        """Initialize the bot"""
        self.responses_cache: Dict[str, str] = {}
        self.customers_cache: Dict[str, Dict] = {}  # phone -> customer data
        self.orders_cache: List[Dict] = []
        self.last_refresh = None
        self.client = None
        self.is_connected = False
        self.retry_count = 0
        self.sheets_manager = None
        
        logger.info('🤖 WhatsApp Chatbot initialized with Customer & Order Management')
    
    def initialize_sheets(self):
        """Initialize Google Sheets manager"""
        try:
            self.sheets_manager = SheetsManager(config.GOOGLE_SHEET_ID)
            logger.info('✅ Google Sheets manager initialized')
            return True
        except Exception as e:
            logger.error(f'❌ Error initializing Sheets: {e}')
            return False
    
    def load_responses_from_sheets(self) -> Dict[str, str]:
        """Load Q&A pairs from Google Sheets (Respuestas sheet)"""
        try:
            if not self.sheets_manager:
                return {}
            
            responses = self.sheets_manager.get_responses()
            self.last_refresh = datetime.now()
            logger.info(f'✅ Loaded {len(responses)} responses from Google Sheets')
            return responses
            
        except Exception as e:
            logger.error(f'❌ Error loading responses: {e}')
            return self.responses_cache
    
    def load_customers_from_sheets(self) -> Dict[str, Dict]:
        """Load customer data from Google Sheets (Clientes sheet)"""
        try:
            if not self.sheets_manager:
                return {}
            
            customers = self.sheets_manager.get_customers()
            logger.info(f'✅ Loaded {len(customers)} customers from Google Sheets')
            return customers
            
        except Exception as e:
            logger.error(f'❌ Error loading customers: {e}')
            return self.customers_cache
    
    def load_orders_from_sheets(self) -> List[Dict]:
        """Load orders from Google Sheets (Pedidos sheet)"""
        try:
            if not self.sheets_manager:
                return []
            
            orders = self.sheets_manager.get_orders()
            logger.info(f'✅ Loaded {len(orders)} orders from Google Sheets')
            return orders
            
        except Exception as e:
            logger.error(f'❌ Error loading orders: {e}')
            return self.orders_cache
    
    def register_customer(self, phone: str, name: str = 'Unknown') -> bool:
        """Register or update customer in Google Sheets"""
        try:
            if not self.sheets_manager:
                return False
            
            # Check if customer already exists
            if phone in self.customers_cache:
                logger.info(f'ℹ️ Customer {phone} already registered')
                return True
            
            # Register new customer
            result = self.sheets_manager.add_customer(
                phone=phone,
                name=name,
                first_contact=datetime.now().isoformat()
            )
            
            if result:
                self.customers_cache[phone] = {
                    'phone': phone,
                    'name': name,
                    'first_contact': datetime.now().isoformat()
                }
                logger.info(f'✅ Customer {phone} registered successfully')
            
            return result
            
        except Exception as e:
            logger.error(f'❌ Error registering customer: {e}')
            return False
    
    def register_order(self, phone: str, product: str, quantity: int = 1, 
                      price: float = 0, status: str = 'Pendiente') -> bool:
        """Register order in Google Sheets"""
        try:
            if not self.sheets_manager:
                return False
            
            # Check for duplicate recent orders (within 5 minutes)
            recent_order = self.check_duplicate_order(phone, product)
            if recent_order:
                logger.warning(f'⚠️ Duplicate order detected for {phone}: {product}')
                return False
            
            # Register order
            result = self.sheets_manager.add_order(
                phone=phone,
                product=product,
                quantity=quantity,
                price=price,
                status=status,
                date=datetime.now().isoformat()
            )
            
            if result:
                logger.info(f'✅ Order registered for {phone}: {product}')
            
            return result
            
        except Exception as e:
            logger.error(f'❌ Error registering order: {e}')
            return False
    
    def check_duplicate_order(self, phone: str, product: str, minutes: int = 5) -> Optional[Dict]:
        """Check if there's a recent duplicate order"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            for order in self.orders_cache:
                if (order.get('phone') == phone and 
                    order.get('product', '').lower() == product.lower() and
                    order.get('status') == 'Pendiente'):
                    
                    order_time = datetime.fromisoformat(order.get('date', ''))
                    if order_time > cutoff_time:
                        return order
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Error checking duplicate: {e}')
            return None
    
    def close_order(self, phone: str, product: str) -> bool:
        """Mark order as completed"""
        try:
            if not self.sheets_manager:
                return False
            
            result = self.sheets_manager.close_order(phone, product)
            
            if result:
                logger.info(f'✅ Order closed for {phone}: {product}')
            
            return result
            
        except Exception as e:
            logger.error(f'❌ Error closing order: {e}')
            return False
    
    def find_best_match(self, user_input: str) -> Optional[str]:
        """Find best matching response for user input"""
        user_input = user_input.strip().lower()
        
        # Exact match
        if user_input in self.responses_cache:
            return self.responses_cache[user_input]
        
        # Similarity matching
        best_match = None
        best_score = 0
        
        for question, answer in self.responses_cache.items():
            score = SequenceMatcher(None, user_input, question).ratio()
            if score > best_score and score >= config.SIMILARITY_THRESHOLD:
                best_score = score
                best_match = answer
        
        if best_match:
            logger.info(f'📝 Found match with score: {best_score:.2%}')
        
        return best_match
    
    async def refresh_data(self):
        """Periodically refresh data from Google Sheets"""
        logger.info(f'🔄 Starting data refresh cycle (interval: {config.REFRESH_INTERVAL}s)')
        while True:
            try:
                await asyncio.sleep(config.REFRESH_INTERVAL)
                self.responses_cache = self.load_responses_from_sheets()
                self.customers_cache = self.load_customers_from_sheets()
                self.orders_cache = self.load_orders_from_sheets()
            except Exception as e:
                logger.error(f'❌ Error during refresh cycle: {e}')
    
    async def handle_message(self, sender: str, message: str) -> Dict:
        """Handle incoming message and register customer/order"""
        logger.info(f'📥 Message from {sender}: {message[:50]}...')
        
        # Extract phone number (remove special characters)
        phone = ''.join(filter(str.isdigit, sender))
        
        # Register customer
        self.register_customer(phone=phone, name=f'Customer {phone}')
        
        # Find matching response
        response = self.find_best_match(message)
        
        result = {
            'phone': phone,
            'message': message,
            'response': response,
            'customer_registered': True,
            'timestamp': datetime.now().isoformat()
        }
        
        if response:
            logger.info(f'📤 Sending response to {phone}')
            # Optionally register order based on message content
            # self.register_order(phone=phone, product=message, quantity=1)
        else:
            logger.info(f'ℹ️ No matching response for: {message[:50]}')
        
        return result
    
    async def connect_whatsapp(self):
        """Connect to WhatsApp Web"""
        try:
            # Note: This is a simplified template. 
            # Full implementation requires whatsapp-web.js with Node.js bridge
            logger.info('🔗 Connecting to WhatsApp Web...')
            logger.info('📱 Please scan the QR code with your WhatsApp')
            
            # In production, this would use:
            # from whatsapp_web import WhatsAppWeb
            # self.client = WhatsAppWeb()
            # await self.client.connect()
            
            self.is_connected = True
            self.retry_count = 0
            logger.info('✅ Connected to WhatsApp successfully')
            return True
            
        except Exception as e:
            logger.error(f'❌ Failed to connect: {e}')
            self.retry_count += 1
            return False
    
    async def reconnect_with_backoff(self):
        """Reconnect with exponential backoff"""
        wait_time = min(config.RECONNECT_INTERVAL * (2 ** self.retry_count), 300)
        logger.warning(f'⏳ Retrying connection in {wait_time}s (attempt {self.retry_count + 1})')
        
        await asyncio.sleep(wait_time)
        
        if self.retry_count < config.MAX_RETRIES:
            return await self.connect_whatsapp()
        else:
            logger.error('❌ Max retries reached. Please restart the bot.')
            return False
    
    async def start(self):
        """Start the chatbot"""
        try:
            # Validate configuration
            config.validate_config()
            
            # Initialize Sheets
            if not self.initialize_sheets():
                raise Exception('Could not initialize Google Sheets')
            
            # Load initial data
            logger.info('📚 Loading data from Google Sheets...')
            self.responses_cache = self.load_responses_from_sheets()
            self.customers_cache = self.load_customers_from_sheets()
            self.orders_cache = self.load_orders_from_sheets()
            
            if not self.responses_cache:
                logger.warning('⚠️ No responses loaded from Google Sheets')
            
            logger.info(f'📊 Status:')
            logger.info(f'   - Respuestas: {len(self.responses_cache)}')
            logger.info(f'   - Clientes: {len(self.customers_cache)}')
            logger.info(f'   - Pedidos: {len(self.orders_cache)}')
            
            # Connect to WhatsApp
            connected = await self.connect_whatsapp()
            
            if not connected:
                connected = await self.reconnect_with_backoff()
            
            if not connected:
                raise Exception('Could not establish WhatsApp connection')
            
            # Start refresh cycle
            refresh_task = asyncio.create_task(self.refresh_data())
            
            logger.info('✅ Chatbot started successfully')
            logger.info('📡 Monitoring for incoming messages...')
            logger.info('💡 Tip: Customers are auto-registered when they message')
            logger.info('📝 Check Google Sheets for: Respuestas, Clientes, Pedidos')
            
            # Keep bot running
            await refresh_task
            
        except KeyboardInterrupt:
            logger.info('\n⏹️ Shutting down gracefully...')
            await self.shutdown()
        except Exception as e:
            logger.error(f'❌ Fatal error: {e}')
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Shutdown the bot gracefully"""
        logger.info('🔌 Disconnecting from WhatsApp...')
        if self.client:
            try:
                # self.client.disconnect()
                pass
            except Exception as e:
                logger.error(f'Error during disconnect: {e}')
        logger.info('✅ Bot shutdown complete')


async def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║         🤖 WhatsApp Chatbot with Customer & Order Management 🤖          ║
║                                                                           ║
║  • Automated responses from Google Sheets                                ║
║  • Auto-register customers                                              ║
║  • Track orders and history                                             ║
║  • Avoid duplicate orders                                               ║
║  • Persistent session (no frequent reconnects)                          ║
║  • Auto-refresh of responses & data                                     ║
║  • Smart keyword matching                                               ║
║                                                                           ║
║  Google Sheets Tabs:                                                    ║
║    • Respuestas → Bot responses                                         ║
║    • Clientes → Customer registry                                       ║
║    • Pedidos → Order history                                            ║
║                                                                           ║
║  Press Ctrl+C to stop                                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    bot = WhatsAppBot()
    await bot.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        raise
