#!/usr/bin/env python3
"""
Example: Customizing System Prompts for Domain-Specific Agent

This example shows how a developer can easily modify the framework's
core prompts to make their agent behave optimally for their specific domain.
"""

import agentic
from agentic import system_prompts


def customize_for_pizza_ordering():
    """Customize system prompts for a pizza ordering domain."""
    
    print("🍕 Customizing Agentic Framework for Pizza Ordering")
    print("=" * 55)
    
    # 1. View current classification prompt
    print("📋 Current Classification Prompt:")
    print(f"Length: {len(system_prompts.CLASSIFICATION_PROMPT)} chars")
    print("Categories mentioned: TechnicalSupport, BillingInquiry, AccountAccess...")
    
    # 2. Customize classification for pizza ordering
    print("\n🔧 Customizing classification for pizza domain...")
    
    system_prompts.CLASSIFICATION_PROMPT = """Classify this customer message into ONE category: {categories}

Pizza Shop Guidelines:
- OrderPizza: Ordering new pizzas, customizing orders, adding items
- TrackOrder: Checking order status, delivery time, order updates  
- MenuQuestion: Questions about toppings, sizes, prices, specials
- Complaint: Issues with previous orders, delivery problems, quality complaints
- StoreInfo: Hours, locations, delivery areas, contact information

Instructions:
- Focus on pizza shop context and customer intent
- If unsure, default to "MenuQuestion" for general inquiries
- Respond with ONLY the category name

Customer: "{message}"

Category:"""

    print("✅ Classification prompt updated for pizza shop context")
    
    # 3. Customize requirements checking
    print("\n🔧 Customizing requirements validation...")
    
    system_prompts.REQUIREMENTS_PROMPT = """Check what information the customer provided: {required_fields}

Customer said: "{message}"{recent_context}

Pizza Shop Field Guidelines:
- pizza_size: Small, Medium, Large, Extra Large (accept Size abbreviations)
- toppings: Any pizza toppings (be flexible with names)
- delivery_address: Full address for delivery
- phone_number: Contact number (accept any format)
- order_number: Order ID (usually 4-6 digits)

Rules:
- Be VERY flexible - "pepperoni large" contains both size and toppings
- Accept common abbreviations and variations
- If customer gives reasonable info, mark as PROVIDED

Missing fields (or "NONE" if all provided):"""

    print("✅ Requirements prompt updated for pizza ordering")
    
    # 4. Customize conversation threading  
    print("\n🔧 Customizing conversation threading...")
    
    system_prompts.CONVERSATION_THREAD_PROMPT = """Is this about the SAME order/inquiry or a NEW order?

Previous: {recent_context}
Current: {current_message}

Pizza Shop Rules:
- Same order: Adding items, changing delivery, asking about same order
- New order: Starting fresh pizza order, completely different inquiry
- When in doubt: choose CONTINUE (keep same conversation)

Response: NEW or CONTINUE"""

    print("✅ Threading prompt updated for pizza context")
    
    # 5. Customize default responses
    print("\n🔧 Customizing response personality...")
    
    system_prompts.DEFAULT_RESPONSE_PROMPT = """You are Tony from Tony's Pizza! You're friendly, enthusiastic about pizza, and always hungry to help customers get the perfect order.

{knowledge_section}
{tools_section}

Conversation:
{conversation_history}

Tony's Style:
- Be warm and conversational like a local pizza shop
- Mention popular combinations when customers seem unsure  
- Always ask if they want drinks or sides
- Use phrases like "What can I make for you?" or "Coming right up!"
- Keep it brief but friendly

Tony:"""

    print("✅ Response prompt updated with Tony's pizza shop personality")

def create_pizza_agent():
    """Create an agent that will use the customized prompts."""
    
    print("\n🤖 Creating Pizza Agent (uses customized prompts)")
    print("=" * 50)
    
    class PizzaAgent(agentic.Agent):
        def get_classification_categories(self):
            return ["OrderPizza", "TrackOrder", "MenuQuestion", "Complaint", "StoreInfo"]
        
        def get_category_requirements(self):
            return [
                agentic.CategoryRequirement(
                    category="OrderPizza",
                    required_fields=["pizza_size", "toppings", "delivery_address"]
                ),
                agentic.CategoryRequirement(
                    category="TrackOrder", 
                    required_fields=["order_number"]
                )
            ]
        
        def get_personality(self):
            return "You are Tony from Tony's Pizza Shop. You're enthusiastic about making great pizza!"
    
    agent = PizzaAgent(name="pizza_tony")
    print("✅ Pizza agent created with customized system prompts")
    
    return agent

