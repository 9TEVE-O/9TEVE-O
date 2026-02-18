# Code Performance Review Checklist

A practical checklist for identifying performance issues during code review or refactoring.

## Quick Performance Audit

Use this checklist when reviewing code for performance issues.

---

## 🔍 Profiling & Measurement

- [ ] Have you profiled the code to identify actual bottlenecks?
- [ ] Are there performance benchmarks for critical paths?
- [ ] Is there monitoring in place to track performance in production?
- [ ] Have you measured the impact of any optimizations?

---

## 🎯 Algorithm & Data Structures

### Time Complexity
- [ ] Are nested loops necessary? (Potential O(n²) or worse)
- [ ] Can hash tables/sets replace linear searches? (O(n) → O(1))
- [ ] Are there redundant computations that could be cached?
- [ ] Is the algorithm the most efficient for the use case?

### Data Structure Selection
- [ ] Lists used for membership testing? (Consider sets/dicts)
- [ ] Frequent insertions/deletions at start? (Consider deque)
- [ ] Need sorted data with fast insertion? (Consider heapq or SortedDict)
- [ ] Key-value pairs with ordering? (Consider OrderedDict)

---

## 🐍 Python-Specific Issues

### Common Anti-patterns
- [ ] String concatenation in loops? (Use `''.join()`)
- [ ] List creation when generator would work? (Memory efficiency)
- [ ] Regular loops instead of list comprehensions?
- [ ] Global variable lookups in hot loops? (Cache as local)
- [ ] Index-based loops where direct iteration (`for x in items`) would be simpler/faster?

### Built-in Usage
- [ ] Manual implementations instead of built-ins? (sum, min, max, any, all)
- [ ] Reinventing the wheel? (Check itertools, collections, functools)
- [ ] Using third-party libraries when standard library suffices?

### Examples to Catch
```python
# ❌ String concatenation in loop
result = ""
for item in items:
    result += str(item)

# ❌ List when generator works
values = [expensive_func(x) for x in huge_list]
total = sum(values)

# ❌ Global lookup in loop
for i in range(n):
    result = math.sqrt(i)  # math looked up each iteration

# ❌ Index-based loop when index is not needed
for i in range(len(items)):
    process(items[i])

# ✅ Direct iteration
for item in items:
    process(item)
```

---

## 🤖 ML/AI Code

### Model Performance
- [ ] Are predictions batched? (vs. one-at-a-time)
- [ ] Using appropriate precision? (float32 vs float64)
- [ ] Model quantized for inference? (If applicable)
- [ ] Unnecessary model loading? (Load once, reuse)
- [ ] GPU utilized when available?

### Data Processing
- [ ] NumPy vectorization used? (vs. Python loops)
- [ ] Pandas operations vectorized? (vs. iterrows/apply)
- [ ] Data loaded efficiently? (Lazy loading, streaming)
- [ ] Appropriate data types? (category, int32 vs int64)

### Examples to Catch
```python
# ❌ Item-by-item prediction
for item in dataset:
    pred = model.predict([item])

# ❌ Python loops on arrays
result = []
for i in range(len(arr)):
    result.append(arr[i] ** 2)

# ❌ Loading entire dataset into memory
data = pd.read_csv('huge_file.csv')
```

---

## 📊 Database & Queries

### Query Optimization
- [ ] N+1 query problem? (Load related data in one query)
- [ ] Missing indexes on frequently queried columns?
- [ ] SELECT * used unnecessarily? (Specify needed columns)
- [ ] Queries in loops? (Batch or use JOINs)
- [ ] Transactions used appropriately?

### Connection Management
- [ ] Connection pooling configured?
- [ ] Connections properly closed? (Use context managers)
- [ ] Too many simultaneous connections?

