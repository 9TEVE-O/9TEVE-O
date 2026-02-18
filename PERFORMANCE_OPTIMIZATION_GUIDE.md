# Code Performance Optimization Guide

A comprehensive guide for identifying and improving slow or inefficient code, with focus on AI/ML, NLP, and document intelligence systems.

## Table of Contents
1. [Performance Profiling](#performance-profiling)
2. [Algorithm Optimization](#algorithm-optimization)
3. [Python-Specific Optimizations](#python-specific-optimizations)
4. [ML/AI Performance Optimization](#mlai-performance-optimization)
5. [Database & I/O Optimization](#database--io-optimization)
6. [Memory Management](#memory-management)
7. [Concurrency & Parallelism](#concurrency--parallelism)
8. [NLP & Document Processing](#nlp--document-processing)

---

## Performance Profiling

### Identify Bottlenecks First
Before optimizing, always measure and identify actual bottlenecks.

#### Python Profiling Tools
```python
# cProfile - Standard profiler
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions

# line_profiler - Line-by-line profiling
# Install: pip install line-profiler
# Usage: @profile decorator and run with kernprof
@profile
def slow_function():
    # Your code
    pass

# memory_profiler - Memory usage
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code
    pass
```

#### Time Complexity Analysis
```python
import timeit

# Measure execution time
execution_time = timeit.timeit(
    'function_to_test()',
    setup='from __main__ import function_to_test',
    number=1000
)
```

---

## Algorithm Optimization

### Choose Efficient Data Structures

#### ❌ Inefficient - O(n) lookup
```python
# List membership testing
items = [1, 2, 3, 4, 5]
if target in items:  # O(n) - linear search
    pass
```

#### ✅ Efficient - O(1) lookup
```python
# Set membership testing
items = {1, 2, 3, 4, 5}
if target in items:  # O(1) - hash lookup
    pass
```

### Avoid Nested Loops When Possible

#### ❌ Inefficient - O(n²)
```python
def find_common_elements(list1, list2):
    common = []
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                common.append(item1)
    return common
```

#### ✅ Efficient - O(n)
```python
def find_common_elements(list1, list2):
    return list(set(list1) & set(list2))
```

### Use Built-in Functions
Built-in functions are implemented in C and are much faster.

#### ❌ Inefficient
```python
# Manual sum
total = 0
for num in numbers:
    total += num
```

#### ✅ Efficient
```python
# Built-in sum
total = sum(numbers)
```

---

## Python-Specific Optimizations

### List Comprehensions vs. Loops

#### ❌ Less Efficient
```python
squares = []
for i in range(1000):
    squares.append(i ** 2)
```

#### ✅ More Efficient
```python
squares = [i ** 2 for i in range(1000)]
```

### Generator Expressions for Large Data

#### ❌ Memory Inefficient
```python
# Creates entire list in memory
large_data = [process(item) for item in huge_dataset]
total = sum(large_data)
```

#### ✅ Memory Efficient
```python
# Processes items one at a time
large_data = (process(item) for item in huge_dataset)
total = sum(large_data)
```

### String Concatenation

#### ❌ Inefficient - O(n²)
```python
result = ""
for item in items:
    result += str(item)  # Creates new string each time
```

#### ✅ Efficient - O(n)
```python
result = "".join(str(item) for item in items)
```

### Use Local Variables
Local variable access is faster than global variable access.

#### ❌ Slower
```python
import math

def calculate_many():
    results = []
    for i in range(10000):
        results.append(math.sqrt(i))  # Global lookup each time
    return results
```

#### ✅ Faster
```python
import math

def calculate_many():
    sqrt = math.sqrt  # Local reference
    results = []
    for i in range(10000):
        results.append(sqrt(i))
    return results
```

### Avoid Function Call Overhead in Loops

#### ❌ Inefficient
```python
def process_items(items):
    for item in items:
        result = expensive_function(item)
        if result:
            yield result
```

#### ✅ More Efficient (if applicable)
```python
def process_items(items):
    # Batch processing if function supports it
    results = expensive_function_batch(items)
    return (r for r in results if r)
```

---

## ML/AI Performance Optimization

### Vectorization with NumPy

#### ❌ Inefficient - Python loops
```python
import numpy as np

def slow_computation(arr):
    result = np.zeros_like(arr)
    for i in range(len(arr)):
        for j in range(len(arr[0])):
            result[i, j] = arr[i, j] ** 2 + 2 * arr[i, j]
    return result
```

#### ✅ Efficient - Vectorized operations
```python
import numpy as np

def fast_computation(arr):
    return arr ** 2 + 2 * arr  # 10-100x faster
```

### Batch Processing

#### ❌ Inefficient - Item-by-item
```python
predictions = []
for item in dataset:
    pred = model.predict(item.reshape(1, -1))
    predictions.append(pred)
```

#### ✅ Efficient - Batch prediction
```python
# Process in batches
batch_size = 32
predictions = model.predict(dataset, batch_size=batch_size)
```

### Use Appropriate Data Types

#### ❌ Memory Inefficient
```python
import numpy as np

# float64 uses 8 bytes per element
large_array = np.array(data, dtype=np.float64)
```

#### ✅ Memory Efficient
```python
import numpy as np

# float32 uses 4 bytes per element (50% memory savings)
# Often sufficient precision for ML tasks
large_array = np.array(data, dtype=np.float32)
```

### Model Optimization

```python
# 1. Use mixed precision training (PyTorch example)
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
for data, target in dataloader:
    optimizer.zero_grad()
    with autocast():
        output = model(data)
        loss = criterion(output, target)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()

# 2. Quantization (reduce model size and increase speed)
import torch

# Dynamic quantization
quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)

# 3. Model pruning (remove unnecessary weights)
import torch.nn.utils.prune as prune

# Prune 40% of weights
prune.l1_unstructured(model.layer, name='weight', amount=0.4)
```

### GPU Optimization

```python
# Transfer data to GPU efficiently
import torch

# ❌ Inefficient - multiple small transfers
for batch in dataloader:
    data = batch['data'].cuda()
    labels = batch['labels'].cuda()
    
# ✅ Efficient - pin memory for faster transfer
dataloader = DataLoader(
    dataset,
    batch_size=32,
    pin_memory=True,  # Faster GPU transfer
    num_workers=4     # Parallel data loading
)

# Use non_blocking transfers
for batch in dataloader:
    data = batch['data'].cuda(non_blocking=True)
    labels = batch['labels'].cuda(non_blocking=True)
```

---

## Database & I/O Optimization

### Batch Database Operations

#### ❌ Inefficient - Individual queries
```python
for item in items:
    cursor.execute("INSERT INTO table VALUES (?)", (item,))
    connection.commit()  # Commit each time
```

#### ✅ Efficient - Batch operations
```python
cursor.executemany("INSERT INTO table VALUES (?)", items)
connection.commit()  # Single commit
```

### Use Connection Pooling

```python
from sqlalchemy import create_engine, pool

# Connection pool for database connections
engine = create_engine(
    'postgresql://user:pass@localhost/db',
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### Index Database Queries

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_document_created_at ON documents(created_at);

-- Composite index for multi-column queries
CREATE INDEX idx_user_created ON users(user_id, created_at);
```

### File I/O Optimization

#### ❌ Inefficient - Reading entire file
```python
with open('large_file.txt', 'r') as f:
    content = f.read()  # Loads entire file into memory
    for line in content.split('\n'):
        process(line)
```

#### ✅ Efficient - Streaming
```python
with open('large_file.txt', 'r') as f:
    for line in f:  # Reads line by line
        process(line)
```

### Caching

```python
from functools import lru_cache

# Cache expensive computations
@lru_cache(maxsize=128)
def expensive_computation(n):
    # Complex calculation
    return result

# Use Redis for distributed caching
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def get_data(key):
    # Check cache first
    cached = r.get(key)
    if cached:
        return cached
    
    # Compute if not cached
    data = expensive_database_query(key)
    r.setex(key, 3600, data)  # Cache for 1 hour
    return data
```

---

## Memory Management

### Avoid Memory Leaks

#### ❌ Potential Memory Leak
```python
class DataProcessor:
    def __init__(self):
        self.cache = []  # Grows indefinitely
    
    def process(self, data):
        self.cache.append(data)
        return analyze(data)
```

#### ✅ Bounded Memory Usage
```python
from collections import deque

class DataProcessor:
    def __init__(self, max_cache=1000):
        self.cache = deque(maxlen=max_cache)  # Auto-removes old items
    
    def process(self, data):
        self.cache.append(data)
        return analyze(data)
```

### Use Context Managers

```python
# Automatic resource cleanup
with open('file.txt', 'r') as f:
    data = f.read()
# File automatically closed

# Database connections
with database.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(query)
# Connection automatically returned to pool
```

### Delete Large Objects

```python
import gc

large_data = load_huge_dataset()
process(large_data)

# Explicitly delete and collect garbage
del large_data
gc.collect()
```

---

## Concurrency & Parallelism

### Multiprocessing for CPU-Bound Tasks

```python
from multiprocessing import Pool
import os

def cpu_intensive_task(data):
    # Heavy computation
    return result

if __name__ == '__main__':
    data_chunks = [chunk1, chunk2, chunk3, chunk4]
    
    # Use all CPU cores
    with Pool(processes=os.cpu_count()) as pool:
        results = pool.map(cpu_intensive_task, data_chunks)
```

### Async I/O for I/O-Bound Tasks

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Run concurrent requests
urls = ['url1', 'url2', 'url3']
results = asyncio.run(fetch_all(urls))
```

### Thread Pools for I/O Operations

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def download_file(url):
    response = requests.get(url)
    return response.content

urls = ['url1', 'url2', 'url3']

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(download_file, urls))
```

---

## NLP & Document Processing

### Efficient Text Processing

#### ❌ Inefficient - Repeated regex compilation
```python
import re

def process_documents(documents):
    results = []
    for doc in documents:
        # Regex compiled each time
        matches = re.findall(r'\b[A-Z][a-z]+\b', doc)
        results.append(matches)
    return results
```

#### ✅ Efficient - Compile regex once
```python
import re

pattern = re.compile(r'\b[A-Z][a-z]+\b')

def process_documents(documents):
    results = []
    for doc in documents:
        matches = pattern.findall(doc)
        results.append(matches)
    return results
```

### Batch Text Processing with spaCy

```python
import spacy

nlp = spacy.load("en_core_web_sm")

# ❌ Inefficient - Process one at a time
docs = [nlp(text) for text in texts]

# ✅ Efficient - Batch processing with pipeline
docs = list(nlp.pipe(texts, batch_size=50, n_process=4))
```

### Efficient Document Embeddings

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

documents = ['doc1', 'doc2', 'doc3', ...]

# ❌ Inefficient
embeddings = [model.encode(doc) for doc in documents]

# ✅ Efficient - Batch encoding
embeddings = model.encode(
    documents,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True  # Faster than tensors for storage
)
```

### Use Efficient Storage for Vectors

```python
# Use FAISS for efficient similarity search
import faiss
import numpy as np

# Create index
dimension = 384  # embedding dimension
index = faiss.IndexFlatL2(dimension)

# Add vectors
vectors = np.array(embeddings).astype('float32')
index.add(vectors)

# Fast similarity search
k = 5  # top 5 results
distances, indices = index.search(query_vector, k)
```

### Stream Large Documents

```python
# ❌ Inefficient - Load entire file
with open('huge_document.txt', 'r') as f:
    text = f.read()
    tokens = tokenize(text)

# ✅ Efficient - Process in chunks
def process_large_document(filepath, chunk_size=1000000):
    with open(filepath, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield process_chunk(chunk)
```

### RAG Optimization

```python
# Optimize retrieval-augmented generation
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Use efficient embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",  # Fast, small model
    model_kwargs={'device': 'cuda'},  # Use GPU
    encode_kwargs={'batch_size': 32}  # Batch encoding
)

# Create vector store with efficient retrieval
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_metadata={"hnsw:space": "cosine"}  # Efficient similarity
)

# Optimize retrieval
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximum marginal relevance
    search_kwargs={
        "k": 5,  # Retrieve fewer docs
        "fetch_k": 20  # Consider more for diversity
    }
)
```

---

## Best Practices Summary

### 1. **Measure Before Optimizing**
- Use profiling tools to identify actual bottlenecks
- Don't optimize prematurely

### 2. **Algorithm First, Micro-optimizations Later**
- Changing O(n²) to O(n log n) > micro-optimizations
- Choose appropriate data structures

### 3. **Leverage Libraries and Built-ins**
- NumPy, Pandas for data operations
- Use compiled extensions when available

### 4. **Batch Operations**
- Database queries
- API calls
- Model predictions

### 5. **Use Appropriate Concurrency**
- Async for I/O-bound tasks
- Multiprocessing for CPU-bound tasks
- Thread pools for I/O operations

### 6. **Memory Management**
- Stream large files
- Use generators for large datasets
- Implement bounded caches

### 7. **Cache Strategically**
- Cache expensive computations
- Use appropriate invalidation strategies
- Consider distributed caching for scale

### 8. **Monitor in Production**
- Application Performance Monitoring (APM)
- Log slow queries and operations
- Set up alerts for performance degradation

---

## Performance Monitoring Tools

### Python Profiling
- `cProfile` - CPU profiling
- `line_profiler` - Line-by-line profiling
- `memory_profiler` - Memory usage
- `py-spy` - Sampling profiler (no code changes needed)

### Application Monitoring
- **Prometheus** + **Grafana** - Metrics and visualization
- **New Relic** / **DataDog** - APM solutions
- **Sentry** - Error tracking and performance monitoring

### Database Monitoring
- `EXPLAIN ANALYZE` - Query execution plans
- **pgBadger** (PostgreSQL) - Log analyzer
- **MySQL Slow Query Log** - Identify slow queries

---

## Resources

### Books
- "High Performance Python" by Micha Gorelick & Ian Ozsvald
- "Python Performance Programming" by Gabriele Lanaro

### Online Tools
- [Python Speed Center](https://speed.python.org/)
- [Perfetto](https://perfetto.dev/) - Performance profiling
- [Scalene](https://github.com/plasma-umass/scalene) - CPU/GPU/memory profiler

### Benchmarking
```python
# Use pytest-benchmark for reliable benchmarks
def test_performance(benchmark):
    result = benchmark(function_to_test, arg1, arg2)
    assert result == expected_value
```

---

## Conclusion

Performance optimization is an iterative process:
1. **Profile** to identify bottlenecks
2. **Optimize** the most impactful areas
3. **Measure** improvements
4. **Repeat** as needed

Focus on algorithmic improvements first, then optimize hot paths identified through profiling. Remember: "Premature optimization is the root of all evil" - Donald Knuth. Always measure before and after optimization to ensure you're actually improving performance.
