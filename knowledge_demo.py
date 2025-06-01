"""
Demonstration of the framework-agnostic knowledge integration.

This shows how the KnowledgeManager can be used with different GenAI frameworks.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from agentic.knowledge import create_default_knowledge_manager
from agentic.examples.helpdesk_agent import HelpDeskAgent


async def demo_knowledge_integration():
    """Demonstrate the framework-agnostic knowledge integration."""
    print("🚀 Framework-Agnostic Knowledge Integration Demo")
    print("=" * 60)
    
    # 1. Standalone KnowledgeManager usage
    print("\n📚 Standalone Knowledge Manager:")
    km = create_default_knowledge_manager()
    
    # Demo with example sources (you can replace with your own)
    sources = [
        "./README.md",  # Use existing file as demo
        "./docs/",      # Example directory
    ]
    
    stats = km.load_sources(sources)
    print(f"✅ Loaded {stats['loaded_successfully']}/{stats['total_sources']} sources")
    if stats['errors']:
        print(f"⚠️  Some sources failed to load (this is normal for demo): {len(stats['errors'])} errors")
    
    # Query for framework info
    query = "What is this framework about?"
    relevant = km.retrieve_for_query(query, max_results=1)
    print(f"\n🔍 Query: '{query}'")
    if relevant:
        print(f"📋 Retrieved: {len(relevant.split())} words of relevant content")
        print(f"📄 Content preview: {relevant[:150]}...")
    else:
        print("📋 No relevant content found (normal for demo)")
    
    # 2. Framework Integration Examples - All use the same simple API
    print(f"\n🔧 Framework-Agnostic Usage:")
    
    # Any framework can use the same API
    knowledge_for_any_framework = km.retrieve_for_query(query, max_results=2)
    print(f"📦 Universal format: {len(knowledge_for_any_framework)} characters")
    
    # Raw content access for frameworks that need it
    all_content = [c['content'] for c in km.loaded_content if c.get('content') and not c.get('error')]
    print(f"📦 Raw content: {len(all_content)} documents")
    
    # Different max_results for different needs
    brief_knowledge = km.retrieve_for_query(query, max_results=1)
    detailed_knowledge = km.retrieve_for_query(query, max_results=5)
    print(f"📦 Brief: {len(brief_knowledge)} chars, Detailed: {len(detailed_knowledge)} chars")
    
    # 3. Agent Integration (Our Framework)
    print(f"\n🤖 Agentic Framework Integration:")
    agent = HelpDeskAgent()
    
    # Test agent response (no knowledge sources configured in this demo)
    response = await agent.chat("What types of issues can you help with?", "demo_user")
    print(f"💬 Agent response length: {len(response)} characters")
    print(f"📝 Response preview: {response[:200]}...")
    
    # Note about knowledge integration
    print("📝 Note: Agent has no knowledge sources configured in this demo")
    print("📝 To see knowledge integration, configure get_knowledge() in your agent")
    
    print(f"\n🎯 Framework-Agnostic Benefits:")
    print("• Universal API: Same retrieve_for_query() works with any framework")
    print("• No framework dependencies: Pure Python, works anywhere") 
    print("• Context-aware: Retrieves relevant knowledge based on queries")
    print("• Pluggable architecture: FileLoader, URLLoader, SimpleRetriever can be extended")
    print("• Efficient: Only loads content once, retrieves on-demand")
    print("• Scalable: Handles files, directories, and URLs")
    print("• Simple integration: Just call km.retrieve_for_query() from any framework")
    
    print(f"\n✨ Knowledge integration completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_knowledge_integration())