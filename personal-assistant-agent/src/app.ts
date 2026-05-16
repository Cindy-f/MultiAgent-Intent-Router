import 'dotenv/config';
import { AssistantAgent } from './agents/assistant';

async function main() {
    const assistant = new AssistantAgent();

    try {
        await assistant.authenticate();
        const unreadEmails = await assistant.checkUnreadEmails();
        console.log('Unread Emails:', unreadEmails);

        const today = new Date().toISOString().split('T')[0];
        const dailySchedule = await assistant.fetchDailyMeetingSchedule(today);
        console.log('Today\'s Meeting Schedule:', dailySchedule);

        const currentTime = await assistant.getCurrentTime();
        console.log('Current Time:', currentTime);
    } catch (error) {
        console.error('Error:', error);
    }
}

main();