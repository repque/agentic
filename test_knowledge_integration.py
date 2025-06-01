"""
Test script to verify knowledge integration is working properly.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path so we can import agentic
sys.path.insert(0, str(Path(__file__).parent))

from agentic.examples.helpdesk_agent import HelpDeskAgent


async def test_knowledge_integration():
    """Test the new knowledge integration."""
    print("🧪 Testing Knowledge Integration")
    print("=" * 50)
    
    # Create agent
    agent = HelpDeskAgent()
    
    # Test 1: Check knowledge loading stats
    print("\n📚 Knowledge Loading Test:")
    stats = agent.reload_knowledge()
    print(f"Total sources: {stats['total_sources']}")
    print(f"Loaded successfully: {stats['loaded_successfully']}")
    print(f"Failed: {stats['failed']}")
    if stats['errors']:
        print(f"Errors: {stats['errors']}")
    
    # Test 2: Check knowledge manager content
    print("\n📋 Loaded Knowledge Summary:")
    summary = agent.knowledge_manager.get_all_content_summary()
    print(summary if summary else "No knowledge loaded")
    
    # Test 3: Test retrieval for billing query
    print("\n🔍 Knowledge Retrieval Test (Billing):")
    billing_query = "What payment methods do you accept?"
    relevant_knowledge = agent.knowledge_manager.retrieve_for_query(billing_query, max_results=2)
    if relevant_knowledge:
        print("Retrieved knowledge:")
        print(relevant_knowledge[:500] + "..." if len(relevant_knowledge) > 500 else relevant_knowledge)
    else:
        print("No relevant knowledge retrieved")
    
    # Test 4: Test retrieval for technical query
    print("\n🔍 Knowledge Retrieval Test (Technical):")
    tech_query = "My system is not working properly"
    relevant_knowledge = agent.knowledge_manager.retrieve_for_query(tech_query, max_results=2)
    if relevant_knowledge:
        print("Retrieved knowledge:")
        print(relevant_knowledge[:500] + "..." if len(relevant_knowledge) > 500 else relevant_knowledge)
    else:
        print("No relevant knowledge retrieved")
    
    # Test 5: Test actual agent response with knowledge
    print("\n💬 Agent Response Test with Knowledge:")
    try:
        response = await agent.chat("What are your payment methods?", "test_user")
        print(f"Agent response: {response[:300]}...")
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
    
    print("\n✅ Knowledge integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_knowledge_integration())