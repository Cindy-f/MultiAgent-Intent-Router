export interface Email {
    id: string;
    subject: string;
    sender: string;
    receivedDate: Date;
    isRead: boolean;
}

export interface Meeting {
    title: string;
    startTime: Date;
    endTime: Date;
    location?: string;
    attendees: string[];
}

export interface Token {
    accessToken: string;
    refreshToken: string;
    expiryDate: Date;
}