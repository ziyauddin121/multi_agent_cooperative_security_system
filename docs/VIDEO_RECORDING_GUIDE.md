# Step-by-Step Video Recording Guide
### Multi-Agent Cooperative Security System (MACSS)

---

## 🎥 1. How to Record Your Screen on Windows

You do **NOT** need to install any external recorder. Use any of these easy options:

### Option A: Windows Built-in Screen Recorder (Recommended & Easiest)
1. Open your browser to `http://localhost:3000`.
2. Press **`Win + Alt + R`** on your keyboard to immediately start recording your screen.
   *(Or press `Win + G` to open Xbox Game Bar and click the Record button).*
3. A small recording timer will appear in the top-right corner.
4. When finished, press **`Win + Alt + R`** again to stop.
5. Your MP4 video is automatically saved in your **`Videos\Captures`** folder!

### Option B: PowerPoint Screen Recording
1. Open PowerPoint $\rightarrow$ Blank Presentation.
2. Click **Insert** $\rightarrow$ **Screen Recording**.
3. Select your screen area and click **Record**.
4. When finished, press `Win + Shift + Q`. Right-click the video slide $\rightarrow$ **Save Media As...** $\rightarrow$ MP4 file.

---

## 📋 2. Pre-Recording Checklist (Do This Before Pressing Record)

Before you hit record, make sure everything is ready on your screen:

1. **Start the containers** (if not already running):
   ```powershell
   docker compose up -d
   ```
2. **Open your browser tabs**:
   - Tab 1: **`http://localhost:3000`** (Frontend Dashboard)
   - Tab 2: **`http://localhost:8000/docs`** (FastAPI Swagger API)
3. **Clean the screen**:
   - Press **`F11`** in Chrome/Edge if you want clean full-screen mode, or maximize the window.
   - Close WhatsApp, Discord, or personal tabs.
4. **Click `Reset State` on the Overview page once** before recording, so the counters start fresh at zero.

---

## 🎬 3. Scene-by-Scene Video Walkthrough (3 to 5 Minutes Total)

Follow this exact scene flow while recording:

---

### ⏱️ Scene 1: Introduction & Architecture (0:00 - 0:45)
- **On Screen:** Start on `http://localhost:3000` (Overview page).
- **What to Click:**
  1. Show the clean layout: Sidebar on the left, Dashboard on the right.
  2. Point your cursor to the top header: click **`Horizontal (Option 2)`**, wait 2 seconds to show how the top navbar renders, then click **`Sidebar (Option 1)`** to show flexibility.
  3. Point to the top-right pill: **`API: Connected`**.
  4. Click **`Agent Status`** in the left menu.
- **What to Say:**
  > *"Hello everyone. Today I am demonstrating my MCA final year project: the **Multi-Agent Cooperative Security System (MACSS)**.  
  > In this project, we have four autonomous software agents operating over a shared Redis blackboard.  
  > Here in the Agent Status view, you can see all microservice agents running: Perimeter Agent, Endpoint Agent, Forensics Agent, Coordinator Agent, and our Single-Agent Baseline comparator. Each agent publishes live heartbeats every 3 seconds."*

---

### ⏱️ Scene 2: Launching the Mixed Attack Campaign (0:45 - 2:00)
- **On Screen:** Go to `Overview` or `Attack Simulator`.
- **What to Click:**
  1. Click the blue button: **`Launch Mixed Campaign`**.
  2. Watch the blue status banner update.
  3. While it runs, click **`Event Stream`** in the sidebar to show raw events coming in.
  4. Click **`Incidents & Alerts`** to show the alerts being generated.
- **What to Say:**
  > *"Now, I will launch our synthetic mixed attack campaign.  
  > In real life, attackers launch two attacks at once: a fake volumetric DDoS flood at the perimeter to distract defenders, while secretly executing ransomware on internal database servers.  
  > As you can see, our simulator is orchestrating 4 stages:  
  > 1. Stage 1: Port scan reconnaissance.  
  > 2. Stage 2: Volumetric DDoS flood targeting the web server.  
  > 3. Stage 3: Covert ransomware trying to lock files on database `db-prod-01`.  
  > 4. Stage 4: Lateral movement to domain controller `dc-core-01`.  
  > In the Event Stream, you can see synthetic sensor events being published to Redis in real time."*

---

