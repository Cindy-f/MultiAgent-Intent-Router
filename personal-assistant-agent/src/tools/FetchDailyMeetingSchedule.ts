import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';

// Accept the authenticated OAuth2Client as the first argument
export const fetchDailyMeetingSchedule = async (auth: OAuth2Client, date: string): Promise<any> => {
    // Pass the pre-authenticated client straight into the calendar service
    const calendar = google.calendar({ version: 'v3', auth });

    // Calculate the start of the day and start of the next day
    const startOfDay = new Date(`${date}T00:00:00`);
    const endOfDay = new Date(`${date}T23:59:59`);

    const response = await calendar.events.list({
        calendarId: 'primary',
        timeMin: startOfDay.toISOString(),
        timeMax: endOfDay.toISOString(),
        singleEvents: true,
        orderBy: 'startTime',
    });

    return response.data.items || [];
};