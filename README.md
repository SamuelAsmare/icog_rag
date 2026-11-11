# Icog_rag

An AI-powered knowledge assistant for ICog that uses Retrieval-Augmented Generation (RAG) to answer questions from the attached ICog document library. Built with React, FastAPI, Gemini, Redis, and Qdrant.


# Caching

## 1. Cache-Aside vs. Read-Through

Both strategies improve read performance by storing frequently accessed data in a cache.

- **Cache-Aside:** The application checks the cache first. If the data is missing (cache miss), the application retrieves it from the database and manually stores it in the cache. The application manages the caching logic.
- **Read-Through:** The application requests data from the cache. If the data is missing, the cache itself retrieves it from the database, stores it, and returns it to the application.

**Difference:** In cache-aside, the application manages cache population, while in read-through, the caching layer manages it.

## 2. Write-Through vs. Write-Behind/Write-Back vs. Write-Around

- **Write-Through:** Data is written to both the cache and the database simultaneously. This keeps the cache and database consistent but can increase write latency.
- **Write-Behind (Write-Back):** Data is first written to the cache and later written to the database asynchronously. It provides faster writes but risks data loss if the cache fails before data is persisted.
- **Write-Around:** Data is written directly to the database without updating the cache. This avoids caching data that may not be read again but can cause a cache miss on the next read.

## 3. TTL, Invalidation, and Eviction

- **TTL (Time To Live):** Defines how long cached data remains valid before it automatically expires. Redis supports TTL using commands such as `EXPIRE` and `SET ... EX`.
- **Invalidation:** Removing or marking cached data as outdated when the original data changes. It prevents applications from returning stale information.
- **Eviction:** Removing cached data when Redis reaches its configured memory limit. Redis uses eviction policies to decide which keys to remove.

## 4. Eviction Policies

| Policy | Description | Advantage | Disadvantage |
|---|---|---|---|
| LRU (Least Recently Used) | Removes the least recently accessed item. | Keeps recently used data. | Recently accessed data might not be frequently needed. |
| LFU (Least Frequently Used) | Removes the least frequently accessed item. | Keeps frequently used data. | Less effective when access patterns change quickly. |
| FIFO (First In, First Out) | Removes the oldest inserted item. | Simple to implement. | Ignores how frequently or recently data is accessed. |
| Random | Removes a randomly selected item. | Simple and low overhead. | May remove frequently used data. |

## 5. Redis Eviction Policies

Redis supports several eviction policies:

- `noeviction`: Returns errors when memory is exceeded instead of removing keys.
- `allkeys-lru`: Removes the least recently used keys from all keys.
- `allkeys-lfu`: Removes the least frequently used keys from all keys.
- `allkeys-random`: Removes random keys from all keys.
- `volatile-lru`: Removes the least recently used keys among keys with an expiration time.
- `volatile-lfu`: Removes the least frequently used keys among keys with an expiration time.
- `volatile-random`: Removes random keys among keys with an expiration time.
- `volatile-ttl`: Removes keys with the shortest remaining TTL first.

**Note:** Redis does not provide FIFO as a built-in eviction policy.

## 6. Trade-offs and Choices in Our RAG Application

Our RAG application uses Redis for caching question retrieval results and generated answers.

We use a **cache-aside approach**:

1. When a user submits a question, the application generates a SHA-256 hash of the normalized question.
2. It checks Redis using the generated cache key.
3. If the question is already cached, the application retrieves the existing request ID and avoids repeating embedding generation and Qdrant retrieval.
4. If it is not cached, the application generates an embedding, searches Qdrant, and stores the retrieval results in Redis.
5. When generating an answer, the application checks whether an answer is already stored in Redis. If so, it returns the cached answer without calling the LLM again.

We use **TTL** to automatically expire cached records after a configured period, preventing old results from remaining indefinitely.

We do not need a write-through or write-behind strategy because Redis is used as a temporary cache rather than the primary database. Our original documents and vector embeddings are stored separately, while Redis stores reusable retrieval results and generated answers.

For eviction, an `allkeys-lru` policy is a reasonable choice because it removes less recently accessed keys when Redis reaches its memory limit, helping preserve recently used cached results.

**Conclusion:** Redis improves our RAG application's performance by reducing repeated vector searches and unnecessary LLM calls. This reduces response time, computational costs, and repeated processing.
