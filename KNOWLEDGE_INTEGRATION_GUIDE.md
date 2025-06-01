# 📚 Knowledge Integration Guide

The Agentic Framework includes a **framework-agnostic KnowledgeManager** that provides intelligent knowledge integration for any GenAI framework. This guide covers how to use it effectively.

## 🚀 Quick Start

### Basic Usage

```python
from agentic import Agent

class MyAgent(Agent):
    def get_knowledge(self) -> list[str]:
        return [
            "./docs/policies.md",           # Single file
            "./support_docs/",              # Directory  
            "https://api.company.com/docs", # URL
        ]
    
    def get_personality(self) -> str:
        return "You are a helpful support agent with access to company knowledge."

# The framework automatically:
# 1. Loads and indexes knowledge sources during initialization
# 2. Retrieves relevant knowledge based on user queries
# 3. Injects knowledge into LLM responses
```

### Real Example

```python
# User asks: "What payment methods do you accept?"
# Framework automatically:
# 1. Analyzes query: ["payment", "methods", "accept"]
# 2. Searches knowledge: finds billing_procedures.md
# 3. Retrieves content: "Credit Cards, ACH, PayPal..."
# 4. Injects into LLM prompt
# 5. LLM responds with specific payment details
```

## 🔧 KnowledgeManager Architecture

### Components

```python
from agentic.knowledge import KnowledgeManager, FileLoader, URLLoader, SimpleRetriever

# The system consists of:
km = KnowledgeManager()
km.add_loader(FileLoader())     # Handles files/directories
km.add_loader(URLLoader())      # Handles web content  
km.set_retriever(SimpleRetriever())  # Keyword-based matching
```

### How It Works

1. **Initialization** - During `Agent.__init__()`
   ```python
   # Framework calls get_knowledge() and loads sources
   knowledge_sources = ["policies.md", "docs/", "https://api.com"]
   stats = knowledge_manager.load_sources(knowledge_sources)
   ```

2. **Runtime** - During response generation
   ```python
   # Framework extracts current user query
   query = "What are your business hours?"
   
   # Retrieves relevant knowledge
   relevant = knowledge_manager.retrieve_for_query(query, max_results=3)
   
   # Injects into LLM prompt
   prompt = f"Personality: {personality}\nKnowledge: {relevant}\nQuery: {query}"
   ```

## 📁 Supported Knowledge Sources

### Files

```python
def get_knowledge(self):
    return [
        "/path/to/policies.md",
        "/path/to/procedures.txt", 
        "/path/to/faq.json"
    ]
```

**Supported formats:**
- Text files (.txt, .md, .rst)
- JSON files (content extracted)
- Any UTF-8 encoded file

**Limitations:**
- Max file size: 10,000 characters (configurable)
- Binary files are skipped with metadata

### Directories

```python
def get_knowledge(self):
    return [
        "/path/to/docs/",           # All markdown files
        "/path/to/knowledge_base/"  # Aggregated content
    ]
```

**Behavior:**
- Recursively finds `.md` files
- Aggregates content with file separators
- Lists other files if no markdown found
- Max 20 files per directory

### URLs

```python
def get_knowledge(self):
    return [
        "https://api.company.com/docs",
        "https://support.example.com/kb"
    ]
```

**Behavior:**
- Fetches content via HTTP GET
- 10-second timeout
- Max 10,000 characters
- Requires `requests` library

## 🔍 Retrieval System

### How Retrieval Works

```python
# SimpleRetriever uses keyword matching
query = "payment methods credit card"
query_words = {"payment", "methods", "credit", "card"}

# For each knowledge source:
content_words = {"payment", "methods", "visa", "mastercard", "credit", "card", "billing"}
overlap = query_words.intersection(content_words)  # {"payment", "methods", "credit", "card"}
score = len(overlap)  # 4

# Sources ranked by score, top 3 returned
```

### Optimizing Retrieval

**Good Knowledge Structure:**
```markdown
# Payment Methods

## Accepted Cards
- Visa
- MasterCard  
- American Express

## Bank Transfers
- ACH transfers
- Wire transfers

## Digital Payments
- PayPal
- Apple Pay
```

