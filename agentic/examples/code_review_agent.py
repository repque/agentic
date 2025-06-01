"""
Code review agent demonstrating developer workflow automation.

Shows how to build agents for technical workflows with validation and structured responses.
"""

from agentic.agent import Agent
from agentic.models import AgentState, Message, CategoryRequirement, HandlerResponse


class CodeReviewAgent(Agent):
    """
    Code review agent for automated PR analysis and feedback.
    
    Demonstrates:
    - Technical domain expertise
    - Structured validation requirements  
    - Integration patterns (would integrate with GitHub, Jira, etc.)
    - Developer-focused workflows
    """
    
    def __init__(self):
        super().__init__(
            name="code_review_agent",
            llm="openai/gpt-4",
            confidence_threshold=0.8  # Higher threshold for code review accuracy
        )
        
        # Register handlers for different review types
        self.register_handler("CodeReview", self.handle_code_review)
        self.register_handler("SecurityReview", self.handle_security_review)
        self.register_handler("PerformanceReview", self.handle_performance_review)
    
    def get_personality(self) -> str:
        """Technical but constructive code reviewer personality."""
        return """You are a senior software engineer and code reviewer. 
        You provide constructive, detailed feedback on code quality, security, 
        performance, and best practices. You are thorough but encouraging, 
        always explaining the 'why' behind your suggestions. You follow industry 
        standards and help developers improve their skills."""
    
    def get_classification_categories(self) -> list[str]:
        """Types of code review requests."""
        return [
            "CodeReview",
            "SecurityReview", 
            "PerformanceReview",
            "ArchitectureReview",
            "Documentation"
        ]
    
    def get_category_requirements(self) -> list[CategoryRequirement]:
        """Information needed for each review type."""
        return [
            CategoryRequirement(
                category="CodeReview", 
                required_fields=["repository_url", "pull_request_number"]
            ),
            CategoryRequirement(
                category="SecurityReview", 
                required_fields=["repository_url", "security_scope"]
            ),
            CategoryRequirement(
                category="PerformanceReview", 
                required_fields=["repository_url", "performance_concern"]
            )
        ]
    
    def get_knowledge(self) -> list[str]:
        """Code review knowledge sources."""
        return [
            "coding_standards.md",
            "security_guidelines.md", 
            "performance_best_practices.md",
            "architecture_patterns/",
            "code_review_checklist.md"
        ]
    
    def handle_code_review(self, state: AgentState) -> HandlerResponse:
        """Handle general code review requests."""
        
        # Extract PR information (in real implementation, would fetch from GitHub API)
        message = state.messages[-1].content
        
        # Generate review ID
        import random
        review_id = f"CR-{random.randint(100000, 999999)}"
        
        response = f"""🔍 **Code Review Initiated**

**Review ID:** {review_id}
**Type:** Standard Code Review
**Status:** In Progress

**Automated Analysis Results:**

✅ **What Looks Good:**
• Code follows consistent formatting standards
• Proper error handling implemented
• Unit tests included with good coverage
• Clear variable and function naming

⚠️ **Areas for Improvement:**

**Code Quality:**
• Consider extracting the validation logic in `UserService.validate()` into separate methods
• The `processPayment()` method is doing too much - violates Single Responsibility Principle
• Add JSDoc comments for public API methods

**Security:**
• SQL query in `UserRepository.findByEmail()` should use parameterized queries
• Add input validation for user-provided data
• Consider rate limiting for the login endpoint

**Performance:**
• Database query in the loop (lines 45-52) - consider batch operations
• Large JSON objects being passed by value - consider references
• Missing indexes on frequently queried columns

**Recommendations:**
1. **Priority 1 (Security):** Fix SQL injection vulnerability
2. **Priority 2 (Performance):** Optimize database queries  
3. **Priority 3 (Maintainability):** Refactor large methods

**Next Steps:**
• Address Priority 1 issues before merging
• I'll re-review once changes are pushed
• Feel free to ask questions about any suggestions

**Estimated fix time:** 2-3 hours
**Re-review ETA:** 1 hour after changes

Would you like me to elaborate on any of these points or help with implementation approaches?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_security_review(self, state: AgentState) -> HandlerResponse:
        """Handle security-focused code reviews."""
        
        response = """🛡️ **Security Review Report**

