"""Google Sheets Manager for Customer and Order Management"""

import logging
from typing import Dict, List
from datetime import datetime
from auth_google import get_credentials
from googleapiclient.discovery import build

logger = logging.getLogger('whatsapp-bot')


class SheetsManager:
    """Manage Google Sheets for responses, customers, and orders"""
    
    SHEETS = {
        'Respuestas': 'Sheet1!A:B',
        'Clientes': 'Clientes!A:D',
        'Pedidos': 'Pedidos!A:G'
    }
    
    def __init__(self, sheet_id: str):
        """Initialize Sheets Manager"""
        self.sheet_id = sheet_id
        self.creds = get_credentials()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self._ensure_sheets_exist()
    
    def _ensure_sheets_exist(self):
        """Ensure all required sheets exist"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()
            
            existing_sheets = {sheet['properties']['title'] for sheet in spreadsheet['sheets']}
            
            # Create Clientes sheet if doesn't exist
            if 'Clientes' not in existing_sheets:
                self._create_clientes_sheet()
            
            # Create Pedidos sheet if doesn't exist
            if 'Pedidos' not in existing_sheets:
                self._create_pedidos_sheet()
            
            logger.info('✅ All required sheets verified')
            
        except Exception as e:
            logger.error(f'❌ Error ensuring sheets exist: {e}')
    
    def _create_clientes_sheet(self):
        """Create Clientes sheet with headers"""
        try:
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': 'Clientes',
                                'index': 1
                            }
                        }
                    }
                ]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            
            # Add headers
            headers = [['Teléfono', 'Nombre', 'Primer Contacto', 'Último Contacto']]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='Clientes!A1:D1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            logger.info('✅ Clientes sheet created')
            
        except Exception as e:
            logger.error(f'❌ Error creating Clientes sheet: {e}')
    
    def _create_pedidos_sheet(self):
        """Create Pedidos sheet with headers"""
        try:
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': 'Pedidos',
                                'index': 2
                            }
                        }
                    }
                ]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            
            # Add headers
            headers = [['Teléfono', 'Producto', 'Cantidad', 'Precio', 'Fecha', 'Estado', 'Notas']]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='Pedidos!A1:G1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            logger.info('✅ Pedidos sheet created')
            
        except Exception as e:
            logger.error(f'❌ Error creating Pedidos sheet: {e}')
    
    def get_responses(self) -> Dict[str, str]:
        """Get responses from Respuestas sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Respuestas']
            ).execute()
            
            values = result.get('values', [])
            responses = {}
            
            # Skip header row
            for row in values[1:] if len(values) > 1 else []:
                if len(row) >= 2:
                    question = row[0].strip().lower()
                    answer = row[1].strip()
                    if question and answer:
                        responses[question] = answer
            
            return responses
            
        except Exception as e:
            logger.error(f'❌ Error getting responses: {e}')
            return {}
    
    def get_customers(self) -> Dict[str, Dict]:
        """Get customers from Clientes sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Clientes']
            ).execute()
            
            values = result.get('values', [])
            customers = {}
            
            # Skip header row
            for row in values[1:] if len(values) > 1 else []:
                if len(row) >= 1:
                    phone = row[0].strip()
                    if phone:
                        customers[phone] = {
                            'phone': phone,
                            'name': row[1] if len(row) > 1 else 'Unknown',
                            'first_contact': row[2] if len(row) > 2 else '',
                            'last_contact': row[3] if len(row) > 3 else ''
                        }
            
            return customers
            
        except Exception as e:
            logger.error(f'❌ Error getting customers: {e}')
            return {}
    
    def get_orders(self) -> List[Dict]:
        """Get orders from Pedidos sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Pedidos']
            ).execute()
            
            values = result.get('values', [])
            orders = []
            
            # Skip header row
            for row in values[1:] if len(values) > 1 else []:
                if len(row) >= 1:
                    order = {
                        'phone': row[0] if len(row) > 0 else '',
                        'product': row[1] if len(row) > 1 else '',
                        'quantity': row[2] if len(row) > 2 else '1',
                        'price': row[3] if len(row) > 3 else '0',
                        'date': row[4] if len(row) > 4 else '',
                        'status': row[5] if len(row) > 5 else 'Pendiente',
                        'notes': row[6] if len(row) > 6 else ''
                    }
                    orders.append(order)
            
            return orders
            
        except Exception as e:
            logger.error(f'❌ Error getting orders: {e}')
            return []
    
    def add_customer(self, phone: str, name: str, first_contact: str) -> bool:
        """Add new customer to Clientes sheet"""
        try:
            # Get current number of rows
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Clientes']
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Add new customer
            new_customer = [[phone, name, first_contact, datetime.now().isoformat()]]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f'Clientes!A{next_row}',
                valueInputOption='RAW',
                body={'values': new_customer}
            ).execute()
            
            logger.info(f'✅ Customer {phone} added to Clientes sheet')
            return True
            
        except Exception as e:
            logger.error(f'❌ Error adding customer: {e}')
            return False
    
    def add_order(self, phone: str, product: str, quantity: int, 
                  price: float, status: str, date: str) -> bool:
        """Add new order to Pedidos sheet"""
        try:
            # Get current number of rows
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Pedidos']
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Add new order
            new_order = [[phone, product, str(quantity), str(price), date, status, '']]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f'Pedidos!A{next_row}',
                valueInputOption='RAW',
                body={'values': new_order}
            ).execute()
            
            logger.info(f'✅ Order added for {phone}: {product}')
            return True
            
        except Exception as e:
            logger.error(f'❌ Error adding order: {e}')
            return False
    
    def close_order(self, phone: str, product: str) -> bool:
        """Mark order as completed (Completado)"""
        try:
            # Get all orders
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.SHEETS['Pedidos']
            ).execute()
            
            values = result.get('values', [])
            
            # Find and update order
            for idx, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
                if len(row) >= 2 and row[0] == phone and row[1].lower() == product.lower():
                    # Update status to Completado
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.sheet_id,
                        range=f'Pedidos!F{idx}',
                        valueInputOption='RAW',
                        body={'values': [['Completado']]}
                    ).execute()
                    
                    logger.info(f'✅ Order closed for {phone}: {product}')
                    return True
            
            logger.warning(f'⚠️ Order not found for {phone}: {product}')
            return False
            
        except Exception as e:
            logger.error(f'❌ Error closing order: {e}')
            return False
