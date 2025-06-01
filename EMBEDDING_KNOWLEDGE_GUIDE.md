# 🧠 Embedding-Based Knowledge Search

The Agentic framework now includes **semantic similarity search** using embeddings and vector storage, providing much more accurate knowledge retrieval than keyword matching.

## 🎯 Key Features

- **Transparent Upgrade**: Automatically uses embeddings when available, falls back to keyword search
- **Change Detection**: Only re-vectorizes content when files actually change (using MD5 hashes)
- **Cheap Embeddings**: Uses OpenAI's `text-embedding-3-small` for cost-effective semantic search
- **Open Source Vector DB**: Built on Chroma for persistent, scalable vector storage
- **Smart Chunking**: Automatically splits large documents with sentence-boundary awareness
- **Framework Agnostic**: Works with any GenAI framework, not just Agentic

## 🚀 Quick Start

### Installation

```bash
# Install with embedding support
pip install agentic[embeddings]

# Or install dependencies manually
pip install chromadb openai
```

### Usage (Completely Transparent)

```python
from agentic import Agent

class MyAgent(Agent):
    def get_knowledge(self):
        return [
            "./docs/policies.md",
            "./guides/",
            "https://api.company.com/docs"
        ]

# That's it! Automatically uses semantic search
agent = MyAgent()
response = await agent.chat("What's the password policy?", "user123")
```

## 🔧 How It Works

### Automatic Embedding Pipeline

1. **Content Loading**: Files/URLs loaded and parsed
2. **Change Detection**: MD5 hashes checked against stored values
3. **Smart Chunking**: Large content split at sentence boundaries (500 chars with 50 char overlap)
4. **Vectorization**: OpenAI embeddings generated for each chunk
5. **Vector Storage**: Embeddings stored in Chroma database with metadata
6. **Similarity Search**: Query vectorized and matched against stored embeddings

### Architecture

```
User Query → OpenAI Embedding → Chroma Vector Search → Relevant Chunks → Formatted Response
```

## 📊 Comparison: Keyword vs Semantic Search

### Keyword Search (Fallback)
```python
Query: "How to reset my password?"
Matches: Documents containing "reset", "password"
Result: Literal keyword matching
```

### Semantic Search (Default)
```python
Query: "How to reset my password?"
Matches: Documents about authentication, login issues, account recovery
Result: Contextual understanding, better relevance
```

### Example Improvements

| Query | Keyword Search | Semantic Search |
|-------|---------------|-----------------|
| "How to reset password?" | Only finds "reset" + "password" | Finds login help, account recovery, authentication docs |
| "VPN connection issues" | Needs exact "VPN" keyword | Finds network, connectivity, remote access docs |
| "Remote work policy" | Must contain "remote" + "work" | Finds WFH, telecommuting, distributed team policies |

## ⚙️ Configuration Options

### Default (Automatic)
```python
from agentic.knowledge import create_default_knowledge_manager

# Tries embedding search first, falls back to keyword search
km = create_default_knowledge_manager()
```

### Explicit Embedding Configuration
```python
from agentic.knowledge import create_embedding_knowledge_manager

km = create_embedding_knowledge_manager(
    persist_directory="./my_vectors",  # Custom vector DB location
    embedding_model="text-embedding-3-small"  # OpenAI model
)
```

### Keyword-Only (No Dependencies)
```python
from agentic.knowledge import create_simple_knowledge_manager

# For environments where you can't install chromadb/openai
km = create_simple_knowledge_manager()
```

## 🔄 Change Detection & Re-vectorization

### How It Works
- **MD5 Hashing**: Each source file/URL content is hashed
- **Hash Storage**: Hashes stored in `.chroma_db/content_hashes.json`
- **Change Detection**: On reload, compares current hash vs stored hash
- **Smart Updates**: Only re-vectorizes changed content, keeps unchanged embeddings

### Example
```python
# Initial load - vectorizes everything
km.load_sources(["./docs/"])

# Edit a file...
# Reload - only re-vectorizes changed files
km.load_sources(["./docs/"])  # Fast! Only processes changes
```

## 💰 Cost Optimization

