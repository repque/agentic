#!/usr/bin/env python3
"""
Test how conversation history affects the feedback response.
"""

import asyncio
from agentic.examples.demo_agent import DemoAgent

async def test_user_context():
    """Test same message with different user contexts."""
    
    print("🧪 Testing User Context Effect")
    print("=" * 40)
    
    agent = DemoAgent()
    
    # Test 1: Fresh user
    print("TEST 1: Fresh user (no history)")
    print("User: i have feedback")
    response1 = await agent.chat("i have feedback", "fresh_user")
    print(f"Response: {response1}")
    print(f"Result: {'✅ Requirements request' if 'feedback' in response1.lower() and 'type' in response1.lower() else '❌ Escalation' if 'reviewed by our team' in response1 else '❓ Other'}")
    
    print("\n" + "-" * 40)
    
    # Test 2: User with conversation history (replicate bob's exact sequence)
    print("TEST 2: User with conversation history")
    print("Building conversation history...")
    await agent.chat("BONJOUR", "history_user")
    await agent.chat("can u help me?", "history_user") 
    await agent.chat("what is agentic?", "history_user")
    
    print("User: i have feedback")
    response2 = await agent.chat("i have feedback", "history_user")
    print(f"Response: {response2}")
    print(f"Result: {'✅ Requirements request' if 'feedback' in response2.lower() and 'type' in response2.lower() else '❌ Escalation' if 'reviewed by our team' in response2 else '❓ Other'}")
    
    print("\n" + "=" * 40)
    print("🔍 Analysis:")
    
    if response1 != response2:
        print("❌ DIFFERENT RESPONSES - Conversation history is affecting behavior")
        print("The issue is in how the agent handles state with conversation context")
    else:
        print("✅ SAME RESPONSES - Issue is not conversation history related")

if __name__ == "__main__":
    asyncio.run(test_user_context())