# Technical Specifications: Telegram Bot @greatnewstechbot

## 1. Purpose

The bot is designed to automate category-based newsletters, manage the subscriber database, and provide an administrative interface for content management and analytics.

## 2. User Roles

* **User:** Manages personal subscriptions to specific thematic newsletters.
* **Administrator:** Has full access to category management, mass broadcasts, and system logs.

## 3. Functional Requirements

### 3.1 Subscription System (Multi-category)

* The bot supports multiple independent newsletter categories.
* Users manage subscriptions via an interactive menu (Inline buttons with "selected/unselected" states).
* **Save Mode:** Changes take effect only after clicking the "Save" button to minimize database queries.

### 3.2 Category Management (Admin Panel)

Administrators can perform full **CRUD** operations:

* **Create:** Add a new newsletter (Name + Description with HTML formatting support).
* **Edit:** Modify the name or description of an existing category.
* **Delete:** Remove a newsletter category and automatically clear all associated user subscriptions.

### 3.3 Mass Broadcasting

* **Type:** Global notifications to all active bot users.
* **Formatting:** Support for all Telegram entities (Bold, Italic, Links, Spoilers) via the `copy_to` method.
* **Fault Tolerance:** Asynchronous delivery with Flood Limit handling and automatic skipping of blocked users.

### 3.4 Statistics

Real-time data visualization via RPC queries:

* Total number of unique users in the system.
* **Subscribers per Category:** A detailed list of all newsletters with the exact subscriber count for each.

## 4. Technical and Non-Functional Requirements

### 4.1 Data Architecture (Supabase)

* **RPC (Remote Procedure Calls):** Complex logic (bulk subscription updates, statistics aggregation) is handled on the database side to increase performance.
* **Integrity:** Use of `bigint` for Telegram IDs and `text` for content.
* **Atomicity:** Bulk operations (category deletion, subscription list updates) are executed within SQL transactions.

### 4.2 Performance and Caching

* **Async I/O:** Use of `asyncio.to_thread` to move blocking synchronous Supabase requests to separate threads.
* **Caching:** Implementation of a thread-safe TTL cache (`cachetools`) for category lists and descriptions to reduce DB load and improve response times.

### 4.3 Security

* **Access:** Admin rights verification via a hardcoded list of IDs (`ADMIN_IDS`) at the router filter level.
* **Validation:** Protection against HTML parsing errors when an administrator enters invalid tags.

## 5. Logging and Audit

The bot maintains a structured log (Standard Logging) with module naming:

* **Info Logs:** Bot startup, configuration loading, DB query execution.
* **Admin Audit Trail:**
* Timestamp and author of category creation/editing (Old value -> New value).
* Timestamp and author of category deletion.
* Start and result of mass broadcasts (delivered vs. blocked).


* **Errors:** Detailed descriptions of exceptions occurring during Telegram API or Supabase interactions.

## 6. Interface (Commands and Menu)

| Command | Access | Description |
| --- | --- | --- |
| `/start` | Public | Greeting and transition to the main menu |
| `/info` | Public | Project information and newsletter catalog |
| `/admin` | Admins | Access to the control panel |

### Admin Menu (Inline):

* 🆕 **Broadcast to All:** Triggers FSM to collect text and start the mailing process.
* 📊 **Statistics:** Instant display of user and subscription data.
* ➕ **Add Newsletter:** Create a new category.
* 📝 **Edit Newsletter:** Select from a list to modify or delete.
* 📋 **User Menu:** Quick switch to preview mode as a regular user