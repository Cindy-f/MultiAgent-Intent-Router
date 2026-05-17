import OpenAI from 'openai';
import { resolveLlmSettings } from '../config/llmConfig';
import { GoogleServicesUtils } from '../services/GoogleServicesUtils';
import { EmailAgent } from './emailAgent';
import { CalendarAgent } from './calendarAgent';
import { TimeAgent } from './timeAgent';
import { localIsoDate } from '../utils/dateUtils';

const GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly',
];

const SYSTEM_PROMPT = `You are a personal assistant with access to the user's Gmail, Google Calendar, and system clock.

Use tools when the user asks about unread email, inbox, messages, calendar, meetings, schedule, or the current time.
Combine multiple tools when a question needs more than one data source (for example, "summarize my morning" may need email and calendar).

When presenting results:
- Be concise and readable.
- For emails, highlight sender and subject.
- For calendar events, show time windows and titles.
- Always call fetch_daily_schedule for calendar questions; never guess.
- fetch_daily_schedule returns { date, timeZone, events }. If events is empty, say no events for that date.
- For "today", omit the date argument so the tool uses the user's local today.`;

const COORDINATOR_TOOLS: OpenAI.Chat.Completions.ChatCompletionTool[] = [
    {
        type: 'function',
        function: {
            name: 'check_unread_emails',
            description: 'Fetch unread emails from the user Gmail inbox.',
            parameters: {
                type: 'object',
                properties: {
                    maxResults: {
                        type: 'number',
                        description: 'Maximum number of emails to return (default 10).',
                    },
                },
            },
        },
    },
    {
        type: 'function',
        function: {
            name: 'fetch_daily_schedule',
            description:
                'Fetch Google Calendar events for one day in the user local timezone. Omit date for today.',
            parameters: {
                type: 'object',
                properties: {
                    date: {
                        type: 'string',
                        description:
                            'Optional. Local calendar date YYYY-MM-DD. Leave empty for today.',
                    },
                },
            },
        },
    },
    {
        type: 'function',
        function: {
            name: 'get_current_time',
            description: 'Get the current system time in ISO format.',
            parameters: {
                type: 'object',
                properties: {},
            },
        },
    },
];

export class LlmCoordinator {
    private readonly openai: OpenAI;
    private readonly model: string;
    readonly llmLabel: string;
    private readonly google: GoogleServicesUtils;
    private readonly emailAgent: EmailAgent;
    private readonly calendarAgent: CalendarAgent;
    private readonly timeAgent: TimeAgent;
    private readonly history: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [];

    constructor() {
        const llm = resolveLlmSettings();
        this.openai = llm.client;
        this.model = llm.model;
        this.llmLabel = `${llm.label} (${llm.model})`;
        this.google = new GoogleServicesUtils(
            process.env.CLIENT_ID || '',
            process.env.CLIENT_SECRET || '',
            process.env.REDIRECT_URI || ''
        );
        this.emailAgent = new EmailAgent(this.google);
        this.calendarAgent = new CalendarAgent(this.google);
        this.timeAgent = new TimeAgent();
    }

    get email() {
        return this.emailAgent;
    }

    get calendar() {
        return this.calendarAgent;
    }

    get time() {
        return this.timeAgent;
    }

    async authenticate(): Promise<void> {
        await this.google.authenticate(GOOGLE_SCOPES);
    }

    async chat(userMessage: string): Promise<string> {
        this.history.push({ role: 'user', content: userMessage });

        while (true) {
            const response = await this.openai.chat.completions.create({
                model: this.model,
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    ...this.history,
                ],
                tools: COORDINATOR_TOOLS,
                tool_choice: 'auto',
            });

            const assistantMessage = response.choices[0]?.message;
            if (!assistantMessage) {
                throw new Error('No response from the language model.');
            }

            this.history.push(assistantMessage);

            const toolCalls = assistantMessage.tool_calls;
            if (!toolCalls?.length) {
                return assistantMessage.content?.trim() || '(No response)';
            }

            for (const toolCall of toolCalls) {
                if (toolCall.type !== 'function') {
                    continue;
                }

                const result = await this.runTool(
                    toolCall.function.name,
                    toolCall.function.arguments
                );

                this.history.push({
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    content: JSON.stringify(result),
                });
            }
        }
    }

    private async runTool(name: string, argsJson: string): Promise<unknown> {
        let args: Record<string, unknown> = {};
        if (argsJson) {
            try {
                args = JSON.parse(argsJson) as Record<string, unknown>;
            } catch {
                throw new Error(`Invalid tool arguments for ${name}`);
            }
        }

        switch (name) {
            case 'check_unread_emails': {
                const maxResults =
                    typeof args.maxResults === 'number' ? args.maxResults : 10;
                return this.emailAgent.checkUnreadEmails(maxResults);
            }
            case 'fetch_daily_schedule': {
                const date =
                    typeof args.date === 'string' && args.date.trim()
                        ? args.date.trim()
                        : localIsoDate();
                return this.calendarAgent.fetchDailyMeetingSchedule(date);
            }
            case 'get_current_time':
                return { time: await this.timeAgent.getCurrentTime() };
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    }
}
