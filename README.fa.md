# HiveOS 🐝 — سیستم عامل چندعاملی

**نسخه 0.10.0** | [English](README.md)

**تیم‌هایی از ایجنت‌های هوش مصنوعی را orchestrate کنید. گردش‌های کاری را بسته‌بندی کنید. به هر جایی بفرستید.**

HiveOS یک پلتفرم برای طراحی، استقرار و orchestration سیستم‌های چندعاملی (MAS) است. مجموعه‌ای از ایجنت‌های AI را به یک تیم ساختاریافته و هماهنگ تبدیل می‌کند — هر کدام با مهارت‌ها، دانش و نقش خود در یک گردش کار مشخص.

---

## ✨ چرا HiveOS؟

بیشتر فریم‌ورک‌های ایجنت در «یک ایجنت برای هر کار» متوقف می‌شوند. HiveOS ایجنت‌ها را به عنوان **پروسه‌های درجه یک سیستم عامل** مدیریت می‌کند:

| مفهوم | توضیح |
|-------|-------|
| 🧠 **موتور گردش کار** | DSL اعلامی YAML برای تعریف تیم‌های ایجنت، وابستگی‌ها، triggers |
| 🌍 **مادرشیپ** | هماهنگ‌کننده مرکزی با اجرای گره‌های ماهواره‌ای |
| 📦 **بسته‌بندی** | فرمت Tar.gz برای بسته‌بندی و ارسال اکوسیستم‌های ایجنت |
| 🔐 **RBAC** | کنترل دسترسی مبتنی بر نقش با نقش‌های داخلی |
| 📜 **ردیابی حسابرسی** | لاگ‌های روزانه JSONL + جستجوی معنایی gbrain |
| 📊 **داشبورد** | SPA تیره برای مانیتورینگ ایجنت‌ها، flows و گره‌ها |
| 🏢 **چندمستأجری** | workspaceهای ایزوله برای هر تیم/سازمان |
| 💰 **قیمت‌گذاری** | سیستم لایسنس ۴ ردیفه با گیتینگ ویژگی‌ها |
| 🧩 **پلاگین‌های دامنه** | دامنه‌های دانش به عنوان پلاگین‌های قابل نصب |

---

## 🏗️ معماری

```
User → Flow DSL YAML → Flow Engine (مرتب‌سازی توپولوژیک)
                         ├── Agent 1 (مهارت‌های: A, B) ──┐
                         ├── Agent 2 (وابسته: 1) ──────┤→ زیرایجنت Hermes
                         ├── Agent 3 (وابسته: 1) ──────┘
                         └── Agent 4 (وابسته: 2, 3) → خروجی نهایی
```

```
┌──────────────────────────────────────────────────────────┐
│                     لایه دامنه                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │حسابداری  │  │ پزشکی    │  │ حقوقی   │   ...          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
├───────┴──────────────┴──────────────┴─────────────────────┤
│                     هسته HiveOS                          │
│  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐ │
│  │  Flow  │  │  Agent   │  │ Package│  │ Communication│ │
│  │ Engine │  │ Registry │  │ Manager│  │     Bus      │ │
│  └────────┘  └──────────┘  └────────┘  └──────────────┘ │
│  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐ │
│  │  RBAC  │  │  Audit   │  │  CLI   │  │  Dashboard   │ │
│  └────────┘  └──────────┘  └────────┘  └──────────────┘ │
│  ┌────────┐  ┌──────────┐  ┌────────┐                   │
│  │License │  │Workspace │  │Domain  │                   │
│  │Manager │  │ Manager  │  │ Plugins│                   │
│  └────────┘  └──────────┘  └────────┘                   │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   Hermes      │
                 │   Agent       │
                 │   Runtime     │
                 └───────────────┘
```

---

## 🚀 شروع سریع

