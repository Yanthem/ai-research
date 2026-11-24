---
description: Analyze code for performance issues and suggest optimizations
---

Review $ARGUMENTS (or the code in context if empty) for these issues, most important first:

1. Performance bottlenecks: O(n²) operations, inefficient loops
2. Memory: unreleased resources, large objects held too long
3. Better algorithms or data structures
4. Caching: repeated computations or repeated API calls
5. Concurrency: race conditions, blocking calls

For each issue give severity (Critical/High/Medium/Low), location (`file:line`), why it is slow, and a fix with a code example.
