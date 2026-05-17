import { BaseAgent } from './base';

export class EmailAgent extends BaseAgent {
    async checkUnreadEmails(maxResults = 10) {
        const { getUnreadEmails } = await import('../tools/GetUnreadEmails');
        return getUnreadEmails(this.google.oauth2Client, maxResults);
    }
}
