export class TimeAgent {
    async getCurrentTime() {
        const { getCurrentTime } = await import('../tools/GetCurrentTime');
        return getCurrentTime();
    }
}
