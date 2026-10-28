# Easy Project Guide & Evaluation Notes (Simple English)
### Multi-Agent Cooperative Security System (MACSS)

---

## 1. What is this Project in Simple Words?

Imagine a bank:
- A gang of thieves sends a big noisy crowd to the front gate to make noise and distract the guards (this is like a **DDoS attack**).
- While all the guards run to the front gate, one thief sneaks in through the back window to steal the money vault (this is like **Ransomware**).

**The Problem with Old Systems:**
Old security systems have only **one guard** (a single program). The single guard gets stuck counting the noisy crowd at the front gate. By the time he looks at the vault, the money is already stolen.

**Our Solution (MACSS):**
Instead of just one guard, we have a **team of 4 specialized guards (called Agents)** working together. Each guard has one job, and they talk to each other through a shared notice board (**Redis**):
1. **Perimeter Agent**: Watches the front gate (Network traffic).
2. **Endpoint Agent**: Watches the computers and files inside (Stops Ransomware).
3. **Forensics Agent**: The detective. Tells the team: *"The front gate noise is just a distraction! Protect the database first!"*
4. **Coordinator Agent**: The team leader. Decides the best action to take so nobody gets confused.

**Our Result:**
Our multi-agent system stops attacks **64% faster** and saves **62% more computers** than the old single-guard system.

---

## 2. The 4 Agents (Team Members)

| Agent Name | Simple Role | What it Watches | What it Does |
|---|---|---|---|
| **Perimeter Agent** | Front Gate Guard | Incoming network traffic | Catches port scans and stops fake traffic floods (DDoS). |
| **Endpoint Agent** | Inside Guard | Files and programs on computers | Catches ransomware if files are changing too fast, and stops it. |
| **Forensics Agent** | Detective | Clues from both network and computers | Connects the dots. Sees that the DDoS is a trick to hide the ransomware. |
| **Coordinator Agent** | Team Leader / Boss | Solves disagreements between agents | Uses a simple math score to pick the best and safest defense action. |
| **Baseline Agent** | Old Single Guard (For comparison) | Tries to do everything alone | Gets overloaded and slow when a big attack happens. |

---

## 3. How the Agents Talk (The Notice Board)

We use **Redis** as a shared **Blackboard** (Notice Board).
- When the Perimeter Agent sees strange traffic, it writes a note on the board: *"Warning: Traffic spike at the gate!"*
- When the Endpoint Agent sees files being locked, it writes: *"Warning: Database computer is under attack!"*
- The Forensics Agent reads both notes, connects them, and writes: *"Alert: This is a double attack! The real target is the database!"*
- The Coordinator reads the notes and writes the final order: *"Action: Disconnect the database computer from the network now to save data!"*

All of this happens in **less than 1 millisecond** because Redis keeps everything in fast computer memory.

---

## 4. How the Boss Solves Conflicts (Simple Math)

Sometimes two agents want to do different things at the same time:
- **Perimeter Agent says:** *"Slow down the internet router."*
- **Endpoint Agent says:** *"Disconnect the database computer immediately."*

Who should the boss listen to?
The Coordinator calculates a simple score for each option:

$$\text{Score} = (\text{Danger Level} \times 0.40) + (\text{Certainty} \times 0.30) + (\text{Clues} \times 0.20) - (\text{Disruption Penalty} \times 0.10)$$

- **Danger Level (0.40):** How bad is the attack? (Ransomware destroying files is high danger = 1.0).
- **Certainty (0.30):** How sure is the agent? (95% sure = 0.95).
- **Clues (0.20):** Did the detective find proof? (Yes = 1.0).
- **Disruption Penalty (0.10):** Does this action shut down services?

**The Result:**
- Disconnecting the infected computer gets a score of **0.835**.
- Just slowing down the router gets a score of **0.625**.
- Because **0.835 is higher**, the Coordinator picks **Disconnect the infected computer**. This saves the database from being destroyed.

---

## 5. Exactly What to Say to Your Guide Tomorrow

Memorize or read these simple lines:

