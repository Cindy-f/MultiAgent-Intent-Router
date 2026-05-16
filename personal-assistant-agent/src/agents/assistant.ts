import { GoogleServicesUtils } from '../services/GoogleServicesUtils';

export class AssistantAgent {
    private googleServices: GoogleServicesUtils;

    constructor() {
        this.googleServices = new GoogleServicesUtils(
            process.env.CLIENT_ID || '',
            process.env.CLIENT_SECRET || '',
            process.env.REDIRECT_URI || ''
        );
    }

    async authenticate() {
        await this.googleServices.authenticate([
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.events.readonly',
        ]);
    }

    async checkUnreadEmails(maxResults = 10) {
        const { getUnreadEmails } = await import('../tools/GetUnreadEmails');
        // Pass the authenticated oauth2Client down into the tool function
        return await getUnreadEmails(this.googleServices.oauth2Client, maxResults);
    }

    async fetchDailyMeetingSchedule(date: string) {
        const { fetchDailyMeetingSchedule } = await import('../tools/FetchDailyMeetingSchedule');
        // Pass the authenticated oauth2Client down into the tool function
        return await fetchDailyMeetingSchedule(this.googleServices.oauth2Client, date);
    }

    async getCurrentTime() {
        const { getCurrentTime } = await import('../tools/GetCurrentTime');
        return await getCurrentTime();
    }
}