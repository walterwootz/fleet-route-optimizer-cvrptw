#!/usr/bin/env python3
"""
MCP Server for Local SQLite Database
Provides database operations via MCP protocol
"""

import asyncio
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "railfleet.db")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("sqlite-local")


def get_db_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(DATABASE_PATH)


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available database resources"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    
    resources = [
        Resource(
            uri="sqlite://schema",
            name="Database Schema",
            mimeType="application/json",
            description="Complete database schema"
        )
    ]
    
    for table in tables:
        table_name = table[0]
        resources.append(
            Resource(
                uri=f"sqlite://{table_name}",
                name=f"{table_name} Table",
                mimeType="application/json",
                description=f"Data from {table_name} table"
            )
        )
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a database resource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if uri == "sqlite://schema":
        # Get schema information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "default": col[4],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        return json.dumps(schema, indent=2)
    
    elif uri.startswith("sqlite://"):
        # Get table data
        table = uri.replace("sqlite://", "")
        cursor.execute(f"SELECT * FROM {table} LIMIT 100")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Convert to dict
        data = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return json.dumps(data, indent=2, default=str)
    
    else:
        return json.dumps({"error": "Unknown resource"})


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available database tools"""
    return [
        Tool(
            name="query",
            description="Execute a SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="get_table_stats",
            description="Get statistics for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    }
                },
                "required": ["table"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute a database tool"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if name == "query":
            sql = arguments.get("sql", "")
            cursor.execute(sql)
            
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                result = {"rows": data, "count": len(data)}
            else:
                conn.commit()
                result = {"affected_rows": cursor.rowcount}
        
        elif name == "get_table_stats":
            table = arguments.get("table", "")
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            result = {
                "table": table,
                "row_count": count,
                "column_count": len(columns),
                "columns": [col[1] for col in columns]
            }
        
        else:
            result = {"error": "Unknown tool"}
        
        conn.close()
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        conn.close()
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

