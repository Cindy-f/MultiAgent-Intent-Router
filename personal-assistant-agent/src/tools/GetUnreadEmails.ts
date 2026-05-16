import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';

export async function getUnreadEmails(auth: OAuth2Client, maxResults: number): Promise<any[]> {
    const gmail = google.gmail({ version: 'v1', auth });

    const response = await gmail.users.messages.list({
        userId: 'me',
        q: 'is:unread',
        maxResults,
    });

    const messages = response.data.messages || [];
    const emailPromises = messages
        .filter((m): m is { id: string } => !!m && !!m.id)
        .map(async (message) => {
            const emailResponse = await gmail.users.messages.get({
                userId: 'me',
                id: message.id,
            });

            const fullDetails = emailResponse.data;
            const headers = fullDetails.payload?.headers || [];

            // Helper function to extract specific information from Google's header array
            const getHeader = (name: string) =>
                headers.find(h => h.name?.toLowerCase() === name.toLowerCase())?.value || 'Unknown';

            return {
                id: fullDetails.id,
                from: getHeader('From'),
                subject: getHeader('Subject'),
                date: getHeader('Date'),
                snippet: fullDetails.snippet,
            };
        });

    return Promise.all(emailPromises);
}