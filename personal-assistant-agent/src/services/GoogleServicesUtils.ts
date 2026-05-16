import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';

export class GoogleServicesUtils {
    public oauth2Client: any;
    constructor(clientId: string, clientSecret: string, redirectUri: string) {
        // use google.auth.OAuth2 from googleapis; cast to OAuth2Client for typing
        this.oauth2Client = new (google.auth as any).OAuth2(clientId, clientSecret, redirectUri) as OAuth2Client;
    }

    async authenticate(scopes: string[]): Promise<void> {
        const authUrl = this.oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: scopes,
        });
        console.log('Authorize this app by visiting this url:', authUrl);
        // Here you would typically wait for the user to provide the code from the URL
        // and then use it to get the token
    }

    async saveToken(token: any): Promise<void> {
        const fs = require('fs');
        fs.writeFileSync('token.json', JSON.stringify(token));
    }

    loadToken(): any {
        const fs = require('fs');
        if (fs.existsSync('token.json')) {
            const token = fs.readFileSync('token.json');
            return JSON.parse(token);
        }
        return null;
    }
}