```bash
# نصب
cd hive-os
uv venv && source .venv/Scripts/activate       # ویندوز
uv pip install .

# مشاهده CLI
hive --version

# اجرای یک نمونه flow
hive flow run prototype/hello-flow/hello.yml

# اعتبارسنجی flowها در یک پوشه
hive flow validate prototype/

# اجرای همه تست‌ها
python -m pytest tests/ -v
```

---

## 🖥️ راهنمای CLI

```
hive
 ├── flow run/validate/list/state/clear-state
 ├── package build/install/list/publish
 ├── registry list/search/info/remove/verify
 ├── mothership
 │    ├── agent register/list/info/remove/capabilities/heartbeat
 │    ├── route assign/reroute/metrics/rules
 │    ├── bus publish/subscribe/stats
 │    ├── health check/monitor/status/failures/circuits/reassignments
 │    └── server start/stop/status
 ├── rbac
 │    ├── user add/list/remove/set-role/set-api-key/enable/disable
 │    └── role add/list/show/remove
 ├── audit list/search/stats/search-gbrain/sync-gbrain/rotate
 ├── dashboard start/stop/status
 ├── workspace create/list/info/update/remove/activate member
 ├── license info/activate/deactivate/upgrade/tiers/check
 └── util init/info
```

### دستورات لایسنس

```bash
hive license info              # نمایش لایسنس فعلی
hive license activate <key>    # فعال‌سازی کلید دمو یا واقعی
hive license deactivate        # بازگشت به رایگان
hive license upgrade pro       # ارتقاء/کاهش ردیف
hive license tiers             # مقایسه همه ردیف‌ها
hive license check <feature>   # بررسی در دسترس بودن ویژگی
```

**کلیدهای دمو:** `hive-pro-demo`، `hive-ent-demo`، `hive-ult-demo`

---

## 🧩 سیستم پلاگین دامنه

HiveOS **مستقل از دامنه** است — هر دامنه‌ای از دانش می‌تواند به عنوان پلاگین نصب شود.

### 🔢 دامنه حسابداری (D1)

اولین دامنه: یک دستیار کامل حسابداری و مالی ساخته شده از سرفصل‌های رسمی آموزش عالی ایران.

```
domains/accounting/
├── domain.yaml                     ★ مانیفست دامنه (۲۹ ایجنت، ۶ فلو)
├── knowledge/
│   ├── tree.yaml                   ★ درخت دانش ۲۰۰+ گره (۱۰ شاخه A-J)
│   └── references/                 سرفصل‌های منبع
├── agents/
│   └── blueprints/                 ★ ۲۹ فایل YAML blueprint ایجنت
│       ├── master-financial-assistant.yaml     هماهنگ‌کننده سطح ۳
│       ├── financial-orchestrator.yaml         هماهنگ‌کننده‌های سطح ۲
│       ├── management-orchestrator.yaml
│       ├── audit-orchestrator.yaml
│       ├── tax-orchestrator.yaml
│       ├── advisory-orchestrator.yaml
│       ├── financial-recorder.yaml             متخصصان سطح ۱
│       ├── financial-reporter.yaml
│       ├── ...                                 ۲۳ متخصص دیگر
└── flows/                         ★ ۶ فایل YAML قالب گردش کار
    ├── financial-close.yaml       بستن حساب پایان دوره
    ├── tax-return.yaml            تهیه اظهارنامه مالیاتی
    ├── audit-engagement.yaml      انجام قرارداد حسابرسی
    ├── company-valuation.yaml     ارزش‌گذاری شرکت
    ├── annual-budget.yaml         تهیه بودجه سالانه
    └── fraud-investigation.yaml   بررسی تقلب مالی
```

---

## 📋 نقشه راه

### ✅ فاز ۰: بنیاد
Flow DSL، موتور گردش کار، CLI، سیستم بسته‌بندی، prototype flows

### ✅ فاز ۱: آزمایشگاه
Flow DSL v0.1، ذخیره وضعیت، مدیریت خطا، دموی ۳ ایجنت