**Tips:**
- Use descriptive headings
- Include synonyms and variations
- Structure content logically
- Avoid very long files

## 🔧 Framework Integration

### Using with Other Frameworks

The KnowledgeManager is designed to work with any GenAI framework using the same simple API:

#### LangChain Integration

```python
from agentic.knowledge import create_default_knowledge_manager

km = create_default_knowledge_manager()
km.load_sources(["./docs/"])

# Get knowledge for LangChain prompts - same API for any framework
query = "How do I reset my password?"
knowledge = km.retrieve_for_query(query, max_results=3)

# Use in LangChain chain
from langchain.prompts import PromptTemplate
prompt = PromptTemplate(
    template="Context: {knowledge}\nQuestion: {query}\nAnswer:",
    input_variables=["knowledge", "query"]
)
```

#### LlamaIndex Integration

```python
# Get all content for LlamaIndex documents
all_content = [c['content'] for c in km.loaded_content if c.get('content') and not c.get('error')]

from llama_index import VectorStoreIndex, Document
documents = [Document(text=content) for content in all_content]
index = VectorStoreIndex.from_documents(documents)
```

#### OpenAI Assistant API

```python
# Same API works for OpenAI
knowledge = km.retrieve_for_query(query, max_results=5)

import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": f"Knowledge: {knowledge}"},
        {"role": "user", "content": query}
    ]
)
```

#### Any Framework

```python
# The same API works everywhere - no framework-specific code needed
km = create_default_knowledge_manager()
km.load_sources(["./docs/"])

# Universal method that works with any framework
knowledge = km.retrieve_for_query("your query here", max_results=3)
```

### Direct Usage (Standalone)

```python
from agentic.knowledge import create_default_knowledge_manager

# Create knowledge manager
km = create_default_knowledge_manager()

# Load sources
sources = ["./policies/", "./faq.md", "https://api.docs.com"]
stats = km.load_sources(sources)
print(f"Loaded {stats['loaded_successfully']}/{stats['total_sources']} sources")

# Query knowledge
query = "What is the refund policy?"
relevant = km.retrieve_for_query(query, max_results=2)
print(f"Relevant knowledge: {relevant}")

# Get summary
summary = km.get_all_content_summary()
print(f"Available knowledge: {summary}")
```

## ⚙️ Configuration

### Custom FileLoader

```python
from agentic.knowledge import KnowledgeManager, FileLoader

# Custom file loader with different limits
custom_loader = FileLoader(
    max_file_size=20000,  # Larger files
    encoding='utf-8'      # Specific encoding
)

km = KnowledgeManager()
km.add_loader(custom_loader)
```

### Custom URLLoader

```python
from agentic.knowledge import URLLoader

# Custom URL loader with longer timeout
custom_url_loader = URLLoader(timeout=30)
km.add_loader(custom_url_loader)
```

### Custom Retriever

```python
from agentic.knowledge import KnowledgeRetriever
from typing import List, Dict, Any

class CustomRetriever:
    def __init__(self):
        self.content_store = []
    
    def add_content(self, content: Dict[str, Any]) -> None:
        # Custom indexing logic
        self.content_store.append(content)
    
    def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        # Custom retrieval logic (e.g., semantic search)
        # This example uses simple keyword matching
        results = []
        for content in self.content_store:
            if query.lower() in content.get('content', '').lower():
                results.append(content)
        return results[:max_results]

# Use custom retriever
km = KnowledgeManager()
km.set_retriever(CustomRetriever())
```

## 🧪 Testing Knowledge Integration

### Unit Testing

```python
import pytest
from agentic.knowledge import create_default_knowledge_manager

def test_knowledge_loading():
    km = create_default_knowledge_manager()
    stats = km.load_sources(["./test_docs/sample.md"])
    
    assert stats['loaded_successfully'] == 1
    assert stats['failed'] == 0

def test_knowledge_retrieval():
    km = create_default_knowledge_manager()
    km.load_sources(["./test_docs/"])
    
    result = km.retrieve_for_query("test query")
    assert len(result) > 0
    assert "test" in result.lower()
```

### Integration Testing

