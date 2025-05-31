"""
MCP (Model Context Protocol) tool integration.

Simple functions to load tools from MCP servers.
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import logging
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Don't log warning here - will log when needed


async def load_mcp_server(server_command: List[str]) -> List[Dict[str, Any]]:
    """Load tools from a single MCP server."""
    if not MCP_AVAILABLE:
        return []
    
    try:
        server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:] if len(server_command) > 1 else []
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools_result = await session.list_tools()
                
                # Convert to simple dict format
                tools = []
                for tool_info in tools_result.tools:
                    tools.append({
                        "name": tool_info.name,
                        "description": tool_info.description,
                        "schema": tool_info.inputSchema.model_dump() if tool_info.inputSchema else {},
                        "session": session  # Keep reference for execution
                    })
                
                logging.info(f"Loaded {len(tools)} tools from MCP server")
                return tools
                
    except Exception as e:
        logging.error(f"Failed to load MCP server {server_command}: {e}")
        return []


async def load_mcp_tools_async(config_path: Union[str, Path] = None) -> List[Dict[str, Any]]:
    """Load all tools from MCP servers defined in config (async version)."""
    if not MCP_AVAILABLE:
        logging.warning("MCP not available. Install with: pip install mcp")
        return []
    
    if config_path is None:
        # Look for common MCP config locations
        possible_paths = [
            Path.home() / ".mcp" / "config.json",
            Path.cwd() / "mcp_config.json",
            Path.cwd() / ".mcp" / "config.json"
        ]
        config_path = next((p for p in possible_paths if p.exists()), None)
    
    if config_path is None:
        logging.info("No MCP configuration file found")
        return []
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        all_tools = []
        for server_name, server_config in config.get('servers', {}).items():
            command = server_config.get('command', [])
            if command:
                tools = await load_mcp_server(command)
                all_tools.extend(tools)
        
        logging.info(f"Loaded {len(all_tools)} total tools from MCP servers")
        return all_tools
        
    except Exception as e:
        logging.error(f"Failed to load MCP config from {config_path}: {e}")
        return []

def load_mcp_tools(config_path: Union[str, Path] = None) -> List[Dict[str, Any]]:
    """Load all tools from MCP servers defined in config (sync wrapper)."""
    return asyncio.run(load_mcp_tools_async(config_path))


async def get_tools_by_names_async(tool_names: List[str], available_tools: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Filter tools by requested names (async version)."""
    if available_tools is None:
        available_tools = await load_mcp_tools_async()
    
    if not tool_names:
        return available_tools
    
    filtered_tools = []
    
    for name in tool_names:
        tool = next((t for t in available_tools if t["name"] == name), None)
        if tool:
            filtered_tools.append(tool)
        else:
            logging.warning(f"Tool '{name}' not found in MCP servers")
    
    return filtered_tools

def get_tools_by_names(tool_names: List[str], available_tools: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Filter tools by requested names (sync wrapper)."""
    return asyncio.run(get_tools_by_names_async(tool_names, available_tools))


def create_mcp_config_template(config_path: Union[str, Path] = None) -> Path:
    """Create a template MCP configuration file."""
    if config_path is None:
        config_path = Path.cwd() / "mcp_config.json"
    else:
        config_path = Path(config_path)
    
    template_config = {
        "servers": {
            "filesystem": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
                "args": ["--root", str(Path.cwd())]
            },
            "web": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-web"]
            },
            "git": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-git"],
                "args": ["--repository", str(Path.cwd())]
            }
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(template_config, f, indent=2)
    
    logging.info(f"Created MCP config template at {config_path}")
    return config_path