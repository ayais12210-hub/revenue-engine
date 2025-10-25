#!/usr/bin/env python3
"""
Database Migration Runner
Runs database migrations in order and tracks migration status
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from pathlib import Path
from typing import List, Tuple
import argparse

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        
    def connect(self):
        """Connect to the database"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")
    
    def create_migrations_table(self):
        """Create the migrations tracking table"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMP DEFAULT NOW(),
            checksum VARCHAR(64),
            status VARCHAR(20) DEFAULT 'completed'
        );
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            logger.info("Migrations table created/verified")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def get_executed_migrations(self) -> List[str]:
        """Get list of already executed migrations"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT filename FROM migrations WHERE status = 'completed' ORDER BY id")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get executed migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of pending migrations"""
        migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
        executed = self.get_executed_migrations()
        
        pending = []
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            if migration_file.name not in executed:
                pending.append((migration_file.name, migration_file))
        
        return pending
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def execute_migration(self, filename: str, file_path: Path) -> bool:
        """Execute a single migration file"""
        logger.info(f"Executing migration: {filename}")
        
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Calculate checksum
            checksum = self.calculate_checksum(file_path)
            
            # Start transaction
            with self.connection.cursor() as cursor:
                # Record migration start
                cursor.execute("""
                    INSERT INTO migrations (filename, checksum, status) 
                    VALUES (%s, %s, 'running')
                    ON CONFLICT (filename) DO UPDATE SET 
                        checksum = EXCLUDED.checksum,
                        status = 'running',
                        executed_at = NOW()
                """, (filename, checksum))
                
                # Execute migration SQL
                cursor.execute(migration_sql)
                
                # Mark as completed
                cursor.execute("""
                    UPDATE migrations 
                    SET status = 'completed' 
                    WHERE filename = %s
                """, (filename,))
                
            logger.info(f"Migration {filename} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration {filename} failed: {e}")
            try:
                # Mark as failed
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE migrations 
                        SET status = 'failed' 
                        WHERE filename = %s
                    """, (filename,))
            except:
                pass
            return False
    
    def run_migrations(self, force: bool = False):
        """Run all pending migrations"""
        logger.info("Starting database migration process")
        
        try:
            self.connect()
            self.create_migrations_table()
            
            pending = self.get_pending_migrations()
            
            if not pending:
                logger.info("No pending migrations found")
                return True
            
            logger.info(f"Found {len(pending)} pending migrations")
            
            success_count = 0
            for filename, file_path in pending:
                if self.execute_migration(filename, file_path):
                    success_count += 1
                else:
                    if not force:
                        logger.error(f"Migration failed: {filename}. Use --force to continue with remaining migrations.")
                        return False
            
            logger.info(f"Migration process completed: {success_count}/{len(pending)} migrations successful")
            return success_count == len(pending)
            
        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False
        finally:
            self.disconnect()
    
    def rollback_migration(self, filename: str):
        """Rollback a specific migration (mark as failed)"""
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE migrations 
                    SET status = 'failed' 
                    WHERE filename = %s
                """, (filename,))
            logger.info(f"Migration {filename} marked as failed")
        except Exception as e:
            logger.error(f"Failed to rollback migration {filename}: {e}")
        finally:
            self.disconnect()
    
    def show_status(self):
        """Show migration status"""
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT filename, status, executed_at, checksum 
                    FROM migrations 
                    ORDER BY executed_at
                """)
                
                migrations = cursor.fetchall()
                
                if not migrations:
                    logger.info("No migrations found")
                    return
                
                logger.info("Migration Status:")
                logger.info("-" * 80)
                logger.info(f"{'Filename':<30} {'Status':<12} {'Executed At':<20} {'Checksum':<12}")
                logger.info("-" * 80)
                
                for filename, status, executed_at, checksum in migrations:
                    status_icon = "✓" if status == "completed" else "✗" if status == "failed" else "⏳"
                    logger.info(f"{filename:<30} {status_icon} {status:<11} {executed_at.strftime('%Y-%m-%d %H:%M:%S') if executed_at else 'N/A':<20} {checksum[:12] if checksum else 'N/A':<12}")
                
        except Exception as e:
            logger.error(f"Failed to show migration status: {e}")
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    parser.add_argument("--database-url", help="Database URL (overrides DATABASE_URL env var)")
    parser.add_argument("--force", action="store_true", help="Continue with remaining migrations if one fails")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--rollback", help="Rollback a specific migration by filename")
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Database URL not provided. Set DATABASE_URL environment variable or use --database-url")
        sys.exit(1)
    
    migrator = DatabaseMigrator(database_url)
    
    if args.status:
        migrator.show_status()
    elif args.rollback:
        migrator.rollback_migration(args.rollback)
    else:
        success = migrator.run_migrations(force=args.force)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()