import 'dotenv/config';
import chalk from 'chalk';
import * as readline from 'readline';
import { LlmCoordinator } from './agents/llmCoordinator';

function createPrompt(): readline.Interface {
    return readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
}

async function main() {
    const coordinator = new LlmCoordinator();

    try {
        console.log(chalk.cyan.bold('Authenticating with Google...'));
        await coordinator.authenticate();
        console.clear();
        console.log(chalk.cyan.bold('Personal Assistant (LLM coordinator)'));
        console.log(chalk.dim(`LLM: ${coordinator.llmLabel}`));
        console.log(
            chalk.dim(
                'Ask about unread email, your calendar, or the time. Type "exit" to quit.\n'
            )
        );

        const rl = createPrompt();

        const ask = (): void => {
            rl.question(chalk.yellow('You: '), async (input) => {
                const trimmed = input.trim();
                if (!trimmed) {
                    ask();
                    return;
                }
                if (trimmed.toLowerCase() === 'exit') {
                    rl.close();
                    return;
                }

                try {
                    process.stdout.write(chalk.dim('Thinking...\r'));
                    const reply = await coordinator.chat(trimmed);
                    process.stdout.write('\r\x1b[K');
                    console.log(chalk.green('Assistant:'), reply, '\n');
                } catch (error) {
                    process.stdout.write('\r\x1b[K');
                    console.error(chalk.red('Error:'), error, '\n');
                }

                ask();
            });
        };

        ask();
    } catch (error) {
        console.error(chalk.red.bold('Failed to start assistant:'), error);
        process.exit(1);
    }
}

main();