```python
def test_agent_with_knowledge():
    from agentic.examples.helpdesk_agent import HelpDeskAgent
    
    agent = HelpDeskAgent()
    
    # Test knowledge is loaded
    summary = agent.knowledge_manager.get_all_content_summary()
    assert "billing_procedures.md" in summary
    
    # Test knowledge is used in responses
    import asyncio
    response = asyncio.run(agent.chat("What payment methods do you accept?", "test_user"))
    
    # Should contain knowledge from billing procedures
    assert any(term in response for term in ["Credit Cards", "PayPal", "ACH"])
```

### Manual Testing

```python
# Create test script
from agentic.examples.helpdesk_agent import HelpDeskAgent
import asyncio

async def test_knowledge():
    agent = HelpDeskAgent()
    
    # Test different knowledge queries
    queries = [
        "What payment methods do you accept?",
        "What are your support response times?", 
        "How do I reset my password?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = await agent.chat(query, "test_user")
        print(f"Response: {response[:200]}...")

asyncio.run(test_knowledge())
```

## 🔧 Best Practices

### Knowledge Organization

```markdown
# Good Structure
docs/
├── billing/
│   ├── payment_methods.md     # Specific topics
│   ├── pricing.md
│   └── refunds.md
├── support/
│   ├── response_times.md
│   └── escalation.md
└── policies/
    ├── privacy.md
    └── terms.md
```

### Content Guidelines

**Good Knowledge Content:**
```markdown
# Payment Methods

## Credit Cards
We accept Visa, MasterCard, and American Express.

## Bank Transfers  
ACH transfers take 3-5 business days.
Wire transfers are processed same day.

## Digital Payments
PayPal and Apple Pay are supported.
```

**Avoid:**
- Very long files (>10,000 chars)
- Binary content  
- Duplicate information
- Unclear headings

### Performance Tips

1. **Limit Knowledge Sources** - Keep to essential files only
2. **Structure Content** - Use clear headings and sections
3. **Monitor Retrieval** - Check what knowledge is being retrieved
4. **Test Regularly** - Ensure knowledge is relevant and current

### Debugging Knowledge Issues

```python
# Debug knowledge loading
agent = MyAgent()
stats = agent.reload_knowledge()
print(f"Loading stats: {stats}")

# Debug retrieval
query = "problem query"
relevant = agent.knowledge_manager.retrieve_for_query(query)
print(f"Retrieved knowledge: {relevant}")

# Check all available knowledge
summary = agent.knowledge_manager.get_all_content_summary()
print(f"Available knowledge: {summary}")
```

## 🚀 Advanced Use Cases

### Dynamic Knowledge Sources

```python
class DynamicAgent(Agent):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__()
    
    def get_knowledge(self) -> list[str]:
        # Dynamic knowledge based on user
        base_knowledge = ["./docs/general/"]
        
        if self.user_id.startswith("admin_"):
            base_knowledge.append("./docs/admin/")
        elif self.user_id.startswith("support_"):
            base_knowledge.append("./docs/support/")
            
        return base_knowledge
```

### Knowledge Versioning

```python
class VersionedAgent(Agent):
    def get_knowledge(self) -> list[str]:
        import os
        version = os.getenv("KNOWLEDGE_VERSION", "latest")
        return [f"./docs/{version}/"]
```

### Multi-Language Knowledge

```python
class MultiLangAgent(Agent):
    def __init__(self, language: str = "en"):
        self.language = language
        super().__init__()
    
    def get_knowledge(self) -> list[str]:
        return [f"./docs/{self.language}/"]
```

## 📖 API Reference

### KnowledgeManager

```python
class KnowledgeManager:
    def add_loader(self, loader: KnowledgeLoader) -> None
    def set_retriever(self, retriever: KnowledgeRetriever) -> None
    def load_sources(self, sources: List[str]) -> Dict[str, Any]
    def retrieve_for_query(self, query: str, max_results: int = 3) -> str
    def get_all_content_summary(self) -> str
```

### Utility Functions

```python
def create_default_knowledge_manager() -> KnowledgeManager
    # Creates KM with FileLoader, URLLoader, and SimpleRetriever
```

The KnowledgeManager provides a powerful, flexible foundation for integrating knowledge into any GenAI application while maintaining framework agnosticism and ease of use.