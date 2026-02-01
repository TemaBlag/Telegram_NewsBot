# 📖 Telegram Bot Documentation: NewsBot

This project is a Telegram bot designed for news aggregation and thematic newsletter management. It allows users to subscribe to specific categories of interest and provides administrators with tools for content management and mass broadcasting.

**Tech Stack:** `Python 3.10+`, `aiogram 3`, `Supabase (PostgreSQL)`, `APScheduler`.

**Bot Handle:** [@greatnewstechbot](https://t.me/greatnewstechbot)

---

## 🛠 Installation and Setup

### Prerequisites

* Python 3.9 or higher.
* A Supabase account and project.
* A Telegram Bot Token (from [@BotFather](https://www.google.com/search?q=https://t.me/botfather)).

### Installation Steps

1. **Clone the Repository:**
```bash
git clone 
cd tg_bot

```


2. **Create a Virtual Environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

```


3. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


4. **Configure Environment Variables:**
Create a `.env` file in the root directory (see the [Environment Configuration](https://www.google.com/search?q=%23-environment-configuration-env) section).
5. **Run the Bot:**
```bash
python bot.py

```



---

## 📂 Project Structure

```text
TG_BOT/
├── bot.py                  # Entry point. Inits Bot, Dispatcher, and Scheduler.
├── database/               # Database interactions.
│   └── supabase.py         # Supabase client, caching, and RPC wrappers.
├── handlers/               # Message handlers (Routers).
│   ├── admin.py            # Admin panel (FSM, CRUD for categories, broadcasts).
│   └── user.py             # User menu and subscription logic.
├── mailing/                # Newsletter logic.
│   ├── tech_news/          # Tech maintenance news module.
│   │   ├── tech_news.py    # Message formatting and delivery.
│   │   └── supabase_tech_news.py # DB fetching logic for tech news.
│   └── bank_news/          # Banking news module.
├── utils/                  # Helper utilities.
│   ├── admin_utils.py      # Permission checks, admin keyboards.
│   └── user_utils.py       # User-facing keyboards.
└── .env                    # Secret keys.

```

---

## 🗄 Database Architecture (Supabase)

The project heavily utilizes **RPC (Remote Procedure Calls)** to offload business logic to the database side, ensuring high performance and data integrity.

### Core Tables

* `categories`: Stores `id`, `category_name`, and `description`.
* `users`: Stores unique `user_id` (bigint) and `created_at`.
* `user_subscriptions`: A junction table mapping `user_id` to `category_id`.
* `tech_news`: Stores news items with `is_sent` flags for the scheduler.

### Essential RPC Functions

The bot relies on the following PostgreSQL functions:

* `update_user_subscriptions`: Transactionally updates user preferences (deletes old, inserts new).
* `get_categories_stats`: Aggregates the number of subscribers per category for admin analytics.
* `delete_category`: Safely removes a category and cascades the deletion to all active user subscriptions.

---

## ⚙️ Features

### 👤 User Features

1. **Main Menu (`/start`):** Quick access to subscriptions and project info.
2. **Newsletter Catalog:** Browse available topics with detailed descriptions.
3. **Subscription Management:**
* Interactive menu with checkboxes (✅/⬜).
* **Stateful Saving:** Changes are applied only after clicking **"Save"**, significantly reducing database overhead.


4. **Automated Feed:** Receive real-time updates based on chosen topics.

### 🛡 Admin Features

Accessed via the `/admin` command (restricted to `ADMIN_IDS`).

* **📊 Analytics:** Real-time counters for total users and per-category subscription density.
* **🆕 Mass Broadcast:** Send rich-media messages to the entire user base using the `copy_to` method to preserve formatting.
* **📂 Category CRUD:** Create, edit (HTML support), and delete newsletter topics dynamically.

### ⏰ Scheduled Tasks

Managed via `APScheduler`:

* **Schedule:** Runs every 15 minutes between 08:00 and 18:00 (MSK).
* **Batching:** Grouping news items to fit the 4096-character limit.
* **Rate Limiting:** Implements a 0.2s delay between messages to comply with Telegram Anti-Spam policies.

---

## 🔧 Technical Implementation Details

* **Concurrency:** Synchronous Supabase calls are wrapped in `asyncio.to_thread` to keep the Event Loop non-blocking.
* **Caching:** `cachetools.TTLCache` is implemented for category metadata to minimize redundant network requests.
* **Security:** Role-based access control (RBAC) is enforced at the router level via custom `is_admin` filters.
* **Resilience:** The broadcast engine gracefully handles `TelegramForbiddenError` (deleting inactive users) and `TelegramRetryAfter` (handling flood limits).

---