### ⏱️ Scene 3: The Core Innovation — Conflict Resolution (2:00 - 3:00)
- **On Screen:** Click **`Conflict Resolution`** in the left sidebar.
- **What to Click:**
  1. Hover your mouse over the conflict table and decision breakdown.
  2. Highlight the two competing agent recommendations:
     - `perimeter-agent` recommended `RATE_LIMIT`.
     - `endpoint-agent` recommended `ISOLATE_ENDPOINT`.
  3. Point out the winner: `ISOLATE_ENDPOINT` with utility score **0.835**.
- **What to Say:**
  > *"This is the core innovation of our project: **Autonomous Conflict Resolution**.  
  > During this blended attack, two agents recommended opposing actions: the Perimeter Agent wanted to rate-limit the gateway, while the Endpoint Agent wanted to immediately isolate the database computer.  
  > In old systems, this causes deadlock or the wrong action gets picked.  
  > In MACSS, our Coordinator Agent uses a mathematical **Multi-Criteria Decision Analysis (MCDA)** formula:  
  > It scored database isolation at 0.835, and rate-limiting at 0.625.  
  > Because protecting enterprise data is more critical than perimeter throughput, the Coordinator decisively chose to isolate the database, completely preventing ransomware encryption and lateral spread."*

---

### ⏱️ Scene 4: Baseline Comparison & Research Results (3:00 - 4:00)
- **On Screen:** Click **`Baseline Compare`** in the left sidebar.
- **What to Click:**
  1. Hover over the large comparative metric cards:
     - **Containment Time**: 411.5 ms vs 1151.7 ms.
     - **Blast Radius**: 1.2 hosts vs 3.2 hosts.
     - **Decision Consistency**: 95.2% vs 72.5%.
  2. Click **`Batch Experiments`** to show the Matplotlib comparison graphs.
- **What to Say:**
  > *"To validate our research, we evaluated MACSS against an industry-standard monolithic single-agent baseline across repeated trials:  
  > 1. **Containment Time**: MACSS contained the attack in **411 milliseconds**, compared to **1151 milliseconds** for the baseline — a **64.3% speedup**. The baseline was delayed because thousands of DDoS flood packets caused head-of-line blocking in its single event queue.  
  > 2. **Blast Radius**: MACSS limited damage to **1.2 hosts**, while the baseline allowed 3.2 hosts to get compromised — a **62.5% reduction in compromised systems**.  
  > 3. **Decision Consistency**: MACSS achieved **95.2%** policy consistency compared to 72.5% for the baseline."*

---

### ⏱️ Scene 5: API Documentation & Automated Tests (4:00 - 4:45)
- **On Screen:**
  1. Switch to the browser tab: `http://localhost:8000/docs`.
  2. Scroll through the endpoints (`/api/agents`, `/api/alerts`, `/api/decisions`, `/api/metrics`, `/api/experiments/results`).
  3. (Optional) Open PowerShell and run:
     ```powershell
     docker exec macss-backend pytest tests/ -v
     ```
     Show that **17 out of 17 tests pass in 1.4 seconds**.
- **What to Say:**
  > *"Behind the UI, our FastAPI backend exposes a fully documented REST and WebSocket API.  
  > In addition, our entire system has a comprehensive unit and integration test suite with 17 automated tests covering message schemas, blackboard consumer groups, and conflict resolution logic.  
  > All 17 tests pass in under 1.5 seconds.  
  > The system is 100% offline, requires no external paid APIs, and runs completely in Docker. Thank you."*
- **Action:** Stop recording (`Win + Alt + R`).

---

## 🔍 4. All Possibilities & "What If" Checklist

| What if this happens? | How to handle it easily: |
|---|---|
| **You want to re-record from scratch?** | Click **`Reset State`** (red button on Overview), wait 2 seconds, and click **`Launch Mixed Campaign`** again. Everything resets cleanly. |
| **Docker containers are stopped?** | Run `docker compose up -d` in PowerShell. All 10 containers start in ~10 seconds. |
| **You want to show your webcam face while recording?** | Use OBS Studio or PowerPoint Screen Recording with camera enabled, or record screen-only (standard for software project demonstrations). |
| **Audio recording tip:** | Speak clearly, use simple English words, and keep your microphone close. Avoid background noise. |
| **Video resolution:** | Record in 1080p (1920x1080) for crisp text readability. |

---

## 📁 5. Where Your Files Are Stored

- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Generated Research Charts**: `c:\Users\ziyau\Desktop\endlab\results\`
- **Project Report**: `c:\Users\ziyau\Desktop\endlab\docs\ACADEMIC_PROJECT_REPORT.md`
- **Simple Evaluation Notes**: `c:\Users\ziyau\Desktop\endlab\docs\EVALUATION_GUIDE_AND_METHODOLOGY.md`