### ✅ فاز ۲: یکپارچه‌سازی
زیرایجنت Hermes، قابلیت ادامه، تلاش مجدد/رد شدن آبشاری، همگام‌سازی دانش

### ✅ فاز ۳: بسته‌بندی
بسته‌های Tar.gz، رجیستری محلی، کلاینت رجیستری راه دور، دستورات CLI

### ✅ فاز ۴: مادرشیپ
رجیستری ایجنت با قابلیت‌ها، مسیریابی وظایف (۵ استراتژی)، گذرگاه ارتباطی (pub/sub)، موتور تاب‌آوری، سرور HTTP FastAPI

### ✅ فاز ۵: سازمانی
RBAC (۳۶ تست)، ردگیری حسابرسی (۲۰ تست)، داشبورد (۲۳ تست)، workspaceهای چندمستأجری (۳۸ تست)، لایسنس/قیمت‌گذاری (۳۲ تست)

### 🏗️ فاز D1: دامنه حسابداری 🏗️
- ✅ درخت دانش (۲۰۰+ گره، ۱۰ شاخه)
- ✅ مانیفست دامنه (۲۹ ایجنت، ۶ فلو)
- ✅ مستندات معماری دامنه
- ✅ ۲۹ blueprint ایجنت (YAML)
- ✅ ۶ قالب گردش کار (YAML)
- ⏳ مهارت‌های Hermes برای هر ایجنت
- ⏳ API تولید خودکار ایجنت
- ⏳ API مرور قالب‌ها

### ⏳ فاز D2: سیستم پلاگین دامنه
CLI دامنه، رجیستری، بارگذاری در مادرشیپ

---

## 🎯 پیش رو: فاز ۶ — پلی‌گراند (رابط کاربری بصری)

**هدف:** جایگزینی فلوهای YAML با سازنده بصری drag-and-drop.

| اولویت | ویژگی |
|--------|-------|
| 🔴 | API اعتبارسنجی فلو + API تولید خودکار ایجنت |
| 🔴 | مرورگر قالب (پیش‌نمایش فلوهای دامنه) |
| 🔴 | بوم بصری (React Flow، کشیدن و رها کردن) |
| 🔴 | اجرا/دیباگ با لاگ‌های زنده |
| 🟡 | گیت‌های تأیید انسانی (human-in-the-loop) |
| 🟡 | سفارشی‌سازی قالب + کتابخانه فلو |
| 🟢 | شرایط بصری + زیرفلو |

---

## 🎯 پیش رو: فاز ۷ — مغز (ویژوالایزر سه‌بعدی شفاف)

**هدف:** شفافیت کامل با نمایش عصبی سه‌بعدی实时.

| اولویت | ویژگی |
|--------|-------|
| 🔴 | رویدادهای زنده ایجنت‌ها |
| 🔴 | ردیاب مسیر تصمیم‌گیری |
| 🔴 | موتور گیت تأیید |
| 🟡 | نمایش عصبی سه‌بعدی |
| 🟡 | اتصال WebSocket بی‌درنگ |
| 🟢 | کاوش تعاملی + پخش دوباره تاریخی |

---

## 🎯 پیش رو: فاز ۸ — یادگیری

- تحلیل اجراها
- تشخیص الگو → پیشنهاد قالب
- انباشت دانش
- مسیریابی تطبیقی

---

## 🧪 آمار تست‌ها

| ماژول | تست | وضعیت |
|-------|-----|-------|
| موتور گردش کار | ۱۳ | ✅ |
| رجیستری ایجنت | ۲۰ | ✅ |
| مسیریابی وظایف | ۱۶ | ✅ |
| گذرگاه ارتباطی | ۱۴ | ✅ |
| تاب‌آوری | ۲۰ | ✅ |
| همگام‌سازی | ۱۲ | ✅ |
| رجیستری بسته | ۱۶ | ✅ |
| RBAC | ۳۶ | ✅ |
| ردگیری حسابرسی | ۲۰ | ✅ |
| داشبورد | ۲۳ | ✅ |
| workspace | ۳۸ | ✅ |
| لایسنس | ۳۲ | ✅ |
| **مجموع** | **۲۷۳** | **✅ همه قبول** |

