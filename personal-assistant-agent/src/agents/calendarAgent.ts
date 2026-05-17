import { BaseAgent } from './base';

export class CalendarAgent extends BaseAgent {
    async fetchDailyMeetingSchedule(date: string) {
        const { fetchDailyMeetingSchedule } = await import('../tools/FetchDailyMeetingSchedule');
        return fetchDailyMeetingSchedule(this.google.oauth2Client, date);
    }
}
