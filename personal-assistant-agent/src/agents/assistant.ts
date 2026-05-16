class AssistantAgent {
    private googleServices: GoogleServicesUtils;

    constructor() {
        this.googleServices = new GoogleServicesUtils();
    }

    async authenticate() {
        await this.googleServices.authenticate();
    }

    async checkUnreadEmails(maxResults: number) {
        const getUnreadEmails = (await import('../tools/GetUnreadEmails')).getUnreadEmails;
        return await getUnreadEmails(maxResults);
    }

    async fetchDailySchedule(date: string) {
        const fetchDailyMeetingSchedule = (await import('../tools/FetchDailyMeetingSchedule')).fetchDailyMeetingSchedule;
        return await fetchDailyMeetingSchedule(date);
    }

    async getCurrentTime() {
        const getCurrentTime = (await import('../tools/GetCurrentTime')).getCurrentTime;
        return await getCurrentTime();
    }
}