def test_customized_prompts():
    """Test that the customized prompts work correctly."""
    
    print("\n🧪 Testing Customized Prompts")
    print("=" * 35)
    
    # Test classification prompt
    test_message = "I want a large pepperoni pizza"
    categories = "OrderPizza, TrackOrder, MenuQuestion"
    
    classification_result = system_prompts.CLASSIFICATION_PROMPT.format(
        categories=categories,
        message=test_message
    )
    
    print("📋 Classification Test:")
    print(f"Message: '{test_message}'")
    print(f"Contains 'Pizza Shop Guidelines': {'Pizza Shop Guidelines' in classification_result}")
    print(f"Contains 'OrderPizza': {'OrderPizza' in classification_result}")
    
    # Test requirements prompt
    requirements_result = system_prompts.REQUIREMENTS_PROMPT.format(
        required_fields="pizza_size, toppings",
        message=test_message,
        recent_context=""
    )
    
    print("\n📋 Requirements Test:")
    print(f"Contains 'Pizza Shop Field Guidelines': {'Pizza Shop Field Guidelines' in requirements_result}")
    print(f"Contains flexibility guidance: {'flexible' in requirements_result}")
    
    # Test conversation threading
    thread_result = system_prompts.CONVERSATION_THREAD_PROMPT.format(
        recent_context="ordering pizza",
        current_message="add extra cheese"
    )
    
    print("\n📋 Threading Test:")
    print(f"Contains 'Pizza Shop Rules': {'Pizza Shop Rules' in thread_result}")
    print(f"Contains 'Same order': {'Same order' in thread_result}")
    
    print("\n✅ All customized prompts working correctly!")

def show_before_after():
    """Show how prompts changed from generic to pizza-specific."""
    
    print("\n📊 Before vs After Comparison")
    print("=" * 35)
    
    print("🔄 Classification Prompt:")
    print("  Before: Generic categories (TechnicalSupport, BillingInquiry...)")
    print("  After:  Pizza categories (OrderPizza, TrackOrder, MenuQuestion...)")
    
    print("\n🔄 Requirements Prompt:")
    print("  Before: Generic field validation")
    print("  After:  Pizza-specific field rules (sizes, toppings...)")
    
    print("\n🔄 Threading Prompt:")
    print("  Before: Generic topic detection")
    print("  After:  Pizza order context awareness")
    
    print("\n🔄 Response Prompt:")
    print("  Before: Generic assistant personality")
    print("  After:  Tony's pizza shop character")

def main():
    """Main example function."""
    
    print("🎛️ SYSTEM PROMPTS CUSTOMIZATION EXAMPLE")
    print("=" * 45)
    
    # Customize prompts for pizza domain
    customize_for_pizza_ordering()
    
    # Create agent that uses customized prompts
    agent = create_pizza_agent()
    
    # Test the customized prompts
    test_customized_prompts()
    
    # Show the transformation
    show_before_after()
    
    print("\n" + "=" * 45)
    print("🎉 EXAMPLE COMPLETE!")
    print("\n📝 What we accomplished:")
    print("  ✅ Modified framework's core classification prompt")
    print("  ✅ Customized requirements validation for pizza ordering")
    print("  ✅ Adjusted conversation threading for order context")
    print("  ✅ Created Tony's pizza shop personality")
    print("  ✅ Agent automatically uses all customized prompts")
    
    print("\n💡 The beauty of this approach:")
    print("  • All prompts in one file (system_prompts.py)")
    print("  • Easy to see exactly what the framework asks")
    print("  • Simple string replacement to customize")
    print("  • No complex templating - just modify the strings")
    print("  • Changes apply to all agents automatically")
    
    return agent

if __name__ == "__main__":
    pizza_agent = main()
    
    # Optionally test with real LLM (requires API key)
    test_llm = input("\nTest with real LLM? (y/n): ")
    if test_llm.lower() == 'y':
        import asyncio
        async def test():
            try:
                response = await pizza_agent.chat("I want a pizza", "customer1")
                print(f"\n🍕 Tony: {response}")
            except Exception as e:
                print(f"API Error: {e}")
        asyncio.run(test())