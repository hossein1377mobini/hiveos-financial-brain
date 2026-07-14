# Domain Plugin System Architecture 🧩

> چارچوب معماری برای تعریف، ثبت و اجرای Domain Plugin‌ها روی HiveOS.
> Core پلتفرم به محتوای دامنه وابسته نیست — فقط قراردادها را اجرا می‌کند.

---

## 1. Core Concepts

### 1.1 What is a Domain?

یک **دامنه (Domain)** یک حوزه تخصصی از دانش انسانی است که:

- **Knowledge Tree** دارد — ساختار سلسله‌مراتبی مفاهیم آن حوزه
- **Agent Blueprints** دارد — نقش ایجنت‌های تخصصی آن حوزه
- **Flows** دارد — جریان‌های کاری استاندارد آن حوزه
- **Rules** دارد — قوانین، استانداردها و مقررات خاص آن حوزه

### 1.2 Lifecycle of a Domain

```
Define (domain.yaml) 
    → Register (hive domain register)
        → Install (hive domain install <name>)
            → Load Agents (blueprints → Hermes agents)
                → Run Flows (flows → flow engine)
```

### 1.3 Domain Abstraction Layer

Core HiveOS **نمی‌داند** که accounting چیست. فقط می‌داند:

- یک domain با نام `accounting` ثبت شده
- درخت دانش آن ۱۰ شاخه اصلی دارد
- ۱۵ blueprint ایجنت دارد
- ۸ flow پیش‌فرض دارد
- ایجنت‌ها روی `mothership` به عنوان node ثبت می‌شوند
- flowها با `flow engine` اجرا می‌شوند

---

## 2. Domain Package Structure

### 2.1 Standard Layout

```
domains/<domain-name>/
├── domain.yaml              # REQUIRED: Domain manifest
├── knowledge/
│   ├── tree.yaml            # REQUIRED: Knowledge tree
│   └── references/          # OPTIONAL: Reference materials
│       ├── books/           # کتاب‌های مرجع
│       ├── standards/       # استانداردها (IFRS, GAAP, ISA, ...)
│       ├── laws/            # قوانین و مقررات
│       └── articles/        # مقالات کلیدی
├── agents/
│   ├── blueprints/          # REQUIRED: Agent definitions
│   │   ├── agent-a.yaml
│   │   └── agent-b.yaml
│   └── prompts/             # OPTIONAL: System prompts for agents
├── flows/                   # OPTIONAL: Default workflow templates
├── skills/                  # OPTIONAL: Hermes skills for this domain
├── rules/                   # OPTIONAL: Domain rule files (for Rule Engine)
│   └── rule-sets.yaml
└── tests/                   # OPTIONAL: Domain-specific tests
```

### 2.2 domain.yaml Specification

```yaml
domain:
  name: <snake_case_name>
  version: <semver>
  label:
    fa: "<نام فارسی>"
    en: "<English Name>"
  description:
    fa: "<توضیحات فارسی>"
    en: "<English description>"
  
  # وابستگی به domainهای دیگر
  depends_on: []
  
  # Domain Orchestrator — ایجنت اصلی که به عنوان درگاه ورود عمل می‌کند
  orchestrator_agent: "<agent-id>"
  
  # Metadata
  metadata:
    authors: []
    tags: []
    homepage: ""
    source_syllabus: []     # سرفصل‌های رسمی که دانش از آنها استخراج شده
  
  # Agent blueprints
  agents:
    - id: "<unique-id>"
      label: "<display name>"
      description: "<what this agent does>"
      knowledge_paths: []    # کدام شاخه‌های درخت دانش را پوشش می‌دهد
      skills: []             # Hermes skills مورد نیاز
      type: specialist       # specialist | orchestrator
  
  # Knowledge tree reference
  knowledge_tree: "knowledge/tree.yaml"
  
  # Flow templates
  flows:
    - id: "<flow-id>"
      label: "<display name>"
      file: "flows/<file>.yaml"
```

---

## 3. Knowledge Tree Schema

درخت دانش، **مهم‌ترین بخش یک دامنه** است. هرگره (node) می‌تواند:

