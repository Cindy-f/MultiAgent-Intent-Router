import 'dotenv/config';
import { AssistantAgent } from './agents/assistant';
import chalk from 'chalk';
import Table = require('cli-table3');

async function main() {
    const assistant = new AssistantAgent();

    try {
        await assistant.authenticate();
        console.clear(); // Clears terminal artifacts for a seamless presentation dashboard

        console.log(chalk.cyan.bold('\n======================================================'));
        console.log(chalk.cyan.bold('      🤖 PERSONAL ASSISTANT AGENT METRICS MAIN        '));
        console.log(chalk.cyan.bold('======================================================\n'));

        // 1. Render Gmail Data inside a table layout
        console.log(chalk.yellow.bold('📥 UNREAD INBOX HIGHLIGHTS'));
        const unreadEmails = await assistant.checkUnreadEmails();

        const emailTable = new Table({
            head: [chalk.bold('From'), chalk.bold('Subject')],
            colWidths: [30, 50]
        });

        unreadEmails.forEach(email => {
            emailTable.push([email.from.substring(0, 28), email.subject.substring(0, 48)]);
        });
        console.log(emailTable.toString());

        // 2. Render Calendar Timeline
        console.log(chalk.green.bold('\n📅 TODAY\'S TIMELINE SCHEDULE'));
        const today = new Date().toISOString().split('T')[0];
        const dailySchedule = await assistant.fetchDailyMeetingSchedule(today);

        if (dailySchedule.length === 0) {
            console.log(chalk.dim('   No events scheduled for today.'));
        } else {
            dailySchedule.forEach((event: any) => {
                console.log(`   ⏱️  ${chalk.bold(event.timeWindow)} ➡️ ${chalk.white(event.summary)}`);
            });
        }

        // 3. System Footers
        const currentTime = await assistant.getCurrentTime();
        console.log(chalk.dim(`\n📊 System Sync Time: ${currentTime}`));
        console.log(chalk.cyan.bold('======================================================\n'));

    } catch (error) {
        console.error(chalk.red.bold('Error during agent execution loop:'), error);
    }
}

main();