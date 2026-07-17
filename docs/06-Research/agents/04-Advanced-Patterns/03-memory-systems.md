# 🧠 Memory Systems in AI Agents — سیستم‌های حافظه در ایجنت‌های هوش مصنوعی

> **شماره مستند:** 03-memory-systems  
> **نسخه:** 1.0.0  
> **تاریخ:** 2026-07-16  
> **نویسنده:** HiveOS Research Team  
> **دسته:** Advanced Patterns — Agent Architecture

---

## 📋 فهرست مطالب

| # | بخش | توضیح |
|---|------|-------|
| 1 | [اهمیت حافظه — Why Memory Matters](#1-اهمیت-حافظه--why-memory-matters) | چرا ایجنت بدون حافظه ناقص است |
| 2 | [انواع حافظه — Types of Memory](#2-انواع-حافظه--types-of-memory) | STM, LTM, Episodic, Semantic, Procedural |
| 3 | [الگوهای پیاده‌سازی — Implementation Patterns](#3-الگوهای-پیاده‌سازی--implementation-patterns) | Dict, Vector DB, SQLite, RAG, Graph |
| 4 | [مدیریت حافظه — Memory Management](#4-مدیریت-حافظه--memory-management) | Retrieval, Consolidation, Forgetting |
| 5 | [حافظه در سیستم‌های چندعاملی — Multi-Agent Memory](#5-حافظه-در-سیستم‌های-چندعاملی--multi-agent-memory) | Bus, Agent-specific, Global KB |
| 6 | [مثال‌های عملی — Practical Code Examples](#6-مثال‌های-عملی--practical-code-examples) | LangGraph, OpenAI, Custom |
| 7 | [ارتباط با HiveOS — HiveOS Integration](#7-ارتباط-با-hiveos--hiveos-integration) | Brain, EventStream, DecisionTracer, StorageEngine |

---

## 1. اهمیت حافظه — Why Memory Matters

ایجنت‌های هوش مصنوعی بدون حافظه مانند **ماهی‌هایی با حافظه سه ثانیه** عمل می‌کنند. هر تعامل یک صفحه سفید است — هیچ چیز از گذشته یاد گرفته نمی‌شود، اشتباهات تکرار می‌شوند، و پیش‌زمینه‌ای برای تصمیم‌گیری وجود ندارد.

### 1.1 مشکلات ایجنت‌های بدون حافظه

```ascii
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Agent Without Memory (Stateless)                          │
│                                                             │
│   User: "My name is Alice"                                  │
│   Agent: "Hello Alice!"                                     │
│                                                             │
│   ──── 5 minutes later ────                                 │
│                                                             │
│   User: "What's my name?"                                   │
│   Agent: "I don't know. You never told me."                 │
│                                                             │
│   ❌ Context lost    ❌ Mistake repeated    ❌ No learning   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

سه مشکل اصلی ایجنت‌های **Stateless**:

| مشکل | توضیح | مثال |
|------|-------|------|
| **تکرار اشتباهات** | ایجنت نمی‌داند چه کاری قبلاً انجام شده | دوباره به همان API درخواست می‌فرستد |
| **از دست دادن بافت** | نمی‌تواند به مکالمات قبلی ارجاع دهد | نام کاربر، ترجیحات، تاریخچه را فراموش می‌کند |
| **عدم یادگیری** | هیچ بهبودی در طول زمان ندارد | همان اشتباه را بارها تکرار می‌کند |

### 1.2 حافظه چه چیزی را ممکن می‌کند

```ascii
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Agent With Memory (Stateful)                              │
│                                                             │
│   User: "My name is Alice"                                  │
│   Agent: "Hello Alice!"                                     │
│              │                                              │
│              ▼                                              │
│        ┌──────────┐                                         │
│        │  Memory  │  ← "user_123": {"name": "Alice"}        │
│        └──────────┘                                         │
│              │                                              │
│   ──── Next Day ────                                        │
│              │                                              │
│   User: "What's my name?"                                   │
│   Agent: "Your name is Alice! 👋"                           │
│                                                             │
│   ✅ Context preserved  ✅ Can learn patterns               │
│   ✅ Personalization    ✅ Continuous improvement           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| قابلیت | توضیح |
|--------|-------|
| **Context Preservation** | حفظ بافت مکالمه در طول زمان |
| **Personalization** | تطبیق با ترجیحات و نیازهای کاربر |
| **Error Recovery** | یادگیری از اشتباهات گذشته |
| **Knowledge Accumulation** | انباشت تدریجی دانش |
| **Behavioral Adaptation** | تطبیق رفتار بر اساس تجربیات گذشته |

---

## 2. انواع حافظه — Types of Memory

حافظه در ایجنت‌های AI از **پنج نوع اصلی** تشکیل شده که هر کدام نقش متفاوتی دارند. این تقسیم‌بندی از علوم شناختی (Cognitive Science) الهام گرفته شده است.

```ascii
                         ┌──────────────────┐
                         │   MEMORY SYSTEM  │
                         │   سیستم حافظه    │
                         └────────┬─────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │  Short-Term    │  │  Long-Term     │  │  Working       │
     │  کوتاه‌مدت     │  │  بلندمدت       │  │  فعال          │
     └────────────────┘  └───────┬────────┘  └────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │   Episodic     │  │   Semantic     │  │   Procedural   │
     │   رویدادی      │  │   معنایی       │  │   رویه‌ای      │
     └────────────────┘  └────────────────┘  └────────────────┘
```

### 2.1 جدول مقایسه انواع حافظه

| نوع | مدت | ظرفیت | persistence | کاربرد اصلی |
|-----|------|-------|-------------|-------------|
| **Short-Term (STM)** | چند ثانیه تا چند دقیقه | محدود (Context Window) | ❌ موقتی | گفتگوی جاری |
| **Working Memory** | طول یک Task | Task-dependent | ❌ موقتی | پردازش فعال |
| **Long-Term (LTM)** | روزها تا سال‌ها | نامحدود | ✅ ماندگار | دانش بلندمدت |
| **Episodic** | نامحدود | بالا | ✅ ماندگار | تجربیات گذشته |
| **Semantic** | نامحدود | بسیار بالا | ✅ ماندگار | دانش عمومی |
| **Procedural** | دائمی | محدود | ✅ ماندگار | مهارت‌ها |

### 2.2 Short-Term Memory (STM) — حافظه کوتاه‌مدت

حافظه کوتاه‌مدت معادل **Context Window** مدل‌های زبانی است. این همان فضایی است که پرامپت فعلی، تاریخچه اخیر، و وضعیت موقت را نگه می‌دارد.

**ویژگی‌ها:**

- **Ephemeral:** با پایان هر session پاک می‌شود
- **ظرفیت محدود:** توسط token limit مدل محدود شده (معمولاً 4K تا 200K توکن)
- **FIFO:** قدیمی‌ترین محتوا حذف می‌شود
- **سرعت بالا:** دسترسی فوری بدون I/O

```python
# نمونه: حافظه کوتاه‌مدت با Queue
from collections import deque

class ShortTermMemory:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.messages: deque = deque()
        self.current_tokens = 0
    
    def add(self, message: dict, token_count: int) -> None:
        while self.current_tokens + token_count > self.max_tokens:
            removed = self.messages.popleft()
            self.current_tokens -= removed.get("tokens", 0)
        self.messages.append(message)
        self.current_tokens += token_count
    
    def get_context(self) -> list:
        return list(self.messages)
```

### 2.3 Long-Term Memory (LTM) — حافظه بلندمدت

حافظه بلندمدت **دائمی** است و در یک Storage backend ذخیره می‌شود. ایجنت می‌تواند روزها بعد اطلاعات را بازیابی کند.

| ویژگی | توضیح |
|--------|-------|
| **Persistence** | روی دیسک / دیتابیس ذخیره می‌شود |
| **Indexing** | با ID, embedding, یا کلید索引 می‌شود |
| **Retrieval** | نیاز به جستجو دارد (Query) |
| **Capacity** | عملاً نامحدود |

### 2.4 Episodic Memory — حافظه رویدادی

حافظه **تجربیات خاص** را ثبت می‌کند: چه اتفاقی افتاد، چه زمانی، چه نتیجه‌ای داشت.

```python
episodic_memory = [
    {
        "episode_id": "ep-001",
        "timestamp": "2026-07-15T10:30:00Z",
        "agent": "workflow-orchestrator",
        "action": "task_routing",
        "input": {"task": "data_processing", "target": "node-alpha"},
        "outcome": "success",
        "latency_ms": 230,
        "reflection": "Node-alpha was fast. Prefer for data tasks."
    },
    {
        "episode_id": "ep-002",
        "timestamp": "2026-07-15T11:00:00Z",
        "agent": "workflow-orchestrator",
        "action": "task_routing",
        "input": {"task": "data_processing", "target": "node-beta"},
        "outcome": "failure",
        "error": "timeout",
        "reflection": "Node-beta is unreliable for large data."
    }
]
```

### 2.5 Semantic Memory — حافظه معنایی

دانش **تعمیم‌یافته** و **واقعی** — برخلاف episodic که خاص یک رویداد است. شامل مفاهیم، روابط، و قوانین.

| Episodic | Semantic |
|----------|----------|
| "دیروز API پرداخت ۵۰۰ms تأخیر داشت" | "API پرداخت معمولاً ۲۰۰-۳۰۰ms تأخیر دارد" |
| خاص (Specific) | عمومی (General) |
| وابسته به زمان | بی‌زمان |
| روایت (Narrative) | دانش (Knowledge) |

### 2.6 Procedural Memory — حافظه رویه‌ای

نحوه انجام کارها — **مهارت‌ها و رویه‌ها**. این حافظه مشخص می‌کند ایجنت چگونه از ابزارها استفاده کند، workflows را اجرا کند، و با خطاها برخورد کند.

```python
procedural_memory = {
    "retry_strategy": {
        "name": "Exponential Backoff",
        "steps": [
            "1. Wait 2^attempt seconds",
            "2. On 429/503: retry up to 3 times",
            "3. On 4xx (non-retryable): fail immediately",
            "4. Log each retry attempt"
        ],
        "applicable_to": ["http_requests", "api_calls"]
    },
    "error_classification": {
        "patterns": {
            "timeout": {"action": "retry_with_longer_timeout"},
            "rate_limit": {"action": "backoff_and_retry"},
            "auth_error": {"action": "renew_credentials"}
        }
    }
}
```

---

## 3. الگوهای پیاده‌سازی — Implementation Patterns

پنج الگوی اصلی برای پیاده‌سازی حافظه در ایجنت‌های AI وجود دارد:

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY IMPLEMENTATIONS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  In-Memory Dict         ════  ساده‌ترین — فقط برای پروتوتایپ    │
│  ┌─────────┐ ┌──────┐                                            │
│  │ user_1  │ │{...} │                                            │
│  │ user_2  │ │{...} │                                            │
│  └─────────┘ └──────┘                                            │
│                                                                  │
│  Vector DB (Chroma)     ════  Semantic search — RAG              │
│  ┌─────────────────────┐                                         │
│  │[0.23, 0.87, ...]───┤  embedding → поиск по смыслу            │
│  └─────────────────────┘                                         │
│                                                                  │
│  SQLite                 ════  Structured + reliable              │
│  ┌─────────────────────┐                                         │
│  │ id │ ns │ key │ val │  ← transactional, zero-config          │
│  └─────────────────────┘                                         │
│                                                                  │
│  RAG Pipeline           ════  LLM + external knowledge           │
│  ┌──────┐  ┌────────┐  ┌──────┐                                  │
│  │Query │→│ Retrieve│→│Generate│                                 │
│  └──────┘  └────────┘  └──────┘                                  │
│                                                                  │
│  Knowledge Graph       ════  Relational memory                   │
│  [Alice]───knows───[Bob]                                         │
│     │                  │                                         │
│  works_at           works_at                                     │
│     │                  │                                         │
│  [Acme Corp]──────┐   │                                          │
│                   │   │                                          │
│             [Project X]                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 In-Memory Dict — حافظه درون‌حافظه‌ای

ساده‌ترین شکل حافظه. مناسب برای **پروتوتایپ** و **single-session** اما با ری‌استارت همه چیز پاک می‌شود.

| مزایا | معایب |
|-------|-------|
| سرعت بالا (RAM) | ❌ از بین رفتن با ری‌استارت |
| بدون وابستگی (No dependencies) | ❌ مقیاس‌پذیری محدود |
| API ساده | ❌ بدون جستجوی معنایی |

```python
class InMemoryStore:
    """In-memory key-value store — simplest memory."""
    def __init__(self):
        self._store: dict[str, dict] = {}
    
    def save(self, key: str, data: dict) -> None:
        self._store[key] = data
    
    def load(self, key: str) -> dict | None:
        return self._store.get(key)
    
    def search(self, query: str) -> list[dict]:
        # Naive keyword search
        results = []
        for key, data in self._store.items():
            if query.lower() in str(data).lower():
                results.append({"key": key, "data": data})
        return results
    
    def clear(self) -> None:
        self._store.clear()
```

### 3.2 Vector DB — پایگاه داده برداری

مهمترین تکنولوژی برای **Semantic Memory** و **RAG**. هر قطعه حافظه به یک embedding تبدیل می‌شود و بر اساس شباهت معنایی جستجو می‌شود.

| ابزار | زبان | ویژگی خاص |
|-------|------|-----------|
| **Chroma** | Python | سبک، embedded، بدون سرور |
| **Pinecone** | REST | مدیریت‌شده، مقیاس‌پذیر |
| **Weaviate** | GraphQL | Hybrid (برداری + کلاسیک) |
| **Qdrant** | Rust | سریع، فیلتر غنی |
| **Milvus** | Go/C++ | مقیاس عظیم، توزیع‌شده |

```python
# Chroma — lightweight embedded vector store
import chromadb
from chromadb.utils import embedding_functions

class VectorMemory:
    def __init__(self, collection_name: str = "agent_memory"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
    
    def remember(self, text: str, metadata: dict = None) -> str:
        """Store a memory with its vector embedding."""
        mem_id = f"mem-{hash(text)}"
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[mem_id]
        )
        return mem_id
    
    def recall(self, query: str, top_k: int = 5) -> list[dict]:
        """Find semantically similar memories."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return [
            {"text": doc, "score": dist, "metadata": meta}
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            )
        ]
```

### 3.3 SQLite — حافظه رابطه‌ای

SQLite بهترین انتخاب برای **Structured Memory** است: نصب نمی‌خواهد، transactional است، و schema دارد. HiveOS StorageEngine دقیقاً از همین الگو استفاده می‌کند.

```python
import sqlite3
import json
from datetime import datetime

class SQLiteMemory:
    """SQLite-backed persistent memory — structured & reliable."""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()
    
    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id          TEXT PRIMARY KEY,
                namespace   TEXT NOT NULL,
                key         TEXT NOT NULL,
                value       TEXT NOT NULL,  -- JSON
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                UNIQUE(namespace, key)
            );
            CREATE INDEX IF NOT EXISTS idx_mem_namespace 
                ON memories(namespace);
        """)
        self.conn.commit()
    
    def upsert(self, namespace: str, key: str, data: dict) -> None:
        now = datetime.utcnow().isoformat()
        raw = json.dumps(data, ensure_ascii=False)
        self.conn.execute("""
            INSERT INTO memories (id, namespace, key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT created_at FROM memories WHERE namespace=? AND key=?), ?
            ), ?)
            ON CONFLICT(id) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (f"{namespace}:{key}", namespace, key, raw, namespace, key, now, now))
        self.conn.commit()
    
    def load(self, namespace: str, key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT value FROM memories WHERE namespace=? AND key=?",
            (namespace, key)
        ).fetchone()
        return json.loads(row[0]) if row else None
    
    def search(self, namespace: str, keyword: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT key, value FROM memories WHERE namespace=? AND value LIKE ?",
            (namespace, f"%{keyword}%")
        ).fetchall()
        return [{"key": r[0], "data": json.loads(r[1])} for r in rows]
```

### 3.4 RAG-Based Retrieval — بازیابی مبتنی بر RAG

**Retrieval-Augmented Generation** قلب حافظه معنایی در ایجنت‌های مدرن است. ایجنت ابتدا حافظه مرتبط را بازیابی می‌کند، سپس پاسخ را تولید می‌کند.

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                               │
│                                                                  │
│  User Query                                                     │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────┐     ┌──────────────┐                              │
│  │ Embed   │────→│  Vector DB   │                              │
│  │ Query   │     │  Search      │                              │
│  └─────────┘     └──────┬───────┘                              │
│                         │ top-k chunks                          │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────┐                │
│  │         Prompt Construction                  │                │
│  │  System: You are a helpful assistant         │                │
│  │  Context: [retrieved chunks]                 │                │
│  │  Query: [user query]                         │                │
│  └─────────────────────┬───────────────────────┘                │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────┐                │
│  │            LLM Generation                    │                │
│  └─────────────────────┬───────────────────────┘                │
│                        │                                        │
│                        ▼                                        │
│  Final Response to User                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```python
class RAGMemory:
    """RAG-based memory — retrieve relevant context before generation."""
    
    def __init__(self, vector_store, llm):
        self.vs = vector_store
        self.llm = llm
    
    def answer_with_memory(self, query: str) -> str:
        # 1. Retrieve relevant memories
        memories = self.vs.recall(query, top_k=3)
        
        # 2. Build context
        context = "\n\n".join([
            f"[Memory {i+1}] {m['text']}"
            for i, m in enumerate(memories)
        ])
        
        # 3. Augment prompt
        prompt = f"""You are an AI assistant with memory.
Previous relevant memories:
{context}

Current question: {query}

Answer based on your knowledge and the memories above."""
        
        # 4. Generate
        return self.llm.generate(prompt)
```

### 3.5 Graph-Based Memory — حافظه گرافی

حافظه به صورت **گره‌ها** (entities) و **یال‌ها** (relationships) ذخیره می‌شود. بهترین گزینه برای حافظه **Semantic** وقتی روابط بین مفاهیم اهمیت دارند.

```python
# ساده‌سازی: حافظه گرافی با دیکشنری مجاورت
class GraphMemory:
    """Simple graph-based memory — entities + relationships."""
    
    def __init__(self):
        self.nodes: dict[str, dict] = {}      # node_id → attributes
        self.edges: list[tuple] = []           # (source, relation, target)
    
    def add_entity(self, entity_id: str, attributes: dict) -> None:
        self.nodes[entity_id] = attributes
    
    def add_relation(self, source: str, relation: str, target: str) -> None:
        self.edges.append((source, relation, target))
    
    def query(self, entity_id: str, depth: int = 1) -> dict:
        """Get an entity and its immediate relations."""
        result = {"entity": self.nodes.get(entity_id), "relations": []}
        for s, r, t in self.edges:
            if s == entity_id:
                result["relations"].append({
                    "relation": r,
                    "target": t,
                    "target_data": self.nodes.get(t)
                })
            elif t == entity_id:
                result["relations"].append({
                    "relation": f"{r} (inverse)",
                    "source": s,
                    "source_data": self.nodes.get(s)
                })
        return result
```

### 3.6 مقایسه الگوها

| معیار | In-Memory | Vector DB | SQLite | RAG | Graph |
|-------|-----------|-----------|--------|-----|-------|
| **پایداری** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **جستجوی معنایی** | ❌ | ✅ | ❌ | ✅ | ⚠️ محدود |
| **جستجوی ساختاری** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **سرعت** | ⚡ فوق‌سریع | 🟢 سریع | 🟢 سریع | 🟡 متوسط | 🟡 متوسط |
| **پیچیدگی** | ★☆☆ | ★★☆ | ★★☆ | ★★★ | ★★★ |
| **کاربرد اصلی** | پروتوتایپ | Semantic Mem | Structured Mem | Long-term | Knowledge Graph |

---

## 4. مدیریت حافظه — Memory Management

داشتن حافظه کافی نیست — باید **مدیریت** شود: چطور بازیابی کنیم، چطور consolidate کنیم، و چطور فراموش کنیم.

### 4.1 Retrieval Strategies — استراتژی‌های بازیابی

```ascii
                    ┌──────────────┐
                    │  QUERY       │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │  Top-K     │ │    MMR     │ │  Reranking │
     │  ساده     │ │  متنوع     │ │  هوشمند   │
     └────────────┘ └────────────┘ └────────────┘
```

#### Top-K Retrieval

ساده‌ترین روش: `k` نتیجه با بیشترین امتیاز شباهت را برمی‌گرداند.

```python
def top_k_retrieval(query_emb: list[float], 
                    memory_embeddings: list[tuple], 
                    k: int = 5) -> list[dict]:
    """Return top-k most similar memories."""
    scores = []
    for mem_id, mem_emb in memory_embeddings:
        similarity = cosine_similarity(query_emb, mem_emb)
        scores.append((similarity, mem_id))
    scores.sort(reverse=True)
    return [{"id": mid, "score": s} for s, mid in scores[:k]]
```

#### MMR (Maximum Marginal Relevance)

تعادلی بین **شباهت** و **تنوع** ایجاد می‌کند — نتایج تکراری را حذف می‌کند.

```python
def mmr_retrieval(query_emb, candidates, k=5, lambda_param=0.7):
    """
    λ=1.0 → pure relevance (like top-k)
    λ=0.0 → pure diversity
    
    score = λ · sim(query, doc) − (1−λ) · max(sim(doc, selected))
    """
    selected = []
    remaining = list(candidates)
    
    for _ in range(k):
        mmr_scores = []
        for doc in remaining:
            relevance = cosine_similarity(query_emb, doc["embedding"])
            if selected:
                max_sim_to_sel = max(
                    cosine_similarity(doc["embedding"], s["embedding"])
                    for s in selected
                )
            else:
                max_sim_to_sel = 0
            mmr = lambda_param * relevance - (1 - lambda_param) * max_sim_to_sel
            mmr_scores.append((mmr, doc))
        
        mmr_scores.sort(reverse=True)
        best = mmr_scores[0][1]
        selected.append(best)
        remaining.remove(best)
    
    return selected
```

#### Reranking

یک مدل رتبه‌بندی قوی‌تر نتایج اولیه را **دوباره مرتب** می‌کند:

| مرحله | توضیح | تکنولوژی |
|-------|-------|-----------|
| 1. Initial Retrieval | بازیابی سریع با embedding | Chroma, FAISS |
| 2. Reranking | ارزیابی دقیق‌تر | Cross-encoder (e.g. Cohere Rerank) |
| 3. Final Selection | انتخاب top-k پس از رتبه‌بندی | Threshold + count |

### 4.2 Memory Consolidation — تثبیت حافظه

تبدیل **حافظه کوتاه‌مدت به بلندمدت** — فرایندی شبیه مغز انسان.

```ascii
Time ────────────────────────────────────────────────────────────►

STM (Ephemeral)           Consolidation           LTM (Persistent)
┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│  Recent      │         │  Extract     │        │  Stored      │
│  Interactions│ ──────► │  Summarize   │ ─────► │  Knowledge   │
│  Raw Events  │         │  Deduplicate │        │  Patterns    │
└──────────────┘         └──────────────┘        └──────────────┘
```

```python
class MemoryConsolidator:
    """Convert short-term memories into long-term knowledge."""
    
    def __init__(self, stm, ltm, llm):
        self.stm = stm   # Short-term (context / recent)
        self.ltm = ltm   # Long-term vector store
        self.llm = llm    # For summarization
    
    def consolidate(self, batch_size: int = 10) -> list[str]:
        """Extract important patterns from recent memories."""
        recent = self.stm.get_recent(batch_size)
        if not recent:
            return []
        
        # Ask LLM to distill key information
        text = "\n".join([m["content"] for m in recent])
        summary = self.llm.generate(
            f"Extract key facts from these interactions:\n{text}\n\n"
            "Return as bullet points of factual knowledge."
        )
        
        # Store in LTM
        ids = []
        for fact in summary.split("\n"):
            if fact.strip():
                fid = self.ltm.remember(fact, {"type": "consolidated"})
                ids.append(fid)
        
        return ids
```

### 4.3 Forgetting Mechanisms — مکانیسم‌های فراموشی

فراموشی یک **ویژگی** است، نه یک باگ. بدون فراموشی، حافظه از اطلاعات کهنه و بی‌ربط پر می‌شود.

| استراتژی | توضیح | پیاده‌سازی |
|----------|-------|-------------|
| **Time-based** | حذف پس از مدت مشخص | TTL on records |
| **Capacity-based** | حذف قدیمی‌ترین هنگام پر شدن | FIFO / LRU cache |
| **Importance-based** | حذف کم‌اهمیت‌ترین‌ها | Score threshold |
| **Decay** | کاهش تدریجی امتیاز relevance | Exponential decay |
| **Active Forgetting** | حذف با تشخیص LLM | Agent decides to forget |

```python
import time

class DecayingMemory:
    """Memory with time-based decay — older memories fade."""
    
    def __init__(self, decay_hours: float = 24.0):
        self.memories: list[dict] = []
        self.decay_seconds = decay_hours * 3600
    
    def add(self, content: str, importance: float = 1.0) -> None:
        self.memories.append({
            "content": content,
            "importance": importance,
            "created_at": time.time(),
        })
    
    def recall(self, threshold: float = 0.3) -> list[dict]:
        """Return memories above relevance threshold."""
        now = time.time()
        active = []
        for mem in self.memories:
            age = now - mem["created_at"]
            decay_factor = exp(-age / self.decay_seconds)
            relevance = mem["importance"] * decay_factor
            if relevance >= threshold:
                active.append({**mem, "relevance": relevance})
        return sorted(active, key=lambda x: x["relevance"], reverse=True)
    
    def forget_old(self, max_age_hours: float = 168) -> int:
        """Explicitly remove memories older than max_age."""
        cutoff = time.time() - (max_age_hours * 3600)
        before = len(self.memories)
        self.memories = [
            m for m in self.memories
            if m["created_at"] > cutoff
        ]
        return before - len(self.memories)
```

---

## 5. حافظه در سیستم‌های چندعاملی — Multi-Agent Memory

در سیستم‌های **Multi-Agent System (MAS)** مثل HiveOS، حافظه به سه سطح تقسیم می‌شود:

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT MEMORY ARCHITECTURE               │
│                                                                  │
│                    ┌──────────────────────┐                      │
│                    │  Global Knowledge    │                      │
│                    │  Base (Shared)       │                      │
│                    │  ↑ read / ↓ write    │                      │
│                    └──────────┬───────────┘                      │
│                               │                                  │
│                    ┌──────────┴───────────┐                      │
│                    │   Memory Bus (Event   │                      │
│                    │   Stream + Messages)  │                      │
│                    └────┬──────┬──────┬───┘                      │
│                         │      │      │                          │
│              ┌──────────┘      │      └──────────┐               │
│              ▼                 ▼                  ▼               │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│     │  Agent A     │  │  Agent B     │  │  Agent C     │        │
│     │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │        │
│     │  │Private │  │  │  │Private │  │  │  │Private │  │        │
│     │  │Memory  │  │  │  │Memory  │  │  │  │Memory  │  │        │
│     │  └────────┘  │  │  └────────┘  │  │  └────────┘  │        │
│     └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.1 Agent-Specific Memory — حافظه اختصاصی ایجنت

هر ایجنت **حافظه خصوصی** خود را دارد — context مکالمه، preferences، و تجربیات شخصی.

```python
class AgentMemory:
    """Private memory for a single agent."""
    
    def __init__(self, agent_id: str, storage_engine):
        self.agent_id = agent_id
        self.namespace = f"agent:{agent_id}"
        self.storage = storage_engine
        self.working_memory: list[dict] = []  # STM
    
    def remember_interaction(self, user_input: str, agent_response: str):
        # Short-term
        self.working_memory.append({
            "input": user_input,
            "output": agent_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Persist to long-term
        self.storage.upsert(
            self.namespace,
            f"interaction:{len(self.working_memory)}",
            self.working_memory[-1]
        )
```

### 5.2 Shared Memory Bus — حافظه اشتراکی از طریق Bus

در HiveOS، **CommunicationBus** نقش حافظه اشتراکی را بازی می‌کند. ایجنت‌ها از طریق پیام‌ها (Messages) دانش را به اشتراک می‌گذارند.

```python
# HiveOS CommunicationBus → Shared Memory Bus
from hiveos.mothership.communication_bus import (
    CommunicationBus, MessageType, Message
)

class SharedMemoryBus:
    """Extends CommunicationBus with memory features."""
    
    def __init__(self, bus: CommunicationBus, storage_engine):
        self.bus = bus
        self.storage = storage_engine
        self.namespace = "shared:knowledge"
    
    def share_knowledge(self, sender: str, topic: str, content: dict):
        """Publish knowledge to all agents."""
        message = self.bus.publish(
            msg_type=MessageType.KNOWLEDGE_UPDATE,
            payload={"topic": topic, "content": content},
            recipient=None,  # broadcast
        )
        # Also persist to shared store
        key = f"{topic}:{message.timestamp}"
        self.storage.upsert(self.namespace, key, {
            "sender": sender,
            "topic": topic,
            "content": content,
            "timestamp": message.timestamp,
        })
        return message
    
    def query_shared_knowledge(self, topic: str) -> list[dict]:
        """Query all shared knowledge on a topic."""
        return self.storage.load_all_with_keys(self.namespace)
```

### 5.3 Global Knowledge Base — پایگاه دانش سراسری

شامل **مشترکات همه ایجنت‌ها**: قوانین کسب‌وکار، دانش دامنه، تنظیمات سراسری.

| ویژگی | توضیح |
|-------|-------|
| **Read Replication** | همه ایجنت‌ها می‌توانند بخوانند |
| **Write Authorization** | فقط ایجنت‌های مجاز می‌توانند بنویسند |
| **Versioning** | هر تغییر نسخه‌بندی می‌شود |
| **Conflict Resolution** | Last-write-wins یا Merge |

### 5.4 Memory Synchronization Patterns

```ascii
Eventual Consistency Model:

Agent A          Memory Bus          Agent B          Agent C
  │                   │                 │                 │
  │──[write: fact]───►│                 │                 │
  │                   │───[sync]───────►│                 │
  │                   │───[sync]─────────────────────────►│
  │                   │                 │                 │
  │       ┌───────────┴──────┐          │                 │
  │       │ Queue + Retry    │          │                 │
  │       │ TTL check        │          │                 │
  │       │ Deduplication    │          │                 │
  │       └──────────────────┘          │                 │
  │                                     │                 │
  │◄────[ACK]────────────────────────────│                 │
  │◄────[ACK]─────────────────────────────────────────────│
```

---

## 6. مثال‌های عملی — Practical Code Examples

### 6.1 LangGraph Memory — حافظه در LangGraph

LangGraph از **Checkpointer** برای حفظ state بین اجراها استفاده می‌کند:

```python
from langgraph.graph import StateGraph, State
from langgraph.checkpoint import MemorySaver
from typing import TypedDict, List

# Define state with memory
class AgentState(TypedDict):
    messages: List[dict]
    context: dict
    memory: List[dict]  # Long-term memory store

# Memory saver — saves state between runs
memory_checkpointer = MemorySaver()

def agent_node(state: AgentState) -> AgentState:
    """Agent node that uses memory."""
    messages = state["messages"]
    memory = state["memory"]
    
    # Retrieve relevant memories
    recent_memories = memory[-5:]  # Last 5 memories
    
    # Build prompt with memory context
    prompt = f"""
    Previous memories: {recent_memories}
    Current message: {messages[-1]}
    Respond considering past context.
    """
    
    # ... LLM call ...
    
    # Update memory with new insight
    new_memory = "User prefers concise answers"
    updated_memory = [*memory, new_memory]
    
    return {
        **state,
        "messages": [*messages, {"role": "assistant", "content": response}],
        "memory": updated_memory,
    }

# Build the graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")

# Compile with memory checkpointing
app = graph.compile(checkpointer=memory_checkpointer)

# Run — state persists via checkpointer
config = {"configurable": {"thread_id": "conversation-1"}}
result = app.invoke({
    "messages": [{"role": "user", "content": "Hi, I'm Alice"}],
    "context": {},
    "memory": [],
}, config)
```

### 6.2 OpenAI Assistants Vector Store — فروشگاه برداری

OpenAI Assistants API حافظه داخلی از طریق **Vector Store** فراهم می‌کند:

```python
from openai import OpenAI

client = OpenAI()

# 1. Create a vector store for the agent's memory
vector_store = client.vector_stores.create(
    name="agent_memory_store"
)

# 2. Upload knowledge documents
file = client.files.create(
    file=open("knowledge_base.txt", "rb"),
    purpose="assistants"
)

# 3. Add file to vector store
client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id=file.id
)

# 4. Create assistant with vector store
assistant = client.beta.assistants.create(
    name="Memory-Enabled Agent",
    instructions="You have long-term memory via vector store.",
    model="gpt-4o",
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [vector_store.id]
        }
    }
)

# 5. Conversation with automatic memory retrieval
thread = client.beta.threads.create()

client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What do we know about the user's preferences?"
)

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)
# Assistant automatically searches vector store for context
```

### 6.3 Custom Memory Implementation — پیاده‌سازی سفارشی

یک سیستم حافظه کامل با **سه لایه**: Working Memory, Episodic Buffer, Long-term Store.

```python
"""
custom_memory.py — Three-tier agent memory system.
Tiers: Working (ephemeral) → Buffer (recent) → Store (permanent)
"""

import json
import time
import sqlite3
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

# ─── Data Structures ─────────────────────────────────────────

@dataclass
class MemoryEntry:
    content: str
    memory_type: str  # working | episodic | semantic
    importance: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = field(default_factory=list)
    access_count: int = 0
    embedding: Optional[list[float]] = None


@dataclass
class RecallResult:
    entries: list[MemoryEntry]
    query: str
    latency_ms: float
    strategy: str

# ─── Three-Tier Memory ───────────────────────────────────────

class TieredMemory:
    """Complete three-tier memory system."""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        # Tier 1: Working Memory (in-memory, fastest)
        self.working: list[MemoryEntry] = []
        self._working_limit = 50
        
        # Tier 2: Episodic Buffer (recent persisted events)
        self._buffer_limit = 500
        
        # Tier 3: Long-term Store (SQLite)
        self._conn = sqlite3.connect(db_path)
        self._init_store()
    
    def _init_store(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                timestamp TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                access_count INTEGER DEFAULT 0
            )
        """)
        self._conn.commit()
    
    def store(self, entry: MemoryEntry) -> str:
        """Store in appropriate tier based on importance."""
        entry.access_count = 0
        
        # Always add to working memory
        self.working.append(entry)
        if len(self.working) > self._working_limit:
            # Move oldest to episodic buffer
            oldest = self.working.pop(0)
            self._store_episodic(oldest)
        
        # If high importance, store directly in LTM
        if entry.importance > 0.7:
            self._store_ltm(entry)
        
        return entry.timestamp
    
    def _store_episodic(self, entry: MemoryEntry):
        """Store in episodic buffer (Tier 2)."""
        self._store_ltm(entry, mem_type="episodic")
    
    def _store_ltm(self, entry: MemoryEntry, mem_type: str = None):
        """Store in long-term SQLite store."""
        self._conn.execute(
            "INSERT INTO long_term_memory (content, memory_type, importance, timestamp, tags) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                entry.content,
                mem_type or entry.memory_type,
                entry.importance,
                entry.timestamp,
                json.dumps(entry.tags),
            )
        )
        self._conn.commit()
    
    def recall(self, query: str, limit: int = 10) -> RecallResult:
        """Search across all tiers."""
        start = time.perf_counter()
        results = []
        
        # 1. Search working memory (keyword)
        for mem in self.working:
            if query.lower() in mem.content.lower():
                results.append(mem)
                mem.access_count += 1
        
        # 2. Search LTM (SQL LIKE)
        rows = self._conn.execute(
            """SELECT content, memory_type, importance, timestamp, tags, access_count
               FROM long_term_memory
               WHERE content LIKE ?
               ORDER BY importance DESC, access_count DESC
               LIMIT ?""",
            (f"%{query}%", limit - len(results))
        ).fetchall()
        
        for row in rows:
            results.append(MemoryEntry(
                content=row[0],
                memory_type=row[1],
                importance=row[2],
                timestamp=row[3],
                tags=json.loads(row[4]),
                access_count=row[5] + 1,
            ))
        
        latency = (time.perf_counter() - start) * 1000
        
        return RecallResult(
            entries=results[:limit],
            query=query,
            latency_ms=round(latency, 2),
            strategy="tiered_search",
        )
    
    def get_stats(self) -> dict:
        """Memory system statistics."""
        ltm_count = self._conn.execute(
            "SELECT COUNT(*) FROM long_term_memory"
        ).fetchone()[0]
        return {
            "working_memory_size": len(self.working),
            "long_term_store_size": ltm_count,
            "total": len(self.working) + ltm_count,
        }

# ─── Usage Example ────────────────────────────────────────────

if __name__ == "__main__":
    mem = TieredMemory()
    
    # Store memories
    mem.store(MemoryEntry(
        content="User Alice prefers dark mode in dashboard",
        memory_type="semantic",
        importance=0.8,
        tags=["user_preference", "alice"],
    ))
    
    mem.store(MemoryEntry(
        content="Database migration failed due to timeout",
        memory_type="episodic",
        importance=0.6,
        tags=["error", "database", "migration"],
    ))
    
    # Recall
    result = mem.recall("database")
    print(f"Found {len(result.entries)} memories in {result.latency_ms}ms")
    for e in result.entries:
        print(f"  [{e.memory_type}] {e.content} (importance: {e.importance})")
    
    # Stats
    print(f"System stats: {mem.get_stats()}")
```

---

## 7. ارتباط با HiveOS — HiveOS Integration

حافظه در HiveOS از طریق سه مؤلفه اصلی پیاده‌سازی شده است:

### 7.1 HiveOS Brain Architecture

```ascii
┌─────────────────────────────────────────────────────────────────┐
│                    HIVEOS BRAIN (🧠 v0.8+)                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EventStream                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Agent    │  │ Task     │  │ Flow     │  │ System   │ │   │
│  │  │ Lifecycle│  │ Events   │  │ Events   │  │ Events   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   DecisionTracer                         │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Trace: flow-20260716-001                          │  │   │
│  │  │  ├── Step 1: Route task to Agent-A (reason: load)  │  │   │
│  │  │  ├── Step 2: Agent-A processes (result: success)   │  │   │
│  │  │  └── Step 3: Aggregate results (outcome: complete)  │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    StorageEngine                         │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  SQLite (WAL mode, thread-safe)                    │  │   │
│  │  │  ┌────────────────────────────────────────────┐    │  │   │
│  │  │  │ kv_store (namespace TEXT, key TEXT, val)   │    │  │   │
│  │  │  │ ─ brain:events     → all event history    │    │  │   │
│  │  │  │ ─ brain:traces     → decision traces      │    │  │   │
│  │  │  │ ─ agent:*          → per-agent memory     │    │  │   │
│  │  │  │ ─ shared:knowledge → global memory        │    │  │   │
│  │  │  └────────────────────────────────────────────┘    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 EventStream — رخدادگان (Episodic Memory)

**EventStream** معادل **Episodic Memory** در HiveOS است. هر رویداد lifecycle یک ایجنت ثبت می‌شود:

```python
from hiveos.brain.event_stream import EventStream
from hiveos.storage.engine import StorageEngine

# Initialize with persistence
storage = StorageEngine("hiveos.db")
event_stream = EventStream(maxlen=10_000, storage=storage)

# Emit memory events
event_stream.emit(
    event_type="agent:memory_write",
    source="agent-01",
    payload={
        "memory_type": "episodic",
        "content": "Completed data pipeline task-42",
        "result": "success",
        "latency_ms": 1200,
    }
)

event_stream.emit(
    event_type="agent:memory_read",
    source="agent-01",
    payload={
        "query": "pipeline patterns",
        "results_found": 3,
        "strategy": "vector_semantic",
    }
)

# Query memory history
recent_events = event_stream.get_events(
    limit=10,
    event_type="agent:memory_write"
)

# Memory stats
stats = event_stream.stats()
```

### 7.3 DecisionTracer — ردیاب تصمیمات (Procedural Memory)

**DecisionTracer** فرایندهای تصمیم‌گیری را به صورت **step-by-step** ثبت می‌کند — این معادل **Procedural Memory** است:

```python
from hiveos.brain.decision_tracer import DecisionTracer

tracer = DecisionTracer(storage=storage)

# Trace a memory-related decision
trace_id = tracer.start_trace(context={
    "agent": "memory-consolidator",
    "action": "consolidation_run",
    "trigger": "working_memory_full",
})

tracer.add_step(trace_id, {
    "action": "evaluate_working_memory",
    "reasoning": "Working memory has 45/50 entries. Evaluating importance.",
    "result": "Found 12 entries with importance > 0.7 for LTM promotion",
})

tracer.add_step(trace_id, {
    "action": "select_consolidation_candidates",
    "reasoning": "Entries below 0.3 importance will be pruned.",
    "result": "12 to promote, 8 to prune, 25 to keep in buffer",
})

tracer.complete_trace(
    trace_id,
    outcome="success",
    summary="Consolidated 12 entries to LTM, pruned 8 low-importance entries",
)
```

### 7.4 StorageEngine — موتور ذخیره‌سازی (LTM Foundation)

**StorageEngine** لایه‌ای است که تمام حافظه دائمی HiveOS روی آن استوار است:

```python
from hiveos.storage.engine import StorageEngine

# Initialize
engine = StorageEngine("hiveos.db")

# Memory namespaces in HiveOS
MEMORY_NAMESPACES = {
    "brain:events":     "Episodic event history",
    "brain:traces":     "Decision trace records",
    "agent:*":          "Per-agent private memories",
    "shared:knowledge": "Global shared knowledge base",
    "learning:insights":"Learned patterns and analytics",
    "audit:trail":      "Audit trail for compliance",
}

def get_agent_memory(agent_id: str) -> dict:
    """Get all memories for a specific agent."""
    namespace = f"agent:{agent_id}"
    return engine.load_all_with_keys(namespace)

def search_across_agents(query: str) -> list[dict]:
    """Cross-agent memory search."""
    results = []
    # This would be enhanced with vector search in production
    for ns in ["brain:events", "shared:knowledge"]:
        all_records = engine.load_all(ns)
        for record in all_records:
            if query.lower() in str(record).lower():
                results.append({"namespace": ns, "data": record})
    return results

def memory_stats() -> dict:
    """Get memory storage statistics."""
    return {
        "events": engine.count("brain:events"),
        "traces": engine.count("brain:traces"),
        "shared_knowledge": engine.count("shared:knowledge"),
    }
```

### 7.5 Memory Data Flow در HiveOS

```ascii
                            USER / SYSTEM
                                │
                                ▼
                     ┌────────────────────┐
                     │   Agent Instance   │
                     │  (در حال اجرا)     │
                     └─────┬──────┬───────┘
                           │      │
              ┌────────────┘      └────────────┐
              ▼                                 ▼
     ┌────────────────┐              ┌──────────────────┐
     │  Working Mem   │              │  Communication   │
     │  (in-RAM dict) │              │  Bus (messages)  │
     └───────┬────────┘              └────────┬─────────┘
             │                                │
             ▼                                ▼
     ┌──────────────────────────────────────────────┐
     │              EventStream                     │
     │  "Happened at T1: agent did X"               │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │           StorageEngine (SQLite)             │
     │  ┌────────────────────────────────────────┐  │
     │  │  kv_store table                        │  │
     │  │  namespace=brain:events → episodic     │  │
     │  │  namespace=agent:*     → private mem   │  │
     │  │  namespace=shared:*    → global mem    │  │
     │  └────────────────────────────────────────┘  │
     └──────────────────────────────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │           DecisionTracer                     │
     │  "Why? Because of steps 1→2→3"              │
     └──────────────────────────────────────────────┘
```

### 7.6 Roadmap — Memory Enhancements در HiveOS

| نسخه | قابلیت حافظه | وضعیت |
|------|-------------|--------|
| v0.8.0 | EventStream + DecisionTracer (in-memory) | ✅ کامل |
| v0.9.0 | StorageEngine (SQLite persistence) | ✅ کامل |
| v0.11.0 | Agent-specific memory namespaces | ✅ کامل |
| v0.12.0 | **Vector memory** (Chroma integration for semantic search) | 📋 برنامه |
| v0.13.0 | **Memory consolidation** (STM → LTM automation) | 📋 برنامه |
| v0.14.0 | **Forgetting mechanisms** (TTL, decay, importance) | 📋 برنامه |
| v1.0.0 | **Distributed memory** (multi-node sync) | 🎯 هدف |

---

## 📚 جمع‌بندی — Summary

سیستم حافظه در ایجنت‌های AI یک **نیاز اساسی** است — بدون آن ایجنت‌ها Stateless و ناقص هستند. این مستند پنج نوع حافظه (Short-term, Long-term, Episodic, Semantic, Procedural) و پنج الگوی پیاده‌سازی (In-Memory, Vector DB, SQLite, RAG, Graph) را بررسی کرد.

در HiveOS، این مفاهیم از طریق:

- **EventStream** → حافظه Episodic
- **DecisionTracer** → حافظه Procedural
- **StorageEngine** → زیرساخت Long-term Memory
- **CommunicationBus** → Shared Memory بین ایجنت‌ها

پیاده‌سازی شده‌اند. مسیر آینده شامل اضافه کردن **Vector Search** برای Semantic Memory و **Consolidation Pipelines** برای مدیریت هوشمند حافظه است.

> **اصل طلایی:** _"An agent without memory is a tool. An agent with memory is a colleague."_
> ایجنت بدون حافظه یک ابزار است. ایجنت با حافظه یک همکار.

---

## 🔗 پیوندها — Related Resources

- [HiveOS Brain Module](../../../src/hiveos/brain/) — کد منبع EventStream و DecisionTracer
- [StorageEngine](../../../src/hiveos/storage/engine.py) — کد منبع StorageEngine
- [CommunicationBus](../../../src/hiveos/mothership/communication_bus.py) — حافظه اشتراکی
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) — Stateful agent graphs
- [Chroma DB](https://www.trychroma.com/) — Vector store for semantic memory
- [OpenAI Assistants](https://platform.openai.com/docs/assistants) — Managed vector stores

---

> **تغییرات:**  
> v1.0.0 — 2026-07-16 — نگارش اولیه کامل
