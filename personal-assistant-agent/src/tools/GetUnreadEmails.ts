import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import { Token } from '../types';
import { loadToken } from '../utils/tokenManager';

export async function getUnreadEmails(maxResults: number): Promise<any[]> {
    const auth = await authenticate();
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

async function authenticate(): Promise<OAuth2Client> {
    const oAuth2Client = new google.auth.OAuth2(
        process.env.CLIENT_ID || '',
        process.env.CLIENT_SECRET || '',
        process.env.REDIRECT_URI || ''
    );

    const token = loadToken(); // Token | undefined
    if (token) {
        // google-auth expects access_token, refresh_token, expiry_date (ms since epoch)
        oAuth2Client.setCredentials({
            access_token: token.accessToken,
            refresh_token: token.refreshToken,
            expiry_date:
                token.expiryDate instanceof Date
                    ? token.expiryDate.getTime()
                    : Number(token.expiryDate),
        } as any);
    }

    return oAuth2Client;
}