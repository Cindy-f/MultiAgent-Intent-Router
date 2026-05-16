export class GoogleServicesUtils {
    private oauth2Client: any;

    constructor(clientId: string, clientSecret: string, redirectUri: string) {
        const { OAuth2 } = require('google-auth-library');
        this.oauth2Client = new OAuth2(clientId, clientSecret, redirectUri);
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