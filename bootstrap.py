#!/usr/bin/env python3
"""
Bootstrap script to initialize the MySQL database and load initial data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Todo
from auth import get_password_hash
from datetime import datetime, timedelta
import time

def wait_for_mysql(database_url, max_retries=30, retry_interval=2):
    """Wait for MySQL to be ready"""
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    
    print("Waiting for MySQL to be ready...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            connection = engine.connect()
            connection.close()
            print("MySQL is ready!")
            return engine
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"MySQL not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print(f"Failed to connect to MySQL after {max_retries} attempts")
                raise e

def create_initial_data():
    """Create initial users and todos for demonstration"""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "mysql+pymysql://mytodo:mytodo123@mysql:3306/mytodo")
    
    # Wait for MySQL and create engine
    engine = wait_for_mysql(database_url)
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_user = db.query(User).filter(User.username == "demo").first()
        if existing_user:
            print("Initial data already exists. Skipping bootstrap.")
            return
        
        print("Creating initial demo data...")
        
        # Create demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            first_name="Demo",
            last_name="User",
            mobile_no="+1234567890",
            hashed_password=get_password_hash("demo123")
        )
        db.add(demo_user)
        db.flush()  # To get the user ID
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            mobile_no="+1987654321",
            hashed_password=get_password_hash("admin")
        )
        db.add(admin_user)
        db.flush()  # To get the user ID
        
        # Create sample todos for demo user
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        sample_todos = [
            Todo(
                title="Welcome to MyTodo!",
                description="This is your first todo item. Try marking it as complete!",
                due_date=today,
                owner_id=demo_user.id
            ),
            Todo(
                title="Plan your week",
                description="Create a list of tasks you want to accomplish this week",
                due_date=tomorrow,
                owner_id=demo_user.id
            ),
            Todo(
                title="Review project requirements",
                description="Go through the project specification and make notes",
                due_date=next_week,
                owner_id=demo_user.id
            ),
            Todo(
                title="Setup development environment",
                description="Install necessary tools and configure your workspace",
                completed=True,
                due_date=today - timedelta(days=1),
                owner_id=demo_user.id
            ),
            Todo(
                title="Learn about the application",
                description="Explore different features like filtering, editing, and date selection",
                owner_id=demo_user.id
            )
        ]
        
        # Add sample todos for admin user
        admin_todos = [
            Todo(
                title="System maintenance",
                description="Perform regular system checks and updates",
                due_date=today + timedelta(days=3),
                owner_id=admin_user.id
            ),
            Todo(
                title="User feedback review",
                description="Review and respond to user feedback and feature requests",
                due_date=next_week,
                owner_id=admin_user.id
            ),
            Todo(
                title="Database backup",
                description="Ensure regular database backups are working properly",
                completed=True,
                due_date=today - timedelta(days=2),
                owner_id=admin_user.id
            )
        ]
        
        # Add all todos to database
        for todo in sample_todos + admin_todos:
            db.add(todo)
        
        # Commit all changes
        db.commit()
        
        print("✅ Successfully created initial data:")
        print(f"   - Demo user: username='demo', password='demo123'")
        print(f"   - Admin user: username='admin', password='admin'")
        print(f"   - {len(sample_todos)} sample todos for demo user")
        print(f"   - {len(admin_todos)} sample todos for admin user")
        print("\nYou can now login with these credentials to explore the application!")
        
    except Exception as e:
        print(f"Error creating initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting MyTodo Bootstrap Process...")
    create_initial_data()
    print("✅ Bootstrap completed successfully!")