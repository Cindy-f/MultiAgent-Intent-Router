import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';

// Accept the authenticated OAuth2Client as the first argument
export async function getUnreadEmails(auth: OAuth2Client, maxResults: number): Promise<any[]> {
    // Pass the pre-authenticated client straight into the gmail service
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
            return emailResponse.data;
        });

    return Promise.all(emailPromises);
}