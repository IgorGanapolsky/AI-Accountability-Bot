#!/usr/bin/env python3
"""
Setup script for creating Airtable tables required by the AI Accountability Bot.
"""
import requests
import os
from dotenv import load_dotenv

def create_table(base_id: str, table_name: str, fields: list, description: str, api_key: str) -> bool:
    """Create an Airtable table with the specified schema"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    table_data = {
        "name": table_name,
        "description": description,
        "fields": fields
    }
    
    url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
    
    try:
        response = requests.post(url, headers=headers, json=table_data, timeout=60)
        response.raise_for_status()
        print(f"✅ Created {table_name} table successfully!")
        return True
    except requests.exceptions.RequestException as e:
        if "already exists" in str(e):
            print(f"ℹ️ {table_name} table already exists.")
            return True
        print(f"❌ Error creating {table_name} table: {str(e)}")
        return False

def setup_airtable():
    """Set up all required Airtable tables"""
    load_dotenv()
    
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or not base_id:
        print("❌ Error: Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID in .env file")
        return False
    
    # Tasks table schema
    tasks_fields = [
        {
            "name": "Title",
            "type": "singleLineText",
            "description": "Task title"
        },
        {
            "name": "Description",
            "type": "multilineText",
            "description": "Task description"
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Todo"},
                    {"name": "In Progress"},
                    {"name": "Done"}
                ]
            },
            "description": "Current status of the task"
        },
        {
            "name": "Due Date",
            "type": "date",
            "description": "When the task is due"
        },
        {
            "name": "Priority",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "High"},
                    {"name": "Medium"},
                    {"name": "Low"}
                ]
            },
            "description": "Task priority"
        },
        {
            "name": "Created At",
            "type": "dateTime",
            "description": "When the task was created"
        }
    ]
    
    # Repositories table schema
    repos_fields = [
        {
            "name": "Repository Name",
            "type": "singleLineText",
            "description": "Name of the repository"
        },
        {
            "name": "Description",
            "type": "multilineText",
            "description": "Repository description"
        },
        {
            "name": "URL",
            "type": "url",
            "description": "Repository URL"
        },
        {
            "name": "Created At",
            "type": "dateTime",
            "description": "When the repository was added"
        },
        {
            "name": "Last Updated",
            "type": "dateTime",
            "description": "When the repository was last updated"
        }
    ]
    
    # Create tables
    success = True
    success &= create_table(
        base_id=base_id,
        table_name="Tasks",
        fields=tasks_fields,
        description="Task management for AI Accountability Bot",
        api_key=api_key
    )
    
    success &= create_table(
        base_id=base_id,
        table_name="Repositories",
        fields=repos_fields,
        description="Repository management for AI Accountability Bot",
        api_key=api_key
    )
    
    if success:
        print("\n✨ Airtable setup completed successfully!")
        print("\nNext steps:")
        print("1. Open your Airtable base and verify the tables were created")
        print("2. Start the bot with: python -m src.cli.main")
    else:
        print("\n❌ Airtable setup failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    setup_airtable()
