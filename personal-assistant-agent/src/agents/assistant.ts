import { GoogleServicesUtils } from '../services/GoogleServicesUtils';
import { EmailAgent } from './emailAgent';
import { CalendarAgent } from './calendarAgent';
import { TimeAgent } from './timeAgent';

/**
 * @deprecated Use LlmCoordinator for chat, or specialist agents directly.
 */
export class AssistantAgent {
    private readonly google: GoogleServicesUtils;
    private readonly emailAgent: EmailAgent;
    private readonly calendarAgent: CalendarAgent;
    private readonly timeAgent: TimeAgent;

    constructor() {
        this.google = new GoogleServicesUtils(
            process.env.CLIENT_ID || '',
            process.env.CLIENT_SECRET || '',
            process.env.REDIRECT_URI || ''
        );
        this.emailAgent = new EmailAgent(this.google);
        this.calendarAgent = new CalendarAgent(this.google);
        this.timeAgent = new TimeAgent();
    }

    async authenticate() {
        await this.google.authenticate([
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.events.readonly',
        ]);
    }

    async checkUnreadEmails(maxResults = 10) {
        return this.emailAgent.checkUnreadEmails(maxResults);
    }

    async fetchDailyMeetingSchedule(date: string) {
        return this.calendarAgent.fetchDailyMeetingSchedule(date);
    }

    async getCurrentTime() {
        return this.timeAgent.getCurrentTime();
    }
}
