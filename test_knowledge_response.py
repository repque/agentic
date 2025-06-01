"""
Test knowledge being used in actual responses.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agentic.examples.helpdesk_agent import HelpDeskAgent


async def test_knowledge_in_response():
    """Test that knowledge is actually used in agent responses."""
    
    agent = HelpDeskAgent()
    
    # Test with a general inquiry that doesn't require specific fields
    print("🧪 Testing Knowledge Usage in Responses")
    print("=" * 50)
    
    # Test 1: General payment question (should use knowledge directly)
    print("\n💰 Test 1: General Payment Question")
    response1 = await agent.chat("I want to know what payment methods you accept", "test_user")
    print(f"Response: {response1}")
    
    # Test 2: Technical support general question  
    print("\n🔧 Test 2: Technical Support General")
    response2 = await agent.chat("What are your support response times?", "test_user") 
    print(f"Response: {response2}")
    
    # Test 3: Direct question about policies
    print("\n📋 Test 3: Policy Question")
    response3 = await agent.chat("What is your password reset policy?", "test_user")
    print(f"Response: {response3}")
    
    print("\n✅ Knowledge usage tests completed!")


if __name__ == "__main__":
    asyncio.run(test_knowledge_in_response())