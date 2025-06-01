"""
Knowledge Management Component - Framework Agnostic

A reusable knowledge integration system that can be used by any GenAI framework.
Provides pluggable knowledge loading, processing, and retrieval capabilities.

Usage:
    from agentic.knowledge import KnowledgeManager, FileLoader, SimpleRetriever
    
    # Configure knowledge system
    km = KnowledgeManager()
    km.add_loader(FileLoader())
    km.add_retriever(SimpleRetriever())
    
    # Load knowledge sources
    km.load_sources(["docs/", "policies.md", "https://api.example.com/docs"])
    
    # Retrieve relevant knowledge for a query
    relevant_content = km.retrieve("How do I reset my password?")
"""

from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import os
import json
from pathlib import Path


class KnowledgeLoader(Protocol):
    """Protocol for knowledge loaders - load content from various sources."""
    
    def can_load(self, source: str) -> bool:
        """Check if this loader can handle the given source."""
        ...
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load content from source, return metadata + content."""
        ...


class KnowledgeRetriever(Protocol):
    """Protocol for knowledge retrievers - find relevant content for queries."""
    
    def add_content(self, content: Dict[str, Any]) -> None:
        """Add content to the retrieval system."""
        ...
    
    def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant content for the query."""
        ...


class FileLoader:
    """Load content from files and directories."""
    
    def __init__(self, max_file_size: int = 10000, encoding: str = 'utf-8'):
        self.max_file_size = max_file_size
        self.encoding = encoding
    
    def can_load(self, source: str) -> bool:
        """Check if source is a file or directory."""
        return not source.startswith(('http://', 'https://'))
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load file or directory content."""
        try:
            path = Path(source)
            
            if path.is_file():
                return self._load_file(path)
            elif path.is_dir():
                return self._load_directory(path)
            else:
                return {
                    'source': source,
                    'content': '',
                    'error': 'Path not found',
                    'type': 'error'
                }
                
        except Exception as e:
            return {
                'source': source,
                'content': '',
                'error': str(e),
                'type': 'error'
            }
    
    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load content from a single file."""
        try:
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
                
            # Truncate if too large
            if len(content) > self.max_file_size:
                content = content[:self.max_file_size] + "... (truncated)"
            
            return {
                'source': str(path),
                'content': content,
                'type': 'file',
                'size': len(content),
                'extension': path.suffix
            }
            
        except UnicodeDecodeError:
            return {
                'source': str(path),
                'content': f"Binary file: {path.name}",
                'type': 'binary',
                'size': path.stat().st_size if path.exists() else 0
            }
    
    def _load_directory(self, path: Path) -> Dict[str, Any]:
        """Load content from directory (list files or aggregate)."""
        try:
            files = []
            total_content = []
            
            for file_path in path.rglob("*.md"):  # Focus on markdown files
                if file_path.is_file():
                    file_content = self._load_file(file_path)
                    files.append(file_path.name)
                    if file_content.get('content'):
                        total_content.append(f"=== {file_path.name} ===\n{file_content['content']}")
            
            # Fallback to listing all files if no markdown
            if not files:
                files = [f.name for f in path.iterdir() if f.is_file()][:20]
            
            content = "\n\n".join(total_content) if total_content else f"Directory contains: {', '.join(files)}"
            
            return {
                'source': str(path),
                'content': content,
                'type': 'directory',
                'files': files,
                'file_count': len(files)
            }
            
        except Exception as e:
            return {
                'source': str(path),
                'content': '',
                'error': str(e),
                'type': 'error'
            }


class URLLoader:
    """Load content from URLs."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def can_load(self, source: str) -> bool:
        """Check if source is a URL."""
        return source.startswith(('http://', 'https://'))
    
    def load(self, source: str) -> Dict[str, Any]:
        """Load content from URL."""
        try:
            import requests
            response = requests.get(source, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'source': source,
                'content': response.text[:10000],  # Limit size
                'type': 'url',
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', '')
            }
            
        except ImportError:
            return {
                'source': source,
                'content': f"URL: {source} (requests library not available)",
                'type': 'url_placeholder',
                'error': 'requests not installed'
            }
        except Exception as e:
            return {
                'source': source,
                'content': f"URL: {source} (failed to load: {str(e)})",
                'type': 'url_error',
                'error': str(e)
            }


class SimpleRetriever:
    """Simple keyword-based content retrieval."""
    
    def __init__(self):
        self.content_store: List[Dict[str, Any]] = []
    
    def add_content(self, content: Dict[str, Any]) -> None:
        """Add content to the store."""
        self.content_store.append(content)
    
    def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve content using simple keyword matching."""
        if not query or not self.content_store:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score content by keyword overlap
        scored_content = []
        for content in self.content_store:
            if content.get('error') or not content.get('content'):
                continue
                
            content_text = content['content'].lower()
            content_words = set(content_text.split())
            
            # Simple scoring: count overlapping words
            overlap = len(query_words.intersection(content_words))
            if overlap > 0:
                scored_content.append((overlap, content))
        
        # Sort by score and return top results
        scored_content.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored_content[:max_results]]