---

## 📁 ساختار پروژه

```
hive-os/
├── src/hiveos/                  بسته پایتون
│   ├── cli/main.py              نقطه ورود CLI
│   ├── dsl.py                   تعاریف DSL گردش کار
│   ├── engine.py                 موتور اجرای گردش کار
│   ├── license/                 قیمت‌گذاری و گیتینگ ویژگی‌ها
│   ├── rbac/                    کنترل دسترسی مبتنی بر نقش
│   ├── audit/                   ردگیری حسابرسی (JSONL + gbrain)
│   ├── dashboard/               رابط کاربری وب (FastAPI + SPA)
│   ├── workspace/               workspaceهای چندمستأجری
│   ├── mothership/              رجیستری ایجنت، مسیریاب، گذرگاه، تاب‌آوری
│   ├── registry/                رجیستری بسته (محلی + راه دور)
│   ├── sync/                    رجیستری گره، همگام‌سازی دانش
│   ├── package/                 بسته‌ساز/نصب‌کننده
│   └── utils/                   تنظیمات، اعتبارسنج، مدیریت دانش
├── domains/                     ★ پلاگین‌های دامنه
│   └── accounting/              اولین دامنه: حسابداری و مالی
│       ├── domain.yaml          مانیفست دامنه
│       ├── knowledge/tree.yaml  درخت دانش (۲۰۰+ گره)
│       ├── agents/blueprints/   ۲۹ فایل YAML blueprint ایجنت
│       └── flows/               ۶ فایل YAML قالب گردش کار
├── docs/                        پایگاه دانش (انبار Obsidian)
├── prototype/                   گردش‌های کاری نمونه
├── tests/                       ۲۷۳ تست
├── ROADMAP.md                   نقشه راه زنده
├── MANIFEST.md                  مانیفست محصول
└── AGENTS.md                    فایل بوت ایجنت (بارگذاری خودکار توسط Hermes)
```

---

## 📄 مستندات

| فایل | هدف |
|------|-----|
| `README.md` | نمای کلی انگلیسی |
| `README.fa.md` | نمای کلی فارسی (این فایل) |
| `ROADMAP.md` | نقشه راه زنده محصول |
| `MANIFEST.md` | مانیفست و اصول محصول |
| `AGENTS.md` | بافت کامل پروژه (بارگذاری خودکار توسط Hermes) |
| `hiveos-skill.md` | تعریف مهارت Hermes |
| `docs/01-Vision/01-product-vision.md` | چشم‌انداز محصول |
| `docs/01-Vision/02-domain-ecosystem-vision.md` | چشم‌انداز اکوسیستم دامنه |
| `docs/02-Architecture/01-high-level-arch.md` | معماری سطح بالا |
| `docs/02-Architecture/02-flow-dsl.md` | مشخصات DSL گردش کار |
| `docs/02-Architecture/03-domain-plugin-system.md` | سیستم پلاگین دامنه |

---

## 🔧 توسعه

```bash
# راه‌اندازی
cd hive-os
python -m venv .venv && source .venv/Scripts/activate
uv pip install -e .

# اجرای تست‌ها
python -m pytest tests/ -v

# نصب بسته
uv pip install .

# ساخت توزیع
python -m build
```

---

## 📜 مجوز

**HiveOS Enterprise** — اختصاصی

مجوز ردیفی: رایگان، حرفه‌ای، سازمانی، نهایی.
برای جزئیات: `hive license` یا `hive license tiers`

---

## 🌐 پیوندها

- **گیت‌هاب:** [hossein1377mobini/hiveos-financial-brain](https://github.com/hossein1377mobini/hiveos-financial-brain)
- **نویسنده:** حسین مبینی — پژوهشگر دکتری (CVC/کارآفرینی)
