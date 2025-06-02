# Knowledge Integration

Add knowledge to your agent in 2 lines of code.

## Basic Usage

```python
class MyAgent(Agent):
    def get_knowledge(self):
        return ["./docs/", "./faq.md", "https://api.company.com/docs"]
```

That's it! The framework automatically:
1. Loads and indexes your knowledge sources
2. Finds relevant content for each user query
3. Injects it into the AI's responses

## What You Can Use

- **Files**: `"./policies.md"`, `"./procedures.txt"`
- **Directories**: `"./docs/"` (finds all .md files)
- **URLs**: `"https://support.company.com/kb"`

## Real Example

```python
class SupportAgent(Agent):
    def get_knowledge(self):
        return [
            "./support_docs/billing.md",
            "./support_docs/technical.md", 
            "./faq.md"
        ]
    
    def get_personality(self):
        return "You are a helpful support agent with access to company knowledge."

# User asks: "What payment methods do you accept?"
# Framework automatically finds relevant info from billing.md
# AI responds with specific payment details from your docs
```

## Advanced: Semantic Search

```bash
# Install for better knowledge matching
pip install agentic[embeddings]
```

Now your agent understands meaning, not just keywords:
- User asks "How do I pay?" → Finds "Payment Methods" content
- User asks "Billing issues" → Finds "Account Problems" content

## Standalone Usage

Use the knowledge system outside the framework:

```python
from agentic.knowledge import create_default_knowledge_manager

km = create_default_knowledge_manager()
km.load_sources(["./docs/"])

knowledge = km.retrieve_for_query("How do I reset password?", max_results=3)
# Use with any AI system: OpenAI, LangChain, local models, etc.
```

## Tips

✅ **Keep it simple**: Start with a few key documents  
✅ **Use clear headings**: "Payment Methods", "Refund Policy"  
✅ **Avoid huge files**: Break into focused topics  
✅ **Test your knowledge**: Use `agentic chat` to see what gets retrieved