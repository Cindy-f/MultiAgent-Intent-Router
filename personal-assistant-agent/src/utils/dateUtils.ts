/** YYYY-MM-DD in the machine's local timezone (not UTC). */
export function localIsoDate(date: Date = new Date()): string {
    return new Intl.DateTimeFormat('en-CA', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).format(date);
}

/** RFC3339 bounds for one local calendar day (timeMax is start of next day, per Google API). */
export function localDayBounds(dateStr: string): { timeMin: string; timeMax: string } {
    const [year, month, day] = dateStr.split('-').map(Number);
    if (!year || !month || !day) {
        throw new Error(`Invalid date: ${dateStr}. Use YYYY-MM-DD.`);
    }

    const start = new Date(year, month - 1, day, 0, 0, 0, 0);
    const endExclusive = new Date(year, month - 1, day + 1, 0, 0, 0, 0);

    return {
        timeMin: start.toISOString(),
        timeMax: endExclusive.toISOString(),
    };
}

export function localTimeZone(): string {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
