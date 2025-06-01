#!/usr/bin/env python3
"""
Test the fixes for Bob's computer and AC issues.
"""

import asyncio
from agentic.examples.helpdesk_agent import HelpDeskAgent

async def test_bob_fixes():
    """Test the fixes for over-asking and wrong ticket reference."""
    
    print("🧪 Testing Bob's Issue Fixes")
    print("=" * 50)
    
    agent = HelpDeskAgent()
    user_id = "bob"
    
    # Test Bob's computer issue sequence
    computer_sequence = [
        "i have a problem with my computer - i cannot boot it",
        "there is no error message - it doesn't turn on at all", 
        "nothing happens - blank screen"
    ]
    
    print("\n--- COMPUTER ISSUE TEST ---")
    for i, message in enumerate(computer_sequence, 1):
        print(f"[Turn {i}] Bob: {message}")
        response = await agent.chat(message, user_id)
        print(f"🤖 Agent: {response[:150]}...")
        
        # Check if agent stops asking after sufficient details
        if i == 3:
            if "ticket" in response.lower():
                print("✅ SUCCESS: Agent created ticket after sufficient details")
            else:
                print("❌ ISSUE: Agent still asking for more details")
    
    # Test AC issue with correct reference
    print("\n--- AC ISSUE TEST ---")
    print("[Turn 4] Bob: my AC doesn't blow cold air")
    response = await agent.chat("my AC doesn't blow cold air", user_id)
    print(f"🤖 Agent: {response[:200]}...")
    
    # Check if ticket reference is correct
    if "ac" in response.lower() or "cold air" in response.lower():
        print("✅ SUCCESS: Ticket reference shows correct issue")
    elif "computer" in response.lower() or "boot" in response.lower():
        print("❌ ISSUE: Ticket reference shows wrong issue")
    else:
        print("❓ INFO: Could not determine ticket reference accuracy")

if __name__ == "__main__":
    asyncio.run(test_bob_fixes())