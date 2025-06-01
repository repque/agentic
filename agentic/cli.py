"""
CLI interface for testing agents in a chat environment.

Provides an interactive chat interface similar to Claude Code for agent testing.
"""

import asyncio
import sys
import os
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import click

from .agent import Agent
from .models import Message


class ChatSession:
    """Manages a multi-user chat session with an agent."""
    
    def __init__(self, agent: Agent, initial_user_id: str = "test_user"):
        self.agent = agent
        self.current_user_id = initial_user_id
        self.users: Dict[str, Dict[str, Any]] = {}
        self.global_history: List[Dict[str, Any]] = []
        self.session_start = datetime.now()
        
        # Initialize the first user
        self.add_user(initial_user_id)
    
    def add_user(self, user_id: str):
        """Add a new user to the session."""
        if user_id not in self.users:
            self.users[user_id] = {
                "join_time": datetime.now(),
                "message_count": 0,
                "last_active": datetime.now()
            }
    
    def switch_user(self, user_id: str):
        """Switch to a different user."""
        self.add_user(user_id)  # Add if doesn't exist
        self.current_user_id = user_id
        self.users[user_id]["last_active"] = datetime.now()
    
    def get_current_user(self) -> str:
        """Get the current active user ID."""
        return self.current_user_id
    
    def list_users(self) -> List[str]:
        """Get list of all users in the session."""
        return list(self.users.keys())
    
    async def send_message(self, message: str) -> str:
        """Send a message to the agent and get response."""
        current_time = datetime.now()
        
        # Update user stats
        self.users[self.current_user_id]["message_count"] += 1
        self.users[self.current_user_id]["last_active"] = current_time
        
        # Record user message
        user_entry = {
            "timestamp": current_time.isoformat(),
            "type": "user",
            "user_id": self.current_user_id,
            "content": message,
            "workflow_step": None
        }
        self.global_history.append(user_entry)
        
        try:
            # Get agent response
            response = await self.agent.chat(message, self.current_user_id)
            
            # Record agent response
            agent_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "assistant", 
                "responding_to_user": self.current_user_id,
                "content": response,
                "workflow_step": getattr(self.agent._workflow, 'last_step', None) if hasattr(self.agent, '_workflow') else None
            }
            self.global_history.append(agent_entry)
            
            return response
            
        except Exception as e:
            error_response = f"Error: {str(e)}"
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "error",
                "user_id": self.current_user_id,
                "content": error_response,
                "workflow_step": None
            }
            self.global_history.append(error_entry)
            return error_response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        user_messages = len([h for h in self.global_history if h["type"] == "user"])
        agent_messages = len([h for h in self.global_history if h["type"] == "assistant"])
        errors = len([h for h in self.global_history if h["type"] == "error"])
        
        # Per-user stats
        user_stats = {}
        for user_id, user_data in self.users.items():
            user_stats[user_id] = {
                "message_count": user_data["message_count"],
                "join_time": user_data["join_time"].isoformat(),
                "last_active": user_data["last_active"].isoformat(),
                "is_current": user_id == self.current_user_id
            }
        
        return {
            "session_duration": str(datetime.now() - self.session_start),
            "current_user": self.current_user_id,
            "total_users": len(self.users),
            "user_messages": user_messages,
            "agent_messages": agent_messages,
            "errors": errors,
            "total_exchanges": user_messages,
            "users": user_stats
        }
    
    def export_history(self, filepath: str):
        """Export chat history to JSON file."""
        export_data = {
            "agent_class": self.agent.__class__.__name__,
            "session_start": self.session_start.isoformat(),
            "session_type": "multi_user",
            "stats": self.get_stats(),
            "history": self.global_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)


class AgentLoader:
    """Handles loading agents from various sources."""
    
    @staticmethod
    def load_from_file(filepath: str) -> Agent:
        """Load an agent from a Python file."""
        filepath = Path(filepath).resolve()
        
        if not filepath.exists():
            raise FileNotFoundError(f"Agent file not found: {filepath}")
        
        # Load module from file
        spec = importlib.util.spec_from_file_location("agent_module", filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {filepath}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find Agent subclasses
        agent_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                issubclass(obj, Agent) and 
                obj is not Agent):
                agent_classes.append(obj)
        
        if not agent_classes:
            raise ValueError(f"No Agent subclasses found in {filepath}")
        
        if len(agent_classes) > 1:
            click.echo(f"Multiple agent classes found: {[cls.__name__ for cls in agent_classes]}")
            click.echo(f"Using the first one: {agent_classes[0].__name__}")
        
        # Instantiate the agent
        agent_class = agent_classes[0]
        return agent_class()
    
    @staticmethod
    def list_example_agents() -> List[str]:
        """List available example agents."""
        examples_dir = Path(__file__).parent / "examples"
        if not examples_dir.exists():
            return []
        
        agent_files = []
        for file in examples_dir.glob("*.py"):
            if file.name != "__init__.py":
                agent_files.append(file.stem)
        
        return agent_files


