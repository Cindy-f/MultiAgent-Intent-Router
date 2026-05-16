import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';

export const fetchDailyMeetingSchedule = async (auth: OAuth2Client, date: string): Promise<any> => {
    const calendar = google.calendar({ version: 'v3', auth });

    const startOfDay = new Date(`${date}T00:00:00`);
    const endOfDay = new Date(`${date}T23:59:59`);

    const response = await calendar.events.list({
        calendarId: 'primary',
        timeMin: startOfDay.toISOString(),
        timeMax: endOfDay.toISOString(),
        singleEvents: true,
        orderBy: 'startTime',
    });

    const events = response.data.items || [];
    
    // Map the raw metadata to a clean, presentable timeline structure
    return events.map(event => {
        const startTime = event.start?.dateTime || event.start?.date || '';
        const endTime = event.end?.dateTime || event.end?.date || '';
        
        // Format time strings cleanly (e.g., "10:00:00")
        const formatTime = (isoString: string) => 
            isoString.includes('T') ? isoString.split('T')[1].split('-')[0] : 'All Day';

        return {
            summary: event.summary || 'Untitled Event',
            timeWindow: `${formatTime(startTime)} - ${formatTime(endTime)}`,
            link: event.htmlLink
        };
    });
};