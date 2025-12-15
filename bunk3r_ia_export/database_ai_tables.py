    def initialize_ai_tables(self):
        """Inicializar tablas para sistema de chat con IA"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(CREATE_AI_CHAT_SQL)
                    conn.commit()
            logger.info("AI chat tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing AI chat tables: {e}")
            return False
    
    def get_virtual_number_setting(self, key: str, default: str = None) -> str:
        """Obtener configuracion de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT setting_value FROM virtual_number_settings WHERE setting_key = %s",
                        (key,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else default
        except Exception as e:
            logger.error(f"Error getting virtual number setting {key}: {e}")
            return default
    
    def set_virtual_number_setting(self, key: str, value: str) -> bool:
        """Establecer configuracion de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO virtual_number_settings (setting_key, setting_value, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (setting_key) DO UPDATE 
                        SET setting_value = EXCLUDED.setting_value, updated_at = CURRENT_TIMESTAMP
                    """, (key, value))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error setting virtual number setting {key}: {e}")
            return False
    
    def get_all_virtual_number_settings(self) -> dict:
        """Obtener todas las configuraciones de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT setting_key, setting_value FROM virtual_number_settings")
                    settings = {}
                    for row in cur.fetchall():
                        settings[row['setting_key']] = row['setting_value']
                    return settings
        except Exception as e:
            logger.error(f"Error getting all virtual number settings: {e}")
            return {}
    
    def get_virtual_number_stats(self, days: int = 30) -> dict:
        """Obtener estadisticas de numeros virtuales"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_orders,
                            COUNT(CASE WHEN status = 'received' THEN 1 END) as successful,
                            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
                            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                            COALESCE(SUM(bunkercoin_charged), 0) as total_revenue,
                            COALESCE(SUM(cost_usd), 0) as total_cost,
                            COALESCE(SUM(cost_with_commission - cost_usd), 0) as total_profit_usd
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                    """, (days,))
                    result = cur.fetchone()
                    
                    cur.execute("""
                        SELECT 
                            DATE(created_at) as date,
                            COUNT(*) as orders,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY DATE(created_at)
                        ORDER BY date DESC
                    """)
                    daily_stats = [dict(row) for row in cur.fetchall()]
                    
                    cur.execute("""
                        SELECT 
                            COALESCE(service_name, service_code) as service,
                            COUNT(*) as count,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY COALESCE(service_name, service_code)
                        ORDER BY count DESC
                        LIMIT 10
                    """, (days,))
                    top_services = [dict(row) for row in cur.fetchall()]
                    
                    cur.execute("""
                        SELECT 
                            COALESCE(country_name, country_code) as country,
                            COUNT(*) as count,
                            COALESCE(SUM(bunkercoin_charged), 0) as revenue
                        FROM virtual_number_orders
                        WHERE created_at >= NOW() - INTERVAL '%s days'
                        GROUP BY COALESCE(country_name, country_code)
                        ORDER BY count DESC
