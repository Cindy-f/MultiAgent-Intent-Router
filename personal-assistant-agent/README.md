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

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.