| ویژگی | نوع | توضیح |
|--------|------|-------|
| `id` | string | شناسه یکتای گره (A1, A1.1, ...) |
| `label` | object | نام فارسی و انگلیسی |
| `description` | object | توضیح مختصر |
| `children` | array | زیرشاخه‌ها |
| `ref` | object | منابع اطلاعاتی مرتبط با این گره |
| `tags` | array | برچسب‌های جستجو |
| `skills_needed` | array | مهارت‌های مورد نیاز برای این حوزه |
| `agent_id` | string | ایجنت پیش‌فرضی که این گره را پوشش می‌دهد |

```yaml
nodes:
  - id: "A"
    label: { fa: "حسابداری مالی", en: "Financial Accounting" }
    description: { fa: "...", en: "..." }
    children:
      - id: "A1"
        label: { fa: "ثبت رویدادها", en: "Transaction Recording" }
        agent_id: "financial-recorder"
        skills_needed: ["journal-entry", "reconciliation"]
        ref:
          books: ["کتاب حسابداری میانه ۱"]
          standards: ["IAS 1", "IAS 8"]
```

---

## 4. Agent Blueprint Schema

برای هر ایجنت در دامنه، یک blueprint تعریف می‌شود:

```yaml
agent:
  id: "financial-recorder"
  label: { fa: "ثبت‌کننده مالی", en: "Financial Recorder" }
  type: specialist
  
  # کدام بخش از درخت دانش را پوشش می‌دهد
  covers:
    - "A1"    # Transaction Recording
    - "A6"    # Standards
    - "A2.1"  # Cash & Receivables
  
  # مهارت‌های Hermes
  skills:
    - journal-entry
    - reconciliation
    - trial-balance
  
  # System prompt برای این ایجنت
  prompt: |
    تو یک حسابدار حرفه‌ای هستی که در ثبت رویدادهای مالی تخصص داری...
  
  # Flowهایی که این ایجنت می‌تواند انجام دهد
  default_flows:
    - id: "record-transaction"
      label: "ثبت سند حسابداری"
  
  # پارامترهای اجرایی
  config:
    max_retries: 3
    timeout: 300
```

---

## 5. Cross-Domain Interaction

وقتی چند domain روی یک HiveOS نصب می‌شوند، می‌توانند با هم تعامل کنند:

```
HiveOS Core
│
├── Accounting Domain
│   ├── Knowledge: حسابداری مالی، مالیاتی، حسابرسی
│   └── Agent: tax-specialist نیاز به دانش حقوقی دارد → 
│       └── Legal Domain (هنگام نصب domain حقوقی)
│           └── Knowledge: قوانین مالیاتی، حقوق تجارت
│
└── Cross-Domain Flow
    └── "بررسی مالیاتی یک شرکت"
        ├── Agent A (tax-specialist) ← Accounting Domain
        ├── Agent B (commercial-lawyer) ← Legal Domain
        └── Agent C (auditor) ← Accounting Domain
```

**قانون:** یک domain فقط در صورت وابستگی صریح (`depends_on`) می‌تواند به دانش domain دیگر دسترسی داشته باشد.

---

## 6. CLI Interface for Domains

دستورات `hive domain` در Core HiveOS:

| Command | Description |
|---------|-------------|
| `hive domain list` | لیست domain های نصب شده |
| `hive domain info <name>` | اطلاعات یک domain |
| `hive domain install <path/name>` | نصب domain جدید |
| `hive domain remove <name>` | حذف domain |
| `hive domain init <name>` | ایجاد scaffold یک domain جدید |
| `hive domain agents <name>` | لیست ایجنت‌های یک domain |
| `hive domain flows <name>` | لیست flowهای یک domain |
| `hive domain knowledge <name>` | نمایش درخت دانش یک domain |

---

## 7. Files vs Implementation

| فایل | وضعیت |
|------|--------|
| `docs/01-Vision/02-domain-ecosystem-vision.md` | ✅ Vision |
| `docs/02-Architecture/03-domain-plugin-system.md` | ✅ Architecture (this file) |
| `domains/accounting/domain.yaml` | 🟡 Created (first domain) |
| `domains/accounting/knowledge/tree.yaml` | 🟡 Created |
| `domains/accounting/agents/blueprints/` | ⬜ Empty (next step) |
| `src/hiveos/domains/` (Python module) | ⬜ Not yet implemented |
| `hive domain` CLI commands | ⬜ Not yet implemented |
