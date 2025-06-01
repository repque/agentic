#!/usr/bin/env python3
"""
Test the exact conversation flow that was causing the escalation issue.
"""

import asyncio
from agentic.examples.demo_agent import DemoAgent

async def test_conversation_flow():
    """Test the exact conversation sequence."""
    
    print("🧪 Testing Exact Conversation Flow")
    print("=" * 40)
    
    agent = DemoAgent()
    
    # Replicate the exact conversation
    print("1. User: BONJOUR")
    response1 = await agent.chat("BONJOUR", "bob")
    print(f"   Agent: [Greeting handler response - {len(response1)} chars]")
    
    print("\n2. User: can u help me?")
    response2 = await agent.chat("can u help me?", "bob")
    print(f"   Agent: [Help handler response - {len(response2)} chars]")
    
    print("\n3. User: what is agentic?")
    response3 = await agent.chat("what is agentic?", "bob")
    print(f"   Agent: [LLM response - {len(response3)} chars]")
    
    print("\n4. User: i have feedback")
    response4 = await agent.chat("i have feedback", "bob")
    print(f"   Agent: {response4}")
    
    print("\n" + "=" * 40)
    print("🔍 Analysis:")
    
    if "reviewed by our team" in response4.lower():
        print("❌ STILL ESCALATING - Thread detection issue persists")
    elif "feedback" in response4.lower() and ("type" in response4.lower() or "details" in response4.lower()):
        print("✅ FIXED - Now asking for feedback requirements")
    else:
        print("❓ UNEXPECTED - Different response pattern")
        
    print(f"\nFinal response: '{response4}'")

if __name__ == "__main__":
    asyncio.run(test_conversation_flow())