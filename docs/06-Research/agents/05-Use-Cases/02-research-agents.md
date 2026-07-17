# عامل‌های تحقیق — Research Agents (کاربردها و سناریوها)

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶

---

## ۱. مقدمه

**عامل‌های تحقیق (Research Agents)** برای جمع‌آوری، تحلیل و ترکیب اطلاعات از منابع مختلف طراحی شده‌اند. این عامل‌ها در دنیای امروز که حجم اطلاعات روزافزون است، ارزش بالایی دارند.

### قابلیت‌های کلیدی:
- **جستجوی هوشمند** در وب، پایگاه‌های علمی، اسناد
- **استخراج و خلاصه‌سازی** اطلاعات
- **ترکیب و سنتز** منابع مختلف
- **اعتبارسنجی** واقعیت‌ها (Fact-Checking)
- **مدیریت ارجاع** (Citation Management)

---

## ۲. معماری Research Agent

```text
┌────────────────────────────────────────────┐
│           Research Agent                    │
│                                            │
│  پرسش → [تجزیه به زیرسوالات] → [جستجوی موازی] │
│                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Search  │ │Search 2 │ │Search 3 │  ...  │
│  │ (Arxiv) │ │  (Web)  │ │ (Books) │       │
│  └────┬────┘ └────┬────┘ └────┬────┘       │
│       │           │           │            │
│       └──────┬────┴──────┬────┘            │
│              ▼           ▼                  │
│  ┌──────────┐   ┌──────────┐               │
│  │ ترکیب    │──▶│ تحلیل    │               │
│  └──────────┘   └──────────┘               │
│                     │                       │
│                     ▼                       │
│  ┌──────────┐   ┌──────────┐               │
│  │ گزارش    │──▶│ اعتبار-  │               │
│  │ نویسی    │   │ سنجی     │               │
│  └──────────┘   └──────────┘               │
└────────────────────────────────────────────┘
```

---

## ۳. سناریوهای کاربردی

| سناریو | توضیح | ابزارهای مورد نیاز |
|--------|-------|-------------------|
| **مرور ادبیات علمی** | جستجوی مقالات مرتبط، خلاصه‌سازی، مقایسه | Semantic Scholar, Arxiv, Google Scholar |
| **تحلیل رقبا** | بررسی وب‌سایت‌ها، محصولات، قیمت‌های رقبا | Web Search, Web Extract, Social Media |
| **تحقیق بازار** | جمع‌آوری آمار، روندها، نیازهای مشتریان | Market DB, Web Search, APIs |
| **جمع‌آوری دانش** | استخراج دانش از اسناد PDF/DOCX | PDF Reader, OCR, Text Extractor |
| **بررسی واقعیت** | اعتبارسنجی ادعاها با منابع متعدد | Web Search, Fact-Check DB |

### مثال: Research Agent برای تحقیق علمی

```yaml
name: literature-review
agents:
  - role: search-planner
    task: "تجزیه سوال تحقیق به زیرسوالات و کلیدواژه‌ها"
  - role: searcher
    count: 3
    task: "جستجوی هم‌زمان در Semantic Scholar, Arxiv, Google Scholar"
  - role: synthesizer
    task: "ترکیب و سنتز نتایج جستجو"
  - role: report-writer
    task: "نوشتن گزارش نهایی با رفرنس‌های کامل"
```

---

## ۴. Research Agents در HiveOS

HiveOS از Research Agentها برای پر کردن محتوای آموزشی دامنه‌ها استفاده می‌کند. مثلاً:

```python
# HiveOS — Research Agent برای دامنه حسابداری
research_flow = {
    "name": "accounting-research",
    "agent": "research-agent",
    "task": "جمع‌آوری آخرین قوانین مالیات بر ارزش افزوده ۱۴۰۴",
    "sources": [
        "audit.org.ir",
        "irhesabdaran.ir",
        "intamedia.ir"
    ],
    "output": {
        "format": "markdown",
        "path": "docs/06-Research/accounting/03-مالیات/"
    }
}
```

---

**فایل‌های مرتبط:**
- `docs/06-Research/agents/02-Multi-Agent-Systems/02-communication-and-coordination.md`
- `docs/06-Research/agents/03-Frameworks/01-agent-frameworks-overview.md`
