# معماری دامنه‌ها در HiveOS — Domain Architecture

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **فایل‌های مرتبط:** `src/hiveos/domain/` · `src/hiveos/mothership/` · `docs/02-Architecture/03-domain-plugin-system.md`

---

## ۱. مفهوم Domain در HiveOS

**Domain (دامنه)** در HiveOS یک **ماژول دانش تخصصی** است که شامل:

| مؤلفه | توضیح |
|-------|-------|
| **عامل‌ها (Agents)** | عامل‌های تخصصی آن دامنه |
| **ابزارها (Tools)** | ابزارهای مورد نیاز عامل‌ها |
| **جریان‌ها (Flows)** | گردش کارهای از پیش تعریف‌شده |
| **دانش (Knowledge)** | محتوای آموزشی و مرجع |
| **تنظیمات (Config)** | پیکربندی دامنه |

### دامنه‌های فعلی:

| دامنه | وضعیت | عامل‌ها | توضیح |
|-------|--------|---------|-------|
| **Accounting** | ✅ نصب | ۶ عامل | حسابداری و مالی ایران |
| **General** | ✅ داخلی | ۳ عامل | عامل‌های عمومی و orchestration |

---

## ۲. معماری Domain Registry

Domain Registry — که در v0.11.0 پیاده‌سازی شده — یک **کاتالوگ مرکزی** برای مدیریت دامنه‌ها است:

```python
# DomainRegistry — هستهٔ مدیریت دامنه‌ها
class DomainRegistry:
    """مدیریت متمرکز دامنه‌ها — StorageEngine-backed"""
    
    def __init__(self, storage_engine):
        self.storage = storage_engine
        self.domains: dict[str, Domain] = {}
    
    def scan_domains(self) -> list[DomainManifest]:
        """جستجوی خودکار دامنه‌های نصب‌شده"""
        # دامنه‌ها در ~/.hiveos/domains/ یا packages/domain-* ذخیره می‌شوند
    
    def install_domain(self, name: str) -> DomainManifest:
        """نصب دامنه جدید + وابستگی‌ها"""
    
    def get_agent_blueprints(self, domain: str) -> list[AgentBlueprint]:
        """دریافت blueprintهای عامل‌های یک دامنه"""
    
    def resolve_dependencies(self, domain: str) -> list[str]:
        """حل وابستگی‌های ترایا (transitive) با detection دور"""
    
    def verify_integrity(self, domain: str) -> IntegrityReport:
        """بررسی یکپارچگی دامنه"""
```

---

## ۳. ساختار یک Domain

هر دامنه در HiveOS از این ساختار پیروی می‌کند:

```
domain-{name}/
├── manifest.yaml           ← مانیفست دامنه (نام، نسخه، وابستگی‌ها)
├── agents/
│   ├── agent-1.yaml        ← تعریف عامل‌ها
│   └── agent-2.yaml
├── flows/
│   ├── flow-1.yaml         ← جریان‌های از پیش تعریف‌شده
│   └── flow-2.yaml
├── tools/
│   ├── tool-1.py           ← ابزارهای تخصصی
│   └── tool-2.py
└── knowledge/
    ├── docs/                ← مستندات و محتوای آموزشی
    └── references/          ← منابع مرجع
```

### مثال manifest.yaml:

```yaml
name: accounting
version: 1.0.0
label: "حسابداری ایران"
description: "دامنه تخصصی حسابداری ایران — قوانین، استانداردها، محاسبات"
author: HiveOS Team

dependencies:
  - general >= 1.0.0

agents:
  - id: financial-analyst
    label: "تحلیل‌گر مالی"
    model: claude-sonnet-4
    tools: [financial-statements, ratio-analyzer]
  
  - id: tax-calculator
    label: "محاسبه‌گر مالیات"
    model: gpt-4o-mini
    tools: [tax-rates, deduction-calc]

flows:
  - id: financial-report
    label: "گزارش مالی"
    steps:
      - agent: financial-analyst
      - agent: tax-calculator

tools:
  - id: financial-statements
    type: python
    path: tools/financial_statements.py
  
  - id: tax-rates
    type: knowledge
    path: knowledge/tax-rates-1404.md
```

---

## ۴. حلقهٔ حیات دامنه (Domain Lifecycle)

```text
کشف (Scan) ← نصب (Install) ← فعال‌سازی (Activate) ← اجرا (Run) ← بروزرسانی (Update) ← حذف (Remove)
     │              │               │               │              │                │
     ▼              ▼               ▼               ▼              ▼                ▼
  جستجو در     بررسی      ثبت در      استفاده در   اعمال          پاک کردن
  packages/   وابستگی‌ها  Registry    Flowها      تغییرات        داده‌ها
```

---

## ۵. Domain Registry API (REST)

| متد | مسیر | توضیح |
|-----|------|-------|
| `GET` | `/api/domains` | لیست دامنه‌ها |
| `GET` | `/api/domains/{name}` | جزئیات دامنه |
| `POST` | `/api/domains/install` | نصب دامنه جدید |
| `POST` | `/api/domains/{name}/uninstall` | حذف دامنه |
| `GET` | `/api/domains/{name}/agents` | عامل‌های دامنه |
| `GET` | `/api/domains/{name}/flows` | جریان‌های دامنه |
| `POST` | `/api/domains/learn` | تحلیل و یادگیری دامنه |
| `GET` | `/api/domains/suggestions` | پیشنهاد دامنه‌های مرتبط |

---

## ۶. ارتباط با معماری کلی HiveOS

```text
┌─────────────────────────────────────┐
│          HiveOS Core                 │
│  ┌──────────┐  ┌────────────────┐   │
│  │ Flow     │  │ Mothership     │   │
│  │ Engine   │──│ (Orchestrator) │   │
│  └──────────┘  └───────┬────────┘   │
│                        │            │
│  ┌─────────────────────▼──────────┐ │
│  │      Domain Registry           │ │
│  └──┬──────────┬──────────┬───────┘ │
│     │          │          │         │
│  ┌──▼──┐  ┌───▼──┐  ┌───▼──┐      │
│  │ Acc.│  │ Tax  │  │ HR   │ ...   │
│  │Dom. │  │ Dom. │  │ Dom. │       │
│  └─────┘  └──────┘  └──────┘       │
└─────────────────────────────────────┘
```

---

> **نکته:** این فایل نمای کلی معماری دامنه‌هاست. برای جزئیات پیاده‌سازی به `docs/02-Architecture/03-domain-plugin-system.md` و `src/hiveos/domain/` مراجعه کنید.
