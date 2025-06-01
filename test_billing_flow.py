#!/usr/bin/env python3
"""
Test the billing conversation flow to debug category switching.
"""

import asyncio
from agentic.examples.helpdesk_agent import HelpDeskAgent
from agentic.classification import classify_message_with_llm

async def test_billing_flow():
    """Test the billing conversation sequence."""
    
    print("🧪 Testing Billing Conversation Flow")
    print("=" * 40)
    
    agent = HelpDeskAgent()
    
    print("Agent categories:", agent.get_classification_categories())
    print("Agent requirements:")
    for req in agent.get_category_requirements():
        print(f"  {req.category}: {req.required_fields}")
    print()
    
    # Step 1: Initial billing issue
    print("1. User: i have an issue with my bill")
    response1 = await agent.chat("i have an issue with my bill", "bob")
    print(f"   Agent: {response1}")
    
    # Step 2: Provide account number
    print("\n2. User: 12234")
    response2 = await agent.chat("12234", "bob")
    print(f"   Agent: {response2}")
    
    # Step 3: Describe the issue - this is where category switching might happen
    print("\n3. User: the account balance is negative")
    
    # Test classification of this message in isolation
    print("   🏷️ Testing classification of 'the account balance is negative':")
    classification = await classify_message_with_llm(
        agent.llm, 
        "the account balance is negative", 
        agent.get_classification_categories()
    )
    print(f"   Classified as: '{classification}'")
    
    response3 = await agent.chat("the account balance is negative", "bob")
    print(f"   Agent: {response3}")
    
    print("\n" + "=" * 40)
    print("🔍 Analysis:")
    
    if "username" in response3.lower():
        print("❌ WRONG REQUIREMENTS - Agent asking for username instead of handling billing issue")
        print("   This suggests the message was classified as 'AccountAccess' instead of continuing 'BillingInquiry'")
        print(f"   Classification result: '{classification}'")
        
        if classification == "AccountAccess":
            print("   🎯 ROOT CAUSE: Message incorrectly classified as AccountAccess")
        elif classification == "BillingInquiry":
            print("   🎯 POSSIBLE CAUSE: Thread detection reset the conversation context")
    else:
        print("✅ CORRECT FLOW - Agent handling as billing inquiry")

if __name__ == "__main__":
    asyncio.run(test_billing_flow())