import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import { localDayBounds, localTimeZone } from '../utils/dateUtils';

export interface CalendarEventSummary {
    summary: string;
    timeWindow: string;
    link?: string | null;
}

export interface DailyScheduleResult {
    date: string;
    timeZone: string;
    events: CalendarEventSummary[];
}

function formatEventTime(isoOrDate: string): string {
    if (!isoOrDate.includes('T')) {
        return 'All day';
    }
    const date = new Date(isoOrDate);
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
    });
}

export const fetchDailyMeetingSchedule = async (
    auth: OAuth2Client,
    date: string
): Promise<DailyScheduleResult> => {
    const calendar = google.calendar({ version: 'v3', auth });
    const timeZone = localTimeZone();
    const { timeMin, timeMax } = localDayBounds(date);

    const response = await calendar.events.list({
        calendarId: 'primary',
        timeMin,
        timeMax,
        timeZone,
        singleEvents: true,
        orderBy: 'startTime',
    });

    const events = response.data.items || [];

    const mapped: CalendarEventSummary[] = events.map((event) => {
        const startRaw = event.start?.dateTime || event.start?.date || '';
        const endRaw = event.end?.dateTime || event.end?.date || '';

        const startLabel = formatEventTime(startRaw);
        const endLabel = endRaw.includes('T') ? formatEventTime(endRaw) : '';

        return {
            summary: event.summary || 'Untitled Event',
            timeWindow: endLabel ? `${startLabel} – ${endLabel}` : startLabel,
            link: event.htmlLink,
        };
    });

    return {
        date,
        timeZone,
        events: mapped,
    };
};
