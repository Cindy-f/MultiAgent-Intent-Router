# Personal Assistant Agent

This project is a personal assistant agent that integrates with Google services to manage emails and calendar events. It utilizes Google OAuth for authentication and provides functionalities to read and summarize emails, fetch today's calendar schedule, and retrieve the current time. 


## Project Structure

```
personal-assistant-agent
├── src
│   ├── app.ts                  # Orchestration entry point & Terminal UI dashboard execution
│   ├── agents
│   │   └── assistant.ts        # Agent abstraction boundary wrapper
│   ├── services
│   │   └── GoogleServicesUtils.ts # Google OAuth2 client initialization & auth flows
│   ├── tools
│   │   ├── GetUnreadEmails.ts  # Fetches & maps raw message payloads to human-readable objects
│   │   ├── FetchDailyMeetingSchedule.ts # Filters and parses the daily timeline array
│   │   └── GetCurrentTime.ts   # System synchronization clock utility
│   ├── utils
│   │   └── tokenManager.ts     # Reads/Writes cached token blocks to disk
│   └── types
│       └── index.ts            # Centralized project type definitions
├── .env.example                 # Distributed template environment file
├── tsconfig.json                # Strict TypeScript compilation parameters
└── package.json                 # Core dependencies (googleapis, chalk, cli-table3)
```

## Setup Instructions

1. **Clone the repository and install the dependencies:**
   ```
   git clone [https://github.com/Cindy-f/Cursor-Agent.git](https://github.com/Cindy-f/Cursor-Agent.git)
   cd personal-assistant-agent
   npm install
   ```

2. **Hydrate Environment Variables:**
   ```
   CLIENT_ID=your_google_client_id.apps.googleusercontent.com
   CLIENT_SECRET=your_google_client_secret
   REDIRECT_URI=http://localhost:8080
   ```
   
3. **Run the application:**
   ```
   npm start
   ```

## 🔒 License

Copyright (c) 2026 Cindy Fan. All rights reserved. 

This software and its associated documentation files are proprietary and confidential. Unauthorized copying, transfer, modification, or distribution of this file, via any medium, is strictly prohibited.