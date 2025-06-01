#!/usr/bin/env python3
"""
Test script for the new embedding-based knowledge retrieval system.

This demonstrates:
- Automatic semantic similarity search
- Change detection and re-vectorization
- Transparent upgrade from keyword to embedding search
"""

import asyncio
import tempfile
import shutil
from pathlib import Path

# Add src to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agentic.knowledge import (
    create_default_knowledge_manager,
    create_embedding_knowledge_manager,
    create_simple_knowledge_manager
)


def create_test_knowledge_files(temp_dir: Path):
    """Create some test knowledge files."""
    
    # Create a policies file
    policies_file = temp_dir / "company_policies.md" 
    policies_file.write_text("""
# Company Policies

## Password Reset Procedure
Users can reset their passwords using the self-service portal. 
Account verification is required via email or SMS.
New passwords must meet complexity requirements.

## Support Response Times  
- High Priority: 2 hours
- Medium Priority: 24 hours
- Low Priority: 72 hours

## Remote Work Policy
Employees may work remotely up to 3 days per week.
Must use VPN for accessing company resources.
Video calls required for team meetings.
""")

    # Create a technical guide
    tech_file = temp_dir / "technical_guide.md"
    tech_file.write_text("""
# Technical Support Guide

## Common Issues

### Login Problems
Check if caps lock is on.
Verify username spelling.
Try password reset if needed.

### VPN Connection Issues  
Restart the VPN client.
Check internet connection.
Contact IT if problems persist.

### Email Configuration
Use these server settings:
- IMAP: mail.company.com
- SMTP: smtp.company.com  
- Port: 993 (IMAP), 587 (SMTP)
""")

    return [str(policies_file), str(tech_file)]


async def test_embedding_vs_keyword():
    """Compare embedding-based vs keyword-based retrieval."""
    
    print("🧪 Testing Embedding vs Keyword Knowledge Retrieval")
    print("=" * 60)
    
    # Create temporary knowledge files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        knowledge_files = create_test_knowledge_files(temp_path)
        
        print(f"📁 Created test knowledge files:")
        for file in knowledge_files:
            print(f"   • {Path(file).name}")
        
        # Test 1: Keyword-based retrieval
        print(f"\n🔍 Test 1: Keyword-based Retrieval")
        print("-" * 40)
        
        km_simple = create_simple_knowledge_manager()
        stats = km_simple.load_sources(knowledge_files)
        print(f"✅ Loaded {stats['loaded_successfully']} sources")
        
        queries = [
            "How do I reset my password?",
            "What are the VPN connection steps?", 
            "Remote work policy details"
        ]
        
        for query in queries:
            result = km_simple.retrieve_for_query(query, max_results=1)
            if result:
                print(f"Query: '{query}'")
                print(f"Found: {len(result)} words (keyword matching)")
                print(f"Preview: {result[:100]}...")
                print()
            else:
                print(f"Query: '{query}' → No results found")
        
        # Test 2: Embedding-based retrieval (if available)
        print(f"\n🧠 Test 2: Embedding-based Retrieval")
        print("-" * 40)
        
        try:
            # Create with custom temp directory for vector DB
            vector_db_path = temp_path / ".test_chroma"
            km_embedding = create_embedding_knowledge_manager(
                persist_directory=str(vector_db_path)
            )
            
            print("✅ Embedding retrieval available")
            stats = km_embedding.load_sources(knowledge_files)
            print(f"✅ Loaded and vectorized {stats['loaded_successfully']} sources")
            
            for query in queries:
                results = km_embedding.retrieve_for_query(query, max_results=1)
                if results:
                    result_text = km_embedding.retrieve_for_query(query, max_results=1)
                    similarity_info = ""
                    if hasattr(km_embedding.retriever, 'retrieve'):
                        detailed_results = km_embedding.retriever.retrieve(query, 1)
                        if detailed_results:
                            similarity_info = f" (similarity: {detailed_results[0].get('similarity_score', 0):.3f})"
                    
                    print(f"Query: '{query}'")
                    print(f"Found: {len(result_text)} chars (semantic search){similarity_info}")
                    print(f"Preview: {result_text[:100]}...")
                    print()
                else:
                    print(f"Query: '{query}' → No results found")
            
            # Test 3: Change detection
            print(f"\n🔄 Test 3: Change Detection")
            print("-" * 40)
            
            # Modify a file
            policies_file = Path(knowledge_files[0])
            original_content = policies_file.read_text()
            modified_content = original_content + "\n## New Policy\nThis is a new policy section."
            policies_file.write_text(modified_content)
            
            print("📝 Modified company_policies.md")
            
            # Reload sources - should detect changes
            stats = km_embedding.load_sources(knowledge_files)
            print(f"✅ Reloaded sources - change detection working")
            
            # Test new content retrieval
            new_query = "What is the new policy?"
            result = km_embedding.retrieve_for_query(new_query, max_results=1)
            if "new policy" in result.lower():
                print(f"✅ New content found: '{new_query}' → Found updated content")
            else:
                print(f"❌ New content not found for: '{new_query}'")
        
        except ImportError as e:
            print(f"⚠️  Embedding retrieval not available: {e}")
            print("💡 To enable: pip install chromadb openai")
        
        # Test 4: Default knowledge manager (auto-fallback)
        print(f"\n⚙️  Test 4: Default Knowledge Manager (Auto-detection)")
        print("-" * 40)
        
        km_default = create_default_knowledge_manager()
        print(f"✅ Created default knowledge manager")
        
        # Check which retriever it's using
        retriever_type = type(km_default.retriever).__name__
        print(f"📊 Using retriever: {retriever_type}")
        
        stats = km_default.load_sources(knowledge_files)
        print(f"✅ Loaded {stats['loaded_successfully']} sources")
        
        test_query = "How to reset password?"
        result = km_default.retrieve_for_query(test_query)
        print(f"🔍 Test query: '{test_query}'")
        print(f"📋 Result length: {len(result)} characters")
        
    print(f"\n✨ Knowledge retrieval testing completed!")


async def test_agent_integration():
    """Test the embedding knowledge with actual agent."""
    
    print(f"\n🤖 Testing Agent Integration")
    print("=" * 40)
    
    try:
        from agentic.examples.helpdesk_agent import HelpDeskAgent
        
        # Note: HelpDeskAgent has no knowledge sources configured by default
        print("📝 Note: HelpDeskAgent has no knowledge sources in this test")
        print("📝 In real usage, configure get_knowledge() method in your agent")
        
        agent = HelpDeskAgent()
        response = await agent.chat("What are your support policies?", "test_user")
        print(f"🤖 Agent response: {response[:150]}...")
        
    except Exception as e:
        print(f"⚠️  Agent test skipped: {e}")


if __name__ == "__main__":
    asyncio.run(test_embedding_vs_keyword())
    asyncio.run(test_agent_integration())