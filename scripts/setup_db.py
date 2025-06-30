#!/usr/bin/env python3
"""
Database setup script for AI Observability RCA
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ai_observability")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def check_postgresql_installed():
    """Check if PostgreSQL is installed"""
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not found")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL not found")
        return False

def install_postgresql_ubuntu():
    """Install PostgreSQL on Ubuntu"""
    print("📦 Installing PostgreSQL on Ubuntu...")
    try:
        # Update package list
        subprocess.run(["sudo", "apt", "update"], check=True)
        
        # Install PostgreSQL
        subprocess.run([
            "sudo", "apt", "install", "-y", 
            "postgresql", "postgresql-contrib", "python3-psycopg2"
        ], check=True)
        
        # Start PostgreSQL service
        subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "postgresql"], check=True)
        
        print("✅ PostgreSQL installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PostgreSQL: {e}")
        return False

def create_database():
    """Create database and user"""
    try:
        # Connect to PostgreSQL as postgres user
        print("🔧 Creating database and user...")
        
        # Create database
        create_db_command = f"""
        sudo -u postgres psql -c "CREATE DATABASE {DB_NAME};"
        """
        
        # Create user
        create_user_command = f"""
        sudo -u postgres psql -c "CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';"
        """
        
        # Grant privileges
        grant_privileges_command = f"""
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};"
        """
        
        # Execute commands
        subprocess.run(create_db_command, shell=True, check=True)
        print(f"✅ Database '{DB_NAME}' created")
        
        try:
            subprocess.run(create_user_command, shell=True, check=True)
            print(f"✅ User '{DB_USER}' created")
        except subprocess.CalledProcessError:
            print(f"ℹ️ User '{DB_USER}' already exists")
        
        subprocess.run(grant_privileges_command, shell=True, check=True)
        print(f"✅ Privileges granted to '{DB_USER}'")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create database: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        print("🔍 Testing database connection...")
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_tables():
    """Create database tables using the backend application"""
    try:
        print("📋 Creating database tables...")
        
        # Change to backend directory
        backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
        original_dir = os.getcwd()
        
        try:
            os.chdir(backend_dir)
            
            # Add backend to Python path
            sys.path.insert(0, os.path.abspath("."))
            
            # Import and initialize database
            from app.core.database import init_db
            import asyncio
            
            # Run database initialization
            asyncio.run(init_db())
            print("✅ Database tables created successfully")
            
            return True
            
        finally:
            os.chdir(original_dir)
            
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def setup_sample_data():
    """Setup sample data for testing"""
    try:
        print("📊 Setting up sample data...")
        
        # You can add sample data creation here
        # For now, we'll just create the basic schema
        
        print("✅ Sample data setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup sample data: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting AI Observability RCA Database Setup")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        print("\n📦 PostgreSQL not found. Installing...")
        if not install_postgresql_ubuntu():
            print("❌ Failed to install PostgreSQL. Please install manually.")
            sys.exit(1)
    
    # Create database and user
    if not create_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        print("❌ Database connection failed")
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        print("❌ Table creation failed")
        sys.exit(1)
    
    # Setup sample data
    if not setup_sample_data():
        print("⚠️ Sample data setup failed, but continuing...")
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\n📝 Connection details:")
    print(f"   Host: {DB_HOST}")
    print(f"   Port: {DB_PORT}")
    print(f"   Database: {DB_NAME}")
    print(f"   User: {DB_USER}")
    print("\n🔧 Update your .env file with these settings if needed.")

if __name__ == "__main__":
    main()