def format_message(content: str, is_user: bool = True, user_id: str = None) -> str:
    """Format a message for display."""
    if is_user:
        if user_id:
            return f"\n💬 **{user_id}:** {content}"
        else:
            return f"\n💬 **You:** {content}"
    else:
        return f"\n🤖 **Agent:** {content}"


def print_workflow_info(agent: Agent):
    """Print information about the agent's workflow."""
    click.echo(f"\n📋 **Agent Info:**")
    click.echo(f"   Class: {agent.__class__.__name__}")
    click.echo(f"   Categories: {agent.get_classification_categories()}")
    click.echo(f"   Requirements: {[req.category + ': ' + str(req.required_fields) for req in agent.get_category_requirements()]}")
    click.echo(f"   Confidence Threshold: {agent.confidence_threshold}")
    click.echo(f"   Registered Handlers: {list(agent.handlers.keys())}")


def print_help():
    """Print help information."""
    click.echo("""
🔧 **Available Commands:**

📝 **Chat Commands:**
   /help        - Show this help message
   /info        - Show agent information  
   /stats       - Show session statistics
   /history     - Show conversation history
   /clear       - Clear conversation history
   /export      - Export chat history to file
   /quit, /exit - Exit the chat

👥 **Multi-User Commands:**
   /user <id>   - Switch to a different user (e.g., /user alice)
   /whoami      - Show current user
   /users       - List all users in the session
   /as <id> <message> - Send a message as a specific user

💡 **Tips:**
   - Type your message and press Enter to chat with the agent
   - Use /user <id> to simulate different users chatting
   - Use /info to see what categories and requirements the agent supports
   - Use /stats to see performance metrics for all users
   - Press Ctrl+C to exit at any time
""")


@click.group()
def cli():
    """Agentic Framework - Interactive Agent Testing CLI"""
    pass


@cli.command()
@click.option('--agent-file', '-f', type=str, help='Path to Python file containing agent class')
@click.option('--example', '-e', type=str, help='Name of example agent to load')
@click.option('--user-id', '-u', default='test_user', help='User ID for the session')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
def chat(agent_file: Optional[str], example: Optional[str], user_id: str, debug: bool):
    """Start an interactive chat session with an agent."""
    
    click.echo("🚀 **Agentic Framework - Agent Test Drive**\n")
    
    # Load agent
    try:
        if agent_file:
            click.echo(f"📂 Loading agent from: {agent_file}")
            agent = AgentLoader.load_from_file(agent_file)
        elif example:
            examples_dir = Path(__file__).parent / "examples"
            agent_path = examples_dir / f"{example}.py"
            click.echo(f"📂 Loading example agent: {example}")
            agent = AgentLoader.load_from_file(str(agent_path))
        else:
            # Use a default demo agent
            from .examples.demo_agent import DemoAgent
            click.echo("📂 Loading default demo agent")
            agent = DemoAgent()
            
        click.echo(f"✅ Agent loaded successfully: {agent.__class__.__name__}")
        
    except Exception as e:
        click.echo(f"❌ Error loading agent: {e}")
        return
    
    # Create chat session
    session = ChatSession(agent, user_id)
    
    # Print agent info
    print_workflow_info(agent)
    
    # Print help
    print_help()
    
    click.echo("\n" + "="*60)
    click.echo(f"💬 **Multi-User Chat Session Started** - Current user: {user_id}")
    click.echo("💡 Type your message or /help for commands")
    click.echo("="*60)
    
    # Main chat loop
    asyncio.run(chat_loop(session, debug))


