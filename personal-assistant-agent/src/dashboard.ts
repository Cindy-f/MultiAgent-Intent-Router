import 'dotenv/config';
import chalk from 'chalk';
import Table = require('cli-table3');
import { LlmCoordinator } from './agents/llmCoordinator';
import { localIsoDate } from './utils/dateUtils';

async function main() {
    const coordinator = new LlmCoordinator();

    try {
        await coordinator.authenticate();
        console.clear();

        console.log(chalk.cyan.bold('      🤖 PERSONAL ASSISTANT AGENT METRICS MAIN        '));

        console.log(chalk.yellow.bold('📥 UNREAD INBOX HIGHLIGHTS'));
        const unreadEmails = await coordinator.email.checkUnreadEmails();

        const emailTable = new Table({
            head: [chalk.bold('From'), chalk.bold('Subject')],
            colWidths: [30, 50],
        });

        unreadEmails.forEach((email: { from: string; subject: string }) => {
            emailTable.push([email.from.substring(0, 28), email.subject.substring(0, 48)]);
        });
        console.log(emailTable.toString());

        console.log(chalk.green.bold("\n📅 TODAY'S TIMELINE SCHEDULE"));
        const dailySchedule = await coordinator.calendar.fetchDailyMeetingSchedule(localIsoDate());

        if (dailySchedule.events.length === 0) {
            console.log(chalk.dim('   No events scheduled for today.'));
        } else {
            dailySchedule.events.forEach((event: { timeWindow: string; summary: string }) => {
                console.log(`   ⏱️  ${chalk.bold(event.timeWindow)} ➡️ ${chalk.white(event.summary)}`);
            });
        }

        const currentTime = await coordinator.time.getCurrentTime();
        console.log(chalk.dim(`\n📊 System Sync Time: ${currentTime}`));
        console.log(chalk.cyan.bold('======================================================\n'));
    } catch (error) {
        console.error(chalk.red.bold('Error during dashboard execution:'), error);
        process.exit(1);
    }
}

main();
