# Tauri + Rust Migration Plan for Weather Checker

## Executive Summary

**Feasibility: YES - Fully achievable with Tauri + Rust**

The current Docker-based Python weather checker can be migrated to a Tauri + Rust desktop application. This will provide:
- Lightweight native application (vs Docker container)
- Cross-platform support (Windows/Mac/Linux)
- Optional GUI for configuration and monitoring
- Lower resource consumption
- Easier distribution and installation for end users

## Current Architecture Analysis

### Python Components
1. **scheduler.py** - Main entry point with cron-like scheduling
2. **JMAFeed.py** - Fetches and parses JMA XML feeds
3. **weather.py** - Core logic for comparing warnings and triggering notifications
4. **weather_DB.py** - Database operations (SQLite)
5. **gmail.py** - Email notification handler
6. **remove_data.py** - Data cleanup tasks

### Dependencies
- pytz, requests, schedule, SQLAlchemy, xmltodict
- Docker for deployment

## Proposed Tauri + Rust Architecture

### Architecture Option A: Background Service (Recommended)

```
Tauri Application
├── Backend (Rust)
│   ├── main.rs - Application entry point
│   ├── scheduler.rs - Periodic task management
│   ├── jma_feed.rs - JMA XML fetching and parsing
│   ├── weather_checker.rs - Core warning comparison logic
│   ├── database.rs - SQLite operations
│   ├── notification.rs - Email/system notification
│   └── cleanup.rs - Data maintenance
└── Frontend (Optional)
    ├── System tray icon
    ├── Settings UI (monitored regions, email config)
    ├── Log viewer
    └── Notification history
```

**Deployment:**
- Single executable binary
- Runs in system tray
- Auto-start on system boot
- No Docker required

### Architecture Option B: Desktop Application

Same as Option A but with full-featured GUI:
- Dashboard showing current warnings
- Interactive map (optional)
- Rich notification settings
- Real-time log streaming

## Technology Mapping

### Core Libraries

| Python Library | Rust Equivalent | Purpose |
|----------------|-----------------|---------|
| schedule | tokio-cron-scheduler | Periodic task scheduling |
| requests | reqwest | HTTP client with async support |
| xmltodict | quick-xml / serde-xml-rs | XML parsing and serialization |
| SQLAlchemy | diesel / sqlx | ORM and database operations |
| smtplib | lettre | SMTP email client |
| python-dotenv | dotenvy | Environment variable management |
| logging | tracing / env_logger | Structured logging |
| - | tauri | Desktop application framework |

### Cargo Dependencies (Cargo.toml)

```toml
[dependencies]
# Tauri framework
tauri = { version = "2.0", features = ["system-tray"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Async runtime
tokio = { version = "1", features = ["full"] }
tokio-cron-scheduler = "0.10"

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# XML parsing
quick-xml = "0.31"
serde-xml-rs = "0.6"

# Database
sqlx = { version = "0.7", features = ["sqlite", "runtime-tokio-rustls"] }
# OR
diesel = { version = "2.1", features = ["sqlite"] }

# Email
lettre = "0.11"

# Configuration
dotenvy = "0.15"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Time handling
chrono = "0.4"
```

## Implementation Roadmap

### Phase 1: Core Backend (No GUI)
**Goal:** Replicate all Python functionality in Rust

1. **Project Setup**
   ```bash
   npm create tauri-app@latest
   # Choose: Rust + No frontend (or minimal HTML)
   ```

2. **Database Layer** (`src-tauri/src/database.rs`)
   - Define schema matching current SQLite tables
   - Implement CRUD operations for CityReport, VPWW54xml, Extra
   - Migration from existing Python DB (if needed)

3. **JMA Feed Client** (`src-tauri/src/jma_feed.rs`)
   - HTTP client with If-Modified-Since header support
   - XML download and caching
   - Parse VPWW54 format
   - Extract warning data for specified cities

4. **Weather Checker** (`src-tauri/src/weather_checker.rs`)
   - Compare new warnings with database state
   - Detect status changes (発表/継続/解除)
   - Trigger notifications on changes

5. **Email Notification** (`src-tauri/src/notification.rs`)
   - Gmail SMTP integration with app password
   - Format warning messages
   - HTML email template

6. **Scheduler** (`src-tauri/src/scheduler.rs`)
   - Initialize database on startup
   - Schedule weather check every 10 minutes
   - Schedule cleanup daily at 01:00
   - Graceful shutdown handling

7. **Data Cleanup** (`src-tauri/src/cleanup.rs`)
   - Delete old XML files (30+ days)
   - Remove soft-deleted DB records (30+ days)

