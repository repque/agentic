#!/usr/bin/env python3
"""
Test DemoAgent feedback scenario to debug the issue.
"""

import asyncio
from agentic.examples.demo_agent import DemoAgent

async def test_demo_feedback():
    """Test the demo agent feedback flow."""
    
    print("🧪 Testing DemoAgent Feedback Flow")
    print("=" * 40)
    
    agent = DemoAgent()
    
    print("Categories:", agent.get_classification_categories())
    print("Requirements:", agent.get_category_requirements())
    print("Registered handlers:", list(agent.handlers.keys()))
    print()
    
    # Test the exact scenario
    print("User: i have feedback")
    response = await agent.chat("i have feedback", "bob")
    print(f"Agent: {response}")
    
    print("\n" + "=" * 40)
    print("🔍 Analysis:")
    print("Expected: Agent should ask for 'feedback_type' and 'details'")
    print("Actual response analysis:")
    if "feedback_type" in response or "details" in response:
        print("✅ Agent is asking for required information")
    elif "reviewed by our team" in response:
        print("❌ Agent is escalating instead of asking for requirements")
    else:
        print("❓ Unexpected response pattern")

if __name__ == "__main__":
    asyncio.run(test_demo_feedback())