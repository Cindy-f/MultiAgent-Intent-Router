# Personal Assistant Agent

This project is a personal assistant agent that integrates with Google services to manage emails and calendar events. It utilizes OAuth for authentication and provides functionalities to check unread emails, fetch today's calendar schedule, and retrieve the current time.

## Project Structure

```
personal-assistant-agent
├── src
│   ├── app.ts                  # Entry point of the application
│   ├── agents
│   │   └── assistant.ts        # Contains the AssistantAgent class
│   ├── tools
│   │   ├── GetUnreadEmails.ts  # Function to retrieve unread emails
│   │   ├── FetchDailyMeetingSchedule.ts # Function to fetch today's meeting schedule
│   │   └── GetCurrentTime.ts   # Function to get the current time
│   ├── services
│   │   └── GoogleServicesUtils.ts # Handles OAuth authentication
│   ├── utils
│   │   └── tokenManager.ts      # Manages token storage and retrieval
│   └── types
│       └── index.ts            # Type definitions for the project
├── .env.example                 # Example environment variables
├── package.json                 # npm configuration file
├── tsconfig.json                # TypeScript configuration file
└── README.md                    # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd personal-assistant-agent
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in the required API keys and OAuth credentials.

4. **Run the application:**
   ```
   npm start
   ```

## Usage

- The personal assistant agent will authenticate using Google OAuth and save the token in `token.json`.
- You can check unread emails, fetch today's calendar schedule, and get the current time using the methods provided in the `AssistantAgent` class.

## Quick repo snapshot (merged & updated)

This repo contains a TypeScript "personal-assistant-agent" app under personal-assistant-agent/ that:
- Uses Google OAuth2 and googleapis to read Gmail, read Calendar events, and return current time.
- Main artefacts:
  - personal-assistant-agent/src/app.ts — example CLI orchestration / entry point
  - personal-assistant-agent/src/agents/assistant.ts — AssistantAgent wrapper
  - personal-assistant-agent/src/services/GoogleServicesUtils.ts — OAuth client, token exchange, save/load
  - personal-assistant-agent/src/tools/{GetUnreadEmails.ts,FetchDailyMeetingSchedule.ts,GetCurrentTime.ts}
  - personal-assistant-agent/src/utils/tokenManager.ts — token persistence helpers
  - personal-assistant-agent/.env.example — required env vars
  - personal-assistant-agent/package.json & tsconfig.json

## First steps (always)
1. From repo root list files:
   - ls -la
   - tree -L 2
2. Inspect the app folder:
   - cd personal-assistant-agent
   - cat package.json
3. If package.json exists, run the health flow:
   - npm install
   - npx tsc --noEmit

Do not run commands outside the detected language/manifest.

## How to run & test (explicit)
- Prepare env (.env) using personal-assistant-agent/.env.example with:
  - CLIENT_ID, CLIENT_SECRET, REDIRECT_URI (or urn:ietf:wg:oauth:2.0:oob), TOKEN_PATH (token.json)
- Local smoke flow (from personal-assistant-agent/):
  - npm install
  - npx tsc --noEmit
  - npm start            # prints OAuth URL first run
  - open "<printed-url>" # complete consent; paste code if app prompts
  - ls -la token.json
- Quick one-liners (assumes token.json exists):
  - Check unread emails:
    npx ts-node -e "import 'dotenv/config'; import { AssistantAgent } from './src/agents/assistant'; (async ()=>{ const a=new AssistantAgent(); await a.authenticate(); console.log(await a.checkUnreadEmails(5)); })()"
  - Fetch today's schedule:
    npx ts-node -e "import 'dotenv/config'; import { AssistantAgent } from './src/agents/assistant'; (async ()=>{ const a=new AssistantAgent(); await a.authenticate(); console.log(await a.fetchDailyMeetingSchedule(new Date().toISOString().split('T')[0])); })()"
  - Get current time:
    npx ts-node -e "import 'dotenv/config'; import { AssistantAgent } from './src/agents/assistant'; (async ()=>{ const a=new AssistantAgent(); console.log(await a.getCurrentTime()); })()"

## Repository-specific patterns & gotchas
- Google OAuth client is constructed in GoogleServicesUtils.ts — ensure use of google.auth.OAuth2 (or new (google.auth as any).OAuth2(...)) and setCredentials expects { access_token, refresh_token, expiry_date (ms) }.
- Tools accept an authenticated OAuth2 client; assistant.ts passes googleServices.oauth2Client into tools.
- TOKEN persistence uses token.json (add to .gitignore). Do not commit .env or token.json.
- Type checks are required: run npx tsc --noEmit before running to catch signature mismatches (common with google-auth types).

## When to ask the user (minimal prompts)
- "Confirm where source lives if not in personal-assistant-agent/ or if you want a different root."
- "Do you prefer an automated OAuth redirect (localhost) or manual code paste (urn:ietf:wg:oauth:2.0:oob)?"
- "Share personal_assistant_agent/src/services/GoogleServicesUtils.ts if token exchange/auto-save needs fixing."

## PR / commit guidance for agents
- Create small focused commits; keep .env/token.json ignored.
- Run npx tsc --noEmit and npm start locally before pushing changes.
- If adding docs, follow .cursorrules style (code-first snippets, Mintlify components where used).


If anything above is out-of-date, paste ls -la or tree output for the repo root and I
<img width="1579" height="1001" alt="Screenshot 2026-05-16 at 4 28 07 PM" src="https://github.com/user-attachments/assets/8e9292ea-e224-48f5-9671-0955d573f0ef" />