### Phase 2: System Integration
**Goal:** Make it run seamlessly in background

1. **System Tray Icon**
   - Show current status
   - Menu: Start/Stop monitoring, View logs, Settings, Quit

2. **Auto-start on Boot**
   - Platform-specific configuration
   - Windows: Registry/Task Scheduler
   - macOS: LaunchAgent
   - Linux: systemd service

3. **Configuration Management**
   - Read from `.env` or config file
   - Store settings in app data directory

### Phase 3: GUI (Optional)
**Goal:** User-friendly configuration and monitoring

1. **Settings Screen**
   - Email configuration (Gmail credentials)
   - Add/remove monitored regions
   - Notification preferences

2. **Dashboard**
   - Current active warnings
   - Last check timestamp
   - Status indicators

3. **Log Viewer**
   - Real-time log streaming
   - Filter by level/component

4. **Notification History**
   - List of past notifications
   - Detail view with full warning text

## Code Examples

### Example: Scheduler Implementation

```rust
// src-tauri/src/scheduler.rs
use tokio_cron_scheduler::{JobScheduler, Job};
use std::time::Duration;

pub async fn start_scheduler() -> Result<(), Box<dyn std::error::Error>> {
    let scheduler = JobScheduler::new().await?;

    // Weather check every 10 minutes
    let weather_job = Job::new_async("0 */10 * * * *", |_uuid, _lock| {
        Box::pin(async {
            if let Err(e) = crate::weather_checker::run_weather_check().await {
                tracing::error!("Weather check failed: {}", e);
            }
        })
    })?;
    scheduler.add(weather_job).await?;

    // Daily cleanup at 01:00
    let cleanup_job = Job::new_async("0 0 1 * * *", |_uuid, _lock| {
        Box::pin(async {
            if let Err(e) = crate::cleanup::cleanup_old_data().await {
                tracing::error!("Cleanup failed: {}", e);
            }
        })
    })?;
    scheduler.add(cleanup_job).await?;

    scheduler.start().await?;

    // Keep scheduler alive
    tokio::time::sleep(Duration::from_secs(u64::MAX)).await;
    Ok(())
}
```

### Example: JMA Feed Client

```rust
// src-tauri/src/jma_feed.rs
use reqwest::Client;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct JMAFeed {
    client: Client,
}

impl JMAFeed {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
        }
    }

    pub async fn fetch_extra_xml(&self) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        let url = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml";

        let response = self.client
            .get(url)
            .header("If-Modified-Since", self.get_last_modified()?)
            .send()
            .await?;

        if response.status() == 304 {
            return Ok(vec![]); // Not modified
        }

        Ok(response.bytes().await?.to_vec())
    }

    pub async fn parse_vpww54(&self, xml_content: &str) -> Result<WarningData, Box<dyn std::error::Error>> {
        // Use quick-xml or serde-xml-rs to parse
        // Extract warning information
        todo!()
    }
}
```

### Example: Database with sqlx

```rust
// src-tauri/src/database.rs
use sqlx::{SqlitePool, FromRow};
use chrono::{DateTime, Utc};

#[derive(Debug, FromRow)]
pub struct CityReport {
    pub id: i64,
    pub xml_file: String,
    pub lmo: String,
    pub city: String,
    pub warning_kind: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub is_delete: bool,
}

pub struct Database {
    pool: SqlitePool,
}

impl Database {
    pub async fn new(db_path: &str) -> Result<Self, sqlx::Error> {
        let pool = SqlitePool::connect(db_path).await?;
        Ok(Self { pool })
    }

    pub async fn get_city_report(
        &self,
        city: &str,
        warning_kind: &str,
    ) -> Result<Option<CityReport>, sqlx::Error> {
        sqlx::query_as::<_, CityReport>(
            "SELECT * FROM city_report WHERE city = ? AND warning_kind = ? AND is_delete = 0"
        )
        .bind(city)
        .bind(warning_kind)
        .fetch_optional(&self.pool)
        .await
    }

    pub async fn create_city_report(&self, report: &CityReport) -> Result<(), sqlx::Error> {
        sqlx::query(
            "INSERT INTO city_report (xml_file, lmo, city, warning_kind, status) VALUES (?, ?, ?, ?, ?)"
        )
        .bind(&report.xml_file)
        .bind(&report.lmo)
        .bind(&report.city)
        .bind(&report.warning_kind)
        .bind(&report.status)
        .execute(&self.pool)
        .await?;
        Ok(())
    }
}
```

### Example: Email Notification