### Examples to Catch
```python
# ❌ N+1 queries
users = User.query.all()
for user in users:
    posts = Post.query.filter_by(user_id=user.id).all()  # Query per user

# ❌ Query in loop
for item_id in item_ids:
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))

# ❌ No connection pooling
for request in requests:
    conn = create_connection()  # New connection each time
    process(conn, request)
    conn.close()
```

---

## 💾 Memory Management

### Memory Efficiency
- [ ] Large files read in chunks? (vs. loading entirely)
- [ ] Generators used for large sequences? (vs. lists)
- [ ] Unbounded caches? (Use LRU cache with maxsize)
- [ ] Large objects explicitly deleted when done?
- [ ] Memory leaks in long-running processes?

### Resource Management
- [ ] Context managers used for resources? (files, connections)
- [ ] Proper cleanup in exception cases?
- [ ] Circular references preventing garbage collection?

### Examples to Catch
```python
# ❌ Loading entire file
with open('huge_file.txt') as f:
    content = f.read()  # Entire file in memory

# ❌ Unbounded cache
cache = {}  # Grows indefinitely
def get_data(key):
    if key not in cache:
        cache[key] = expensive_query(key)
    return cache[key]

# ❌ No resource cleanup
f = open('file.txt')
data = f.read()
# File never closed if error occurs
```

---

## 🔄 I/O Operations

### File I/O
- [ ] Files read/written in appropriate chunks?
- [ ] Buffering configured optimally?
- [ ] Binary mode for binary data?
- [ ] Unnecessary file operations? (Check if file exists multiple times)

### Network I/O
- [ ] Sequential network calls that could be parallel?
- [ ] Timeouts configured?
- [ ] Retries with exponential backoff?
- [ ] Connection reuse? (Keep-alive)

### Examples to Catch
```python
# ❌ Sequential API calls
results = []
for url in urls:
    response = requests.get(url)  # One at a time
    results.append(response.json())

# ❌ Reading file line by line inefficiently
with open('file.txt') as f:
    lines = [f.readline() for _ in range(1000000)]  # Slow
```

---

## ⚡ Concurrency & Parallelism

### Appropriate Use
- [ ] CPU-bound tasks using multiprocessing? (Not threading)
- [ ] I/O-bound tasks using async/await or threading?
- [ ] GIL considered for Python threading?
- [ ] Thread-safe operations in multi-threaded code?

### Resource Management
- [ ] Thread/process pools sized appropriately?
- [ ] Proper error handling in concurrent code?
- [ ] Deadlocks possible? (Lock ordering, timeouts)
- [ ] Race conditions possible?

### Examples to Catch
```python
# ❌ Threading for CPU-bound work
import threading

threads = []
for data in cpu_intensive_data:
    t = threading.Thread(target=cpu_bound_function, args=(data,))
    threads.append(t)
    t.start()  # GIL prevents true parallelism

# ❌ Sequential I/O operations
for url in urls:
    data = requests.get(url).json()  # Could be concurrent
```

---

## 📝 NLP & Text Processing

### Text Processing
- [ ] Regex patterns compiled once? (Not in loops)
- [ ] Batch processing for NLP pipelines?
- [ ] Efficient tokenization? (Using compiled libraries)
- [ ] String operations optimized?

### Document Processing
- [ ] Large documents streamed? (vs. loading entirely)
- [ ] Embeddings computed in batches?
- [ ] Vector storage optimized? (FAISS, efficient formats)
- [ ] Caching for repeated computations?

### Examples to Catch
```python
# ❌ Dynamic regex compilation in loop
for text in texts:
    pattern = re.compile(build_pattern(config))
    matches = pattern.findall(text)

# ✅ Compile once and reuse
pattern = re.compile(build_pattern(config))
for text in texts:
    matches = pattern.findall(text)

# ❌ Sequential document processing
docs = [nlp(text) for text in texts]  # No batching

# ❌ Inefficient embeddings
embeddings = []
for doc in docs:
    emb = model.encode(doc)  # One at a time
    embeddings.append(emb)
```

---

## 🎨 Code Structure