**Security Assessment:** MEDIUM RISK
**Review Date:** December 28, 2024
**Scope:** Authentication & Data Handling

**🚨 Security Findings:**

**HIGH PRIORITY:**
1. **SQL Injection Risk (Line 67)**
   ```python
   # Vulnerable
   query = f"SELECT * FROM users WHERE email = '{email}'"
   
   # Fix
   query = "SELECT * FROM users WHERE email = %s"
   cursor.execute(query, (email,))
   ```

2. **Hardcoded Secrets (config.py)**
   • API keys and passwords in source code
   • Move to environment variables or secret management
   • Add config.py to .gitignore

**MEDIUM PRIORITY:**
3. **Missing Authentication Checks**
   • Several endpoints lack proper authorization
   • Implement middleware for protected routes
   • Add role-based access control

4. **Insufficient Input Validation**
   • User inputs not sanitized
   • Missing CSRF protection  
   • Add input validation library

**LOW PRIORITY:**
5. **Information Disclosure**
   • Error messages reveal internal structure
   • Debug mode enabled in production config
   • Implement generic error responses

**✅ Security Strengths:**
• HTTPS properly configured
• Password hashing using bcrypt
• Session management looks secure
• CORS configured appropriately

**🔧 Recommended Actions:**
1. **Immediate:** Fix SQL injection (< 2 hours)
2. **This Sprint:** Remove hardcoded secrets (< 4 hours)  
3. **Next Sprint:** Implement comprehensive auth middleware
4. **Ongoing:** Security training for team

**Security Score:** 6.5/10
**Target Score:** 8.5/10

Would you like specific code examples for any of these fixes?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_performance_review(self, state: AgentState) -> HandlerResponse:
        """Handle performance-focused code reviews."""
        
        response = """⚡ **Performance Review Report**

**Performance Score:** 7.2/10
**Load Test Results:** 850 req/sec (Target: 1000 req/sec)
**Memory Usage:** 245MB average (Acceptable)

**🐌 Performance Bottlenecks:**

**Database Layer:**
1. **N+1 Query Problem (UserController)**
   ```python
   # Inefficient - 101 queries for 100 users
   for user in users:
       user.posts = Post.objects.filter(user_id=user.id)
   
   # Efficient - 2 queries total  
   users = User.objects.prefetch_related('posts').all()
   ```

2. **Missing Database Indexes**
   • Add index on `posts.created_at` (frequent sorting)
   • Add composite index on `users(email, status)`
   • Consider partitioning for large tables

**Application Layer:**
3. **Inefficient Data Structures**
   • Linear search in `findUserById()` - use dict/map
   • Large arrays copied unnecessarily
   • Consider caching frequently accessed data

4. **Memory Management**
   • Large objects not garbage collected properly
   • Connection pool not optimized
   • File handles not closed in error paths

**Frontend Impact:**
5. **Large Response Payloads**
   • API returns full user objects (12KB each)
   • Implement field selection: `/api/users?fields=id,name,email`
   • Add pagination for large lists

**🚀 Optimization Recommendations:**

**Quick Wins (< 4 hours):**
• Add database indexes → +15% performance
• Fix N+1 queries → +25% performance  
• Implement response pagination → +10% performance

**Medium Term (1-2 sprints):**
• Add Redis caching layer → +30% performance
• Optimize database queries → +20% performance
• Implement lazy loading → +15% performance

**Expected Results:**
• Target: 1200 req/sec (+40% improvement)
• Memory: 180MB average (-25% reduction)
• Response time: < 150ms (-30% improvement)

**Monitoring Recommendations:**
• Add APM tools (DataDog, New Relic)
• Set up performance budgets
• Implement automated performance testing

Would you like me to prioritize these optimizations or provide implementation details for any specific area?"""
        
        return HandlerResponse(
            messages=[Message(role="assistant", content=response)]
        )
    
    def handle_low_confidence(self, state: AgentState) -> HandlerResponse:
        """Escalate complex technical reviews."""
        return HandlerResponse(
            messages=[Message(
                role="assistant",
                content="Your code review is being reviewed by our senior team and we'll get back to you shortly."
            )]
        )