import { google } from 'googleapis';
import { Token } from '../types';
import { loadToken } from '../utils/tokenManager';

export async function getUnreadEmails(maxResults: number): Promise<any> {
    const auth = await authenticate();
    const gmail = google.gmail({ version: 'v1', auth });

    const response = await gmail.users.messages.list({
        userId: 'me',
        q: 'is:unread',
        maxResults: maxResults,
    });

    const messages = response.data.messages || [];
    const emailPromises = messages.map(async (message) => {
        const emailResponse = await gmail.users.messages.get({
            userId: 'me',
            id: message.id,
        });
        return emailResponse.data;
    });

    return Promise.all(emailPromises);
}

async function authenticate() {
    const token: Token = await loadToken();
    const oAuth2Client = new google.auth.OAuth2(
        process.env.CLIENT_ID,
        process.env.CLIENT_SECRET,
        process.env.REDIRECT_URI
    );

    oAuth2Client.setCredentials(token);
    return oAuth2Client;
}