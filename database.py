"""
Supabase database manager for the Telegram bot.
"""

import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages Supabase database operations."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase client."""
        self.url = supabase_url
        self.key = supabase_key
        self.client: Client = create_client(supabase_url, supabase_key)
        self._connect()
    
    def _connect(self):
        """Establish connection to Supabase."""
        try:
            self.client = create_client(self.url, self.key)
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    async def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        Note: This is a simplified approach. In production, you might want to
        query the information_schema or maintain a list of known tables.
        """
        try:
            # Since Supabase doesn't provide a direct way to list tables,
            # we'll attempt to query common table names or use RPC
            
            # Try to use a stored procedure if available
            try:
                response = self.client.rpc('get_table_names').execute()
                if response.data:
                    return response.data
            except Exception:
                # Fallback: return a message explaining the limitation
                logger.warning("Could not retrieve table list via RPC")
            
            # Alternative: Try to query information_schema (if permissions allow)
            try:
                response = self.client.from_('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
                if response.data:
                    return [table['table_name'] for table in response.data]
            except Exception:
                logger.warning("Could not access information_schema")
            
            # If all methods fail, return an informative message
            return ["Unable to list tables automatically. Please specify table names directly."]
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            raise Exception(f"Failed to list tables: {str(e)}")
    
    async def query_table(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query data from a specific table."""
        try:
            if not table_name or not table_name.strip():
                raise ValueError("Table name cannot be empty")
            
            # Sanitize table name to prevent injection
            table_name = table_name.strip().replace(';', '').replace('--', '')
            
            response = self.client.from_(table_name).select('*').limit(limit).execute()
            
            if response.data is None:
                return []
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error querying table {table_name}: {e}")
            raise Exception(f"Failed to query table '{table_name}': {str(e)}")
    
    async def count_rows(self, table_name: str) -> int:
        """Count the number of rows in a table."""
        try:
            if not table_name or not table_name.strip():
                raise ValueError("Table name cannot be empty")
            
            # Sanitize table name
            table_name = table_name.strip().replace(';', '').replace('--', '')
            
            response = self.client.from_(table_name).select('*').execute()
            
            return len(response.data) if response.data is not None else 0
            
        except Exception as e:
            logger.error(f"Error counting rows in table {table_name}: {e}")
            raise Exception(f"Failed to count rows in table '{table_name}': {str(e)}")
    
    async def execute_custom_query(self, table_name: str, filters: Optional[Dict[str, Any]] = None, 
                                 columns: str = '*', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Execute a custom query with filters.
        
        Args:
            table_name: Name of the table to query
            filters: Dictionary of column:value pairs for filtering
            columns: Comma-separated string of columns to select
            limit: Maximum number of rows to return
        """
        try:
            if not table_name or not table_name.strip():
                raise ValueError("Table name cannot be empty")
            
            # Sanitize table name
            table_name = table_name.strip().replace(';', '').replace('--', '')
            
            query = self.client.from_(table_name).select(columns)
            
            # Apply filters if provided
            if filters is not None:
                for column, value in filters.items():
                    # Sanitize column name
                    column = column.strip().replace(';', '').replace('--', '')
                    query = query.eq(column, value)
            
            response = query.limit(limit).execute()
            
            return response.data if response.data is not None else []
            
        except Exception as e:
            logger.error(f"Error executing custom query on table {table_name}: {e}")
            raise Exception(f"Failed to execute custom query: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            # Try a simple operation to test connection
            self.client.from_('test_connection').select('1').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings from the bookings table."""
        try:
            # Try common booking table names
            table_names = ['bookings', 'reservations', 'booking', 'reservation']
            
            for table_name in table_names:
                try:
                    response = self.client.from_(table_name).select('*').order('created_at', desc=True).execute()
                    
                    if response.data is not None:
                        logger.info(f"Found {len(response.data)} bookings in table '{table_name}'")
                        return response.data
                except Exception as table_error:
                    logger.debug(f"Table '{table_name}' not found or accessible: {table_error}")
                    continue
            
            # If no standard table found, return empty list
            logger.warning("No booking table found. Tried: bookings, reservations, booking, reservation")
            return []
            
        except Exception as e:
            logger.error(f"Error getting bookings: {e}")
            raise Exception(f"Failed to retrieve bookings: {str(e)}")
    
    async def get_recent_bookings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent bookings with a limit."""
        try:
            table_names = ['bookings', 'reservations', 'booking', 'reservation']
            
            for table_name in table_names:
                try:
                    response = self.client.from_(table_name).select('*').order('created_at', desc=True).limit(limit).execute()
                    
                    if response.data is not None:
                        return response.data
                except Exception:
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent bookings: {e}")
            raise Exception(f"Failed to retrieve recent bookings: {str(e)}")
    
    async def count_bookings(self) -> int:
        """Count total number of bookings."""
        try:
            table_names = ['bookings', 'reservations', 'booking', 'reservation']
            
            for table_name in table_names:
                try:
                    response = self.client.from_(table_name).select('*').execute()
                    if response.data is not None:
                        return len(response.data)
                except Exception:
                    continue
            
            return 0
            
        except Exception as e:
            logger.error(f"Error counting bookings: {e}")
            return 0
