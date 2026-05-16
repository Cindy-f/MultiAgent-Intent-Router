import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import * as fs from 'fs';
import * as readline from 'readline';

export class GoogleServicesUtils {
    public oauth2Client: any;

    constructor(clientId: string, clientSecret: string, redirectUri: string) {
        this.oauth2Client = new (google.auth as any).OAuth2(clientId, clientSecret, redirectUri) as OAuth2Client;
    }

    async authenticate(scopes: string[]): Promise<void> {
        // 1. Try to load an existing token from disk first
        const savedToken = this.loadToken();
        if (savedToken) {
            this.oauth2Client.setCredentials(savedToken);
            console.log('Successfully authenticated using existing token.json');
            return; // Exit early since we have a valid token!
        }

        // 2. If no token exists, initiate the first-time authentication flow
        console.log('No existing token found. Starting first-time authorization...');
        const authUrl = this.oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: scopes,
        });

        console.log('\n========================================================================');
        console.log('Authorize this app by visiting this url:\n', authUrl);
        console.log('========================================================================\n');

        // 3. Pause the terminal and wait for you to paste the authorization code
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
        });

        const code = await new Promise<string>((resolve) => {
            rl.question('Enter the authorization code from that page here: ', (answer) => {
                rl.close();
                resolve(answer.trim());
            });
        });

        // 4. Trade the code for access tokens and save them
        try {
            const { tokens } = await this.oauth2Client.getToken(code);
            this.oauth2Client.setCredentials(tokens);

            // Save it using your existing saveToken function
            await this.saveToken(tokens);
            console.log('Authentication successful! token.json saved.');
        } catch (err) {
            throw new Error(`Failed to retrieve access token from code: ${err}`);
        }
    }

    async saveToken(token: any): Promise<void> {
        fs.writeFileSync('token.json', JSON.stringify(token));
    }

    loadToken(): any {
        if (fs.existsSync('token.json')) {
            const token = fs.readFileSync('token.json', 'utf8');
            return JSON.parse(token);
        }
        return null;
    }
}