async def chat_loop(session: ChatSession, debug: bool = False):
    """Main chat loop."""
    
    while True:
        try:
            # Get user input with current user indicator
            prompt = f"\n[{session.current_user_id}]> "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command_parts = user_input[1:].split()
                command = command_parts[0].lower() if command_parts else ""
                
                if command in ['quit', 'exit']:
                    click.echo("\n👋 Goodbye!")
                    break
                    
                elif command == 'help':
                    print_help()
                    continue
                    
                elif command == 'info':
                    print_workflow_info(session.agent)
                    continue
                    
                elif command == 'whoami':
                    click.echo(f"\n👤 Current user: {session.current_user_id}")
                    continue
                    
                elif command == 'users':
                    click.echo(f"\n👥 **Active Users:**")
                    for user_id in session.list_users():
                        current_marker = " (current)" if user_id == session.current_user_id else ""
                        user_data = session.users[user_id]
                        click.echo(f"   • {user_id}{current_marker} - {user_data['message_count']} messages")
                    continue
                    
                elif command == 'user':
                    if len(command_parts) < 2:
                        click.echo("❓ Usage: /user <user_id>")
                        continue
                    new_user_id = command_parts[1]
                    session.switch_user(new_user_id)
                    click.echo(f"👤 Switched to user: {new_user_id}")
                    continue
                    
                elif command == 'as':
                    if len(command_parts) < 3:
                        click.echo("❓ Usage: /as <user_id> <message>")
                        continue
                    as_user_id = command_parts[1]
                    as_message = " ".join(command_parts[2:])
                    
                    # Temporarily switch user
                    original_user = session.current_user_id
                    session.switch_user(as_user_id)
                    
                    # Send message
                    click.echo(format_message(as_message, is_user=True, user_id=as_user_id))
                    response = await session.send_message(as_message)
                    click.echo(format_message(response, is_user=False))
                    
                    # Switch back to original user
                    session.switch_user(original_user)
                    continue
                    
                elif command == 'stats':
                    stats = session.get_stats()
                    click.echo(f"\n📊 **Session Statistics:**")
                    for key, value in stats.items():
                        click.echo(f"   {key.replace('_', ' ').title()}: {value}")
                    continue
                    
                elif command == 'history':
                    click.echo(f"\n📜 **Conversation History:**")
                    for i, entry in enumerate(session.global_history):
                        timestamp = entry['timestamp'][:19]  # Trim microseconds
                        msg_type = entry['type']
                        content = entry['content']
                        
                        if msg_type == 'user':
                            user_id = entry.get('user_id', 'unknown')
                            click.echo(f"   {i+1}. 💬 [{timestamp}] {user_id}: {content}")
                        elif msg_type == 'assistant':
                            responding_to = entry.get('responding_to_user', '')
                            user_context = f" (to {responding_to})" if responding_to else ""
                            click.echo(f"   {i+1}. 🤖 [{timestamp}] Agent{user_context}: {content}")
                        elif msg_type == 'error':
                            user_id = entry.get('user_id', 'unknown')
                            click.echo(f"   {i+1}. ❌ [{timestamp}] Error ({user_id}): {content}")
                    continue
                    
                elif command == 'clear':
                    session.global_history.clear()
                    click.echo("🗑️ Conversation history cleared")
                    continue
                    
                elif command == 'export':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"chat_export_{timestamp}.json"
                    session.export_history(filename)
                    click.echo(f"💾 Chat history exported to: {filename}")
                    continue
                    
                else:
                    click.echo(f"❓ Unknown command: /{command}")
                    click.echo("   Type /help for available commands")
                    continue
            
            # Send message to agent
            click.echo(format_message(user_input, is_user=True, user_id=session.current_user_id))
            
            if debug:
                click.echo("🔧 [DEBUG] Sending message to agent...")
            
            response = await session.send_message(user_input)
            
            if debug:
                click.echo(f"🔧 [DEBUG] Agent response received: {len(response)} characters")
            
            click.echo(format_message(response, is_user=False))
            
        except KeyboardInterrupt:
            click.echo("\n\n👋 Goodbye!")
            break
        except EOFError:
            click.echo("\n\n👋 Goodbye!")
            break
        except Exception as e:
            click.echo(f"\n❌ Unexpected error: {e}")
            if debug:
                import traceback
                traceback.print_exc()


@cli.command()
def list_examples():
    """List available example agents."""
    examples = AgentLoader.list_example_agents()
    
    if not examples:
        click.echo("📭 No example agents found")
        return
    
    click.echo("📚 **Available Example Agents:**\n")
    for example in examples:
        click.echo(f"   • {example}")
    
    click.echo(f"\n💡 Use: agentic chat --example <name>")


if __name__ == '__main__':
    cli()