class KnowledgeManager:
    """
    Main knowledge management system - framework agnostic.
    
    Coordinates loaders and retrievers to provide knowledge integration
    for any GenAI framework.
    """
    
    def __init__(self):
        self.loaders: List[KnowledgeLoader] = []
        self.retriever: Optional[KnowledgeRetriever] = None
        self.sources: List[str] = []
        self.loaded_content: List[Dict[str, Any]] = []
    
    def add_loader(self, loader: KnowledgeLoader) -> None:
        """Add a knowledge loader."""
        self.loaders.append(loader)
    
    def set_retriever(self, retriever: KnowledgeRetriever) -> None:
        """Set the knowledge retriever."""
        self.retriever = retriever
    
    def load_sources(self, sources: List[str]) -> Dict[str, Any]:
        """
        Load content from multiple sources.
        
        Returns:
            Dictionary with loading statistics and any errors
        """
        self.sources = sources
        self.loaded_content = []
        
        stats = {
            'total_sources': len(sources),
            'loaded_successfully': 0,
            'failed': 0,
            'errors': []
        }
        
        for source in sources:
            loaded = False
            
            # Try each loader until one can handle the source
            for loader in self.loaders:
                if loader.can_load(source):
                    try:
                        content = loader.load(source)
                        self.loaded_content.append(content)
                        
                        # Add to retriever if available
                        if self.retriever:
                            self.retriever.add_content(content)
                        
                        if content.get('error'):
                            stats['errors'].append(f"{source}: {content['error']}")
                            stats['failed'] += 1
                        else:
                            stats['loaded_successfully'] += 1
                        
                        loaded = True
                        break
                        
                    except Exception as e:
                        stats['errors'].append(f"{source}: {str(e)}")
                        stats['failed'] += 1
                        loaded = True
                        break
            
            if not loaded:
                stats['errors'].append(f"{source}: No suitable loader found")
                stats['failed'] += 1
        
        return stats
    
    def retrieve_for_query(self, query: str, max_results: int = 3) -> str:
        """
        Retrieve relevant knowledge for a query and format for LLM consumption.
        
        Args:
            query: The user query or context
            max_results: Maximum number of knowledge pieces to return
            
        Returns:
            Formatted string ready for LLM prompt injection
        """
        if not self.retriever or not self.loaded_content:
            return ""
        
        relevant_content = self.retriever.retrieve(query, max_results)
        
        if not relevant_content:
            return ""
        
        # Format for LLM consumption
        formatted_parts = []
        for i, content in enumerate(relevant_content, 1):
            source = content.get('source', 'Unknown')
            text = content.get('content', '')
            
            if text:
                formatted_parts.append(f"Knowledge Source {i} ({source}):\n{text}")
        
        return "\n\n".join(formatted_parts) if formatted_parts else ""
    
    def get_all_content_summary(self) -> str:
        """Get a summary of all loaded knowledge for LLM context."""
        if not self.loaded_content:
            return ""
        
        summaries = []
        for content in self.loaded_content:
            if content.get('error'):
                continue
                
            source = content.get('source', 'Unknown')
            content_type = content.get('type', 'unknown')
            
            if content_type == 'file':
                size = content.get('size', 0)
                summaries.append(f"File: {source} ({size} chars)")
            elif content_type == 'directory':
                file_count = content.get('file_count', 0)
                summaries.append(f"Directory: {source} ({file_count} files)")
            elif content_type == 'url':
                summaries.append(f"URL: {source}")
            else:
                summaries.append(f"Source: {source}")
        
        return "Available Knowledge: " + ", ".join(summaries) if summaries else ""


# Convenience function for quick setup
def create_default_knowledge_manager() -> KnowledgeManager:
    """Create a KnowledgeManager with default loaders and retriever."""
    km = KnowledgeManager()
    km.add_loader(FileLoader())
    km.add_loader(URLLoader())
    km.set_retriever(SimpleRetriever())
    return km