> *"Good morning, Sir / Ma'am.*
>
> *My project is called **MACSS: Multi-Agent Cooperative Security System**.*
>
> *In real life, hackers launch two attacks together: a fake flood attack at the front door to distract everyone, while secretly putting ransomware on internal computers.*
>
> *Old single-agent security tools fail because they get overwhelmed reading all the fake packets, so they don't stop the ransomware in time.*
>
> *In my project, I created a team of 4 specialized software agents:*
> *1. A Perimeter Agent to watch the network.*
> *2. An Endpoint Agent to watch the files.*
> *3. A Forensics Agent to connect clues.*
> *4. A Coordinator Agent to make the final decision.*
>
> *They talk using Redis as a fast in-memory notice board.*
>
> *When we tested our system against an old single-agent system, our system stopped the attack **64% faster** and protected **62% more computers**.*
>
> *I have the project running live on my laptop. Let me show you how it works."*

---

## 6. How to Show the Working Project (Click by Click)

Follow these 5 easy steps on your laptop:

### Step 1: Open the Website
1. Open your browser and go to: `http://localhost:3000`
2. Show your guide:
   - The navigation bar is on the left.
   - The dashboard is on the right.
   - Top right corner shows: **`API: Connected`** (Green dot means system is healthy).

### Step 2: Show the Agents
1. Click **`Agent Status`** in the left menu.
2. Tell your guide:
   - *"Here you can see our agents running: perimeter, endpoint, forensics, coordinator, and baseline."*

### Step 3: Start the Attack Simulation
1. Click **`Overview`** in the left menu.
2. Click the big blue button: **`Launch Mixed Campaign`**.
3. Point to the screen as the blue banner updates:
   - *"Sir, now the simulator is sending the attacks:"*
   - *"First, a port scan."*
   - *"Second, a big flood attack (DDoS)."*
   - *"Third, ransomware trying to lock files on `db-prod-01`."*
   - *"Fourth, trying to spread to other computers."*

### Step 4: Show the Conflict Resolution
1. Click **`Conflict Resolution`** in the left menu.
2. Tell your guide:
   - *"Look here: the perimeter guard wanted to rate-limit the router, but the endpoint guard wanted to isolate the database. The Coordinator used our math formula to pick the database isolation because saving data has higher priority."*

### Step 5: Show the Results & Speedup
1. Click **`Baseline Compare`** in the left menu.
2. Point to the numbers on the screen:
   - **Containment Time:** Our system took **411 milliseconds**, but the single agent took **1151 milliseconds** (**64% faster!**).
   - **Blast Radius (Damaged Computers):** Our system only had **1.2 computers** affected, while the old system allowed **3.2 computers** to be affected (**62% fewer computers damaged!**).

---

## 7. Simple Answers to Questions Your Guide May Ask

### Question 1: "Why use multiple agents instead of one big program?"
**Simple Answer:**
> *"If one program tries to do everything, it gets stuck when thousands of fake packets come in. With multiple agents, the endpoint agent watches the computers separately and never gets delayed by network flood packets."*

### Question 2: "What is Redis and why did you use it?"
**Simple Answer:**
> *"Redis is a super-fast in-memory database. We use it like a shared notice board where agents read and write messages in less than 1 millisecond."*

### Question 3: "Did you write real ransomware or hack real computers?"
**Simple Answer:**
> *"No, Sir. For safety, we use a simulation. The simulator creates fake event records that look like real attack logs, so no files or real networks are damaged."*

### Question 4: "What does 'Blast Radius' mean?"
**Simple Answer:**
> *"Blast Radius simply means how many computers got infected or damaged. Lower is better. Our system kept it down to 1 computer, while the old system let it spread to 3 computers."*

### Question 5: "What is PostgreSQL used for?"
**Simple Answer:**
> *"Redis is temporary for fast live communication. PostgreSQL is the permanent database where we save all past alerts, decisions, and experiment history forever."*

### Question 6: "What is the role of Docker in this project?"
**Simple Answer:**
> *"Docker runs all 10 parts of our system (the 5 agents, backend, frontend, Redis, and database) in separate, isolated containers so everything starts with one command."*

---

## 8. Quick Commands (Keep in Mind)

- Open Dashboard: `http://localhost:3000`
- Open Backend API Docs: `http://localhost:8000/docs`
- If you need to check containers in terminal:
  ```powershell
  docker ps
  ```
- If asked to show automated tests:
  ```powershell
  docker exec macss-backend pytest tests/ -v
  ```
  *(All 17 tests will pass in 1.4 seconds!)*