### Function Design
- [ ] Functions doing too much? (Could be split)
- [ ] Expensive operations repeated? (Could cache results)
- [ ] Unnecessary work in hot paths?
- [ ] Early returns to avoid unnecessary computation?

### Imports & Initialization
- [ ] Expensive imports in hot paths?
- [ ] Heavy initialization in loops?
- [ ] Lazy loading where appropriate?

### Examples to Catch
```python
# ❌ Heavy import in function
def process_data(data):
    import pandas as pd  # Import on every call
    return pd.DataFrame(data).mean()

# ❌ Initialization in loop
for item in items:
    processor = HeavyProcessor()  # Created each iteration
    result = processor.process(item)
```

---

## 🧪 Testing Performance

### Benchmarking
- [ ] Performance tests for critical paths?
- [ ] Regression tests for performance?
- [ ] Realistic data sizes in tests?
- [ ] Performance budgets defined?

---

## 📊 Monitoring & Observability

### Production Monitoring
- [ ] Key metrics tracked? (Response time, throughput)
- [ ] Slow operation logging?
- [ ] Resource usage monitored? (CPU, memory)
- [ ] Alerts configured for degradation?

### Debugging Aids
- [ ] Profiling hooks in production code?
- [ ] Performance tracing enabled?
- [ ] Query logging for slow operations?

---

## 🚀 Quick Wins

### High-Impact, Low-Effort Optimizations

1. **Add Database Indexes**
   - Identify slow queries
   - Add indexes on filtered/joined columns
   - Can provide 10-100x speedups

2. **Enable Caching**
   - LRU cache for expensive functions
   - Redis for shared state
   - Query result caching

3. **Batch Operations**
   - Database bulk inserts/updates
   - API call batching
   - Model prediction batching

4. **Use Built-in Functions**
   - Replace manual loops with built-ins
   - Use library functions over custom implementations

5. **Vectorize NumPy/Pandas Operations**
   - Replace loops with array operations
   - Use built-in Pandas methods

6. **Add Profiling**
   - Identify actual bottlenecks
   - Measure before optimizing

---

## 🎯 When to Optimize

### Optimize When:
- ✅ Profiling shows clear bottleneck
- ✅ Users experiencing slow response times
- ✅ Resource costs are high
- ✅ Scalability issues emerging
- ✅ Specific performance requirements not met

### Don't Optimize When:
- ❌ No measurement/profiling done
- ❌ Code clarity would significantly suffer
- ❌ Premature optimization (not a proven bottleneck)
- ❌ Micro-optimizations on non-critical paths
- ❌ Better algorithms available

---

## 📚 Review Process

1. **Identify** - Use this checklist during code review
2. **Measure** - Profile suspected issues
3. **Prioritize** - Focus on highest impact items
4. **Optimize** - Make targeted improvements
5. **Validate** - Benchmark improvements
6. **Document** - Note optimization decisions

---

## Tools Reference

### Profiling
```bash
# CPU profiling
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats

# Line profiling
kernprof -l -v script.py

# Memory profiling
python -m memory_profiler script.py
```

### Benchmarking
```python
# Quick timing
import timeit
timeit.timeit('func()', number=1000)

# Detailed benchmarking
import pytest

def test_performance(benchmark):
    result = benchmark(my_function, arg1, arg2)
```

### Database
```sql
-- PostgreSQL query analysis
EXPLAIN ANALYZE SELECT ...;

-- Show slow queries
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

---

## Summary

**Remember the 80/20 rule**: 80% of execution time is spent in 20% of the code. Focus optimization efforts on the actual bottlenecks identified through profiling, not on premature optimization of code that doesn't impact performance.

**Optimization Priority:**
1. Algorithm/data structure (biggest impact)
2. Database queries and indexes
3. I/O operations (batching, caching)
4. Vectorization (NumPy/Pandas)
5. Concurrency (for appropriate workloads)
6. Micro-optimizations (lowest priority)