```rust
// src-tauri/src/notification.rs
use lettre::{Message, SmtpTransport, Transport};
use lettre::message::header::ContentType;
use lettre::transport::smtp::authentication::Credentials;

pub struct EmailNotifier {
    smtp_username: String,
    smtp_password: String,
    from: String,
    to: String,
    bcc: Option<String>,
}

impl EmailNotifier {
    pub fn new(from: String, password: String, to: String, bcc: Option<String>) -> Self {
        Self {
            smtp_username: from.clone(),
            smtp_password: password,
            from,
            to,
            bcc,
        }
    }

    pub async fn send_warning_notification(
        &self,
        city: &str,
        warning_kind: &str,
        status: &str,
        lmo_url: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let subject = format!("[気象警報] {} - {}", city, warning_kind);
        let body = format!(
            "【{}】\n\n種別: {}\n状態: {}\n\n詳細: {}",
            city, warning_kind, status, lmo_url
        );

        let mut email_builder = Message::builder()
            .from(self.from.parse()?)
            .to(self.to.parse()?)
            .subject(subject);

        if let Some(bcc) = &self.bcc {
            email_builder = email_builder.bcc(bcc.parse()?);
        }

        let email = email_builder
            .header(ContentType::TEXT_PLAIN)
            .body(body)?;

        let creds = Credentials::new(
            self.smtp_username.clone(),
            self.smtp_password.clone(),
        );

        let mailer = SmtpTransport::relay("smtp.gmail.com")?
            .credentials(creds)
            .build();

        mailer.send(&email)?;
        Ok(())
    }
}
```

## Advantages of Tauri + Rust

### Performance
- **Memory:** ~10-50MB (vs ~100-200MB for Docker Python)
- **CPU:** Minimal idle usage, efficient async I/O
- **Startup:** <1 second (vs several seconds for Docker)

### Distribution
- **Single binary:** No Python/Docker installation required
- **Size:** ~5-15MB (vs ~500MB Docker image)
- **Updates:** Built-in auto-update with Tauri

### User Experience
- **Native feel:** System tray integration
- **Offline config:** No need to edit .env files
- **Visibility:** Optional GUI for monitoring

### Security
- **Sandboxed:** Tauri security model
- **No exposed ports:** Unlike Docker container
- **Credential management:** OS keychain integration possible

## Challenges and Solutions

### Challenge 1: XML Parsing Complexity
**Problem:** VPWW54 format may have nested structures
**Solution:** Use `serde` derive macros for automatic deserialization, similar to Python's xmltodict

### Challenge 2: Async Scheduler
**Problem:** Rust async requires more setup than Python's `schedule`
**Solution:** `tokio-cron-scheduler` provides similar API with better performance

### Challenge 3: Database Migration
**Problem:** Existing SQLite database from Python
**Solution:** Schema is compatible; just point Rust app to same DB file

### Challenge 4: Gmail SMTP
**Problem:** OAuth2 vs app password
**Solution:** Use `lettre` with app password (same as Python implementation)

### Challenge 5: Learning Curve
**Problem:** Rust is more complex than Python
**Solution:** Gradual migration; start with core logic, add features iteratively

## Migration Strategy

### Option 1: Clean Rewrite (Recommended)
- Build Tauri app from scratch
- Test in parallel with Docker version
- Migrate database when stable
- Decommission Docker

### Option 2: Gradual Migration
- Keep Docker running
- Build Tauri app incrementally
- Share SQLite database between both
- Disable Python scheduler when Tauri is ready

### Option 3: Hybrid Approach
- Use Tauri for GUI only
- Keep Python backend (via PyO3 bindings)
- **Not recommended** - loses main benefits

## Recommended Choice: Option 1 (Clean Rewrite)

**Timeline Estimate:**
- Phase 1 (Core backend): Main implementation effort
- Phase 2 (System integration): Additional integration work
- Phase 3 (GUI): Optional enhancement phase

**Skills Required:**
- Rust basics (ownership, async/await)
- Tauri fundamentals
- SQLite knowledge (transferable from Python)

## Conclusion

**Tauri + Rust migration is highly feasible and recommended** for this weather checker application.

**Key Benefits:**
1. Lightweight native application
2. No Docker dependency
3. Better resource efficiency
4. Cross-platform support
5. Optional modern GUI
6. Easier distribution to end users

**Recommended Next Steps:**
1. Set up Tauri project skeleton
2. Implement database layer with existing schema
3. Port JMA feed fetching and parsing
4. Implement notification logic
5. Add scheduler
6. Test in parallel with existing Docker version
7. Add system tray and GUI (optional)

The core functionality maps cleanly from Python to Rust, with mature ecosystem libraries available for all required features.
