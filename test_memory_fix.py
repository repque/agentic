#!/usr/bin/env python3
"""
Test script to verify the memory fix for multi-user conversations.
Simulates the exact scenario described in the issue.
"""

import asyncio
from agentic.examples.helpdesk_agent import HelpDeskAgent

async def test_memory_fix():
    """Test the memory fix with the exact scenario that was failing."""
    
    print("🧪 Testing Memory Fix - Multi-User Conversation Scenario")
    print("=" * 60)
    
    # Create agent
    agent = HelpDeskAgent()
    
    # Simulate Bob's conversation
    print("\n👤 BOB's conversation:")
    print("-" * 30)
    
    # Bob's first message
    response1 = await agent.chat("i have an issue with my bill", "bob")
    print(f"Bob: i have an issue with my bill")
    print(f"Agent: {response1}")
    
    # Bob provides account number  
    response2 = await agent.chat("5678", "bob")
    print(f"\nBob: 5678")
    print(f"Agent: {response2}")
    
    # Simulate Alice's conversation (different user)
    print("\n\n👤 ALICE's conversation:")
    print("-" * 30)
    
    response3 = await agent.chat("i have a bill question", "alice")
    print(f"Alice: i have a bill question")
    print(f"Agent: {response3}")
    
    response4 = await agent.chat("1234", "alice")
    print(f"\nAlice: 1234")
    print(f"Agent: {response4}")
    
    # Bob continues his conversation
    print("\n\n👤 BOB continues (should remember account 5678):")
    print("-" * 50)
    
    response5 = await agent.chat("my account shows negative balance", "bob")
    print(f"Bob: my account shows negative balance")
    print(f"Agent: {response5}")
    
    # Check if Bob needs to provide account number again (this was the bug)
    response6 = await agent.chat("i did", "bob")
    print(f"\nBob: i did")
    print(f"Agent: {response6}")
    
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS:")
    
    # Check if the agent is asking for account number again
    if "account number" in response6.lower():
        print("❌ BUG STILL EXISTS: Agent is asking for account number again")
        print("   The agent should remember Bob provided account number 5678")
    else:
        print("✅ FIX WORKING: Agent remembers Bob's account information")
        print("   Agent is not asking for account number again")
        
    print("\n🔍 Response Analysis:")
    print(f"   Last response: '{response6}'")
    print(f"   Contains 'account number': {'account number' in response6.lower()}")

if __name__ == "__main__":
    asyncio.run(test_memory_fix())