### Embedding Costs (OpenAI text-embedding-3-small)
- **$0.00002 per 1K tokens** (extremely cheap)
- **Example**: 100 KB of docs ≈ $0.002 to vectorize
- **Change Detection**: Avoids re-vectorization costs

### Chunking Strategy
- **500 character chunks** with 50 character overlap
- **Sentence boundary breaking** for coherent chunks
- **Optimal balance** between context and cost

## 🗂️ Vector Database Details

### Chroma Configuration
```python
# Automatic setup:
persist_directory = ".chroma_db"  # Local storage
collection_name = "knowledge"     # Collection name
```

### Metadata Stored
```python
{
    "source": "path/to/file.md",
    "chunk_index": 0,
    "total_chunks": 5,
    "content_type": "file",
    "timestamp": "1703123456"
}
```

### Search Results
```python
{
    "source": "policies.md",
    "content": "Password reset procedure...",
    "similarity_score": 0.85,
    "chunk_info": "2/5"  # Chunk 2 of 5
}
```

## 🔧 Advanced Usage

### Custom Retriever
```python
from agentic.knowledge import KnowledgeManager, EmbeddingRetriever

km = KnowledgeManager()
km.set_retriever(EmbeddingRetriever(
    persist_directory="./custom_vectors",
    embedding_model="text-embedding-3-large"  # Higher quality
))
```

### Multiple Collections
```python
# Separate collections for different knowledge types
legal_km = create_embedding_knowledge_manager(
    persist_directory="./legal_vectors",
    collection_name="legal_docs"
)

tech_km = create_embedding_knowledge_manager(
    persist_directory="./tech_vectors", 
    collection_name="technical_docs"
)
```

### Integration with Other Frameworks

```python
# Works with any framework
km = create_embedding_knowledge_manager()
km.load_sources(["./docs/"])

# LangChain
knowledge = km.retrieve_for_query("user question")

# OpenAI
knowledge = km.retrieve_for_query("user question")

# LlamaIndex  
all_content = [c['content'] for c in km.loaded_content]
```

## 🚨 Troubleshooting

### Dependencies Missing
```
Note: Using keyword-based retrieval. For better semantic search, install: pip install chromadb openai
```
**Solution**: `pip install agentic[embeddings]`

### OpenAI API Key Missing
```
Warning: Failed to get embeddings: No API key provided
```
**Solution**: Set `OPENAI_API_KEY` environment variable

### Vector DB Corruption
```
Warning: Failed to add content to vector database
```
**Solution**: Delete `.chroma_db` directory to reset

### Performance Issues
- **Large files**: Increase chunk size in EmbeddingRetriever
- **Many sources**: Use separate collections
- **Slow queries**: Reduce max_results parameter

## 📈 Performance Benefits

### Benchmarks (Approximate)
- **Keyword Search**: ~1ms per query
- **Embedding Search**: ~50ms per query (includes OpenAI API call)
- **Change Detection**: ~10ms per source file
- **Re-vectorization**: Only for changed files

### Scalability
- **Document Limit**: Thousands of documents (Chroma handles GB+ datasets)
- **Query Speed**: Sub-second for most knowledge bases
- **Storage**: ~1MB per 100KB of source text (compressed vectors)

## 🎯 Best Practices

### Knowledge Organization
```markdown
# Good structure for embedding search
docs/
├── policies/
│   ├── security.md      # Clear topics
│   ├── hr.md           # Separate domains
│   └── legal.md        # Distinct content
├── guides/
│   ├── onboarding.md   # Process docs
│   └── troubleshooting.md
└── faqs/
    └── common-issues.md
```

### Optimal Chunk Size
- **Short docs**: Keep default (500 chars)
- **Technical docs**: Increase to 800-1000 chars
- **Legal docs**: May need 1500+ chars for context

### Query Optimization
```python
# Good queries (specific, descriptive)
"How to reset user password in admin panel"
"VPN connection troubleshooting steps"
"Remote work policy for international employees"

# Less effective (too broad/vague)  
"help"
"policy"
"fix"
```

The embedding-based knowledge system provides dramatically improved search quality while remaining completely transparent to users of the framework. The automatic fallback ensures compatibility across all environments.