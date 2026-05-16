export function getCurrentTime(): Promise<string> {
    return new Promise((resolve, reject) => {
        const currentTime = new Date().toISOString();
        resolve(currentTime);
    });
}