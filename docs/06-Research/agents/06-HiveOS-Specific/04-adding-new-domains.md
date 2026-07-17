# اضافه کردن دامنه جدید به HiveOS — Adding New Domains

> **نویسنده:** تیم مستندات HiveOS  
> **تاریخ:** جولای ۲۰۲۶  
> **فایل‌های مرتبط:** `src/hiveos/domain/` · `hive domain init` · `docs/02-Architecture/`

---

## ۱. مقدمه

دامنه‌ها (Domains) ماژول‌های توسعه‌پذیر HiveOS هستند. هر کسی می‌تواند یک دامنه جدید بنویسد و نصب کند. این راهنما مراحل اضافه کردن یک دامنه جدید را توضیح می‌دهد.

---

## ۲. روش ۱: با CLI

ساده‌ترین روش — از خط فرمان:

```bash
# ایجاد دامنه جدید
hive domain init my-domain

# این دستور:
# ۱. یک پوشه domain-my-domain/ می‌سازد
# ۲. فایل manifest.yaml با قالب اولیه می‌سازد
# ۳. پوشه‌های agents/, flows/, tools/, knowledge/ را می‌سازد
```

### خروجی دستور:

```
📦 Creating new domain 'my-domain'...
✅ Created: domain-my-domain/
✅ Created: domain-my-domain/manifest.yaml
✅ Created: domain-my-domain/agents/
✅ Created: domain-my-domain/flows/
✅ Created: domain-my-domain/tools/
✅ Created: domain-my-domain/knowledge/

🔧 Next steps:
  1. Edit manifest.yaml — set name, description, dependencies
  2. Add agent blueprints in agents/
  3. Add flow definitions in flows/
  4. Add tool implementations in tools/
  5. Add knowledge content in knowledge/

📥 To install: hive domain install my-domain
```

---

## ۳. روش ۲: دستی

### مرحله ۱: ساختار پوشه‌ها

```
domain-my-domain/
├── manifest.yaml
├── agents/
│   └── agent.yaml
├── flows/
│   └── flow.yaml
├── tools/
│   └── tool.py
└── knowledge/
    └── README.md
```

### مرحله ۲: مانیفست

```yaml
# domain-my-domain/manifest.yaml
name: my-domain
version: 1.0.0
label: "دامنه جدید من"
description: "توضیح کوتاه درباره دامنه"
author: Your Name

dependencies:
  - general >= 1.0.0

agents:
  - id: my-agent
    label: "عامل من"
    model: claude-sonnet-4
    tools: [my-tool]

flows:
  - id: my-flow
    label: "جریان من"
    steps:
      - agent: my-agent

tools:
  - id: my-tool
    type: python
    path: tools/my_tool.py
```

### مرحله ۳: تعریف ابزار

```python
# domain-my-domain/tools/my_tool.py
from hiveos.tools import BaseTool

class MyTool(BaseTool):
    """ابزار نمونه برای دامنه جدید"""
    
    name = "my-tool"
    description = "توضیح ابزار"
    
    parameters = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "ورودی"
            }
        }
    }
    
    async def run(self, input: str) -> dict:
        # منطق ابزار
        return {"result": f"پردازش شد: {input}"}
```

### مرحله ۴: نصب

```bash
# نصب دامنه
hive domain install my-domain

# بررسی نصب
hive domain list
hive domain info my-domain
```

---

## ۴. محتوای دانش دامنه

برای هر دامنه، باید محتوای آموزشی (Knowledge) تهیه کنید:

```markdown
# domain-my-domain/knowledge/README.md

# دانش دامنهٔ من

## منابع
- منبع ۱: توضیح
- منبع ۲: توضیح

## مفاهیم کلیدی
- مفهوم ۱
- مفهوم ۲
```

---

## ۵. بهترین روش‌ها (Best Practices)

| نکته | توضیح |
|------|-------|
| **نام‌گذاری** | از kebab-case استفاده کنید: `my-domain` |
| **وابستگی‌ها** | حداقل وابستگی را داشته باشید |
| **تست** | قبل از انتشار، ابزارها را تست کنید |
| **مستندات** | حتماً README بنویسید |
| **نسخه‌بندی** | از semantic versioning استفاده کنید |
| **خطاها** | خطاهای ابزار را مدیریت کنید |

---

## ۶. Troubleshooting

| مشکل | راهکار |
|------|--------|
| `domain not found` | دامنه را با `hive domain list` بررسی کنید |
| `dependency error` | وابستگی‌ها را در manifest بررسی کنید |
| `tool not available` | مسیر ابزار را بررسی کنید |
| `agent not responding` | مدل و API key را بررسی کنید |

---

> **نویسنده:** تیم مستندات HiveOS — جولای ۲۰۲۶
> 
> **فایل‌های مرتبط:** `docs/02-Architecture/03-domain-plugin-system.md`
