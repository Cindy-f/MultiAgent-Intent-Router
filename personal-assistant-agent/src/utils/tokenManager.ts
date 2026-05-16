import fs from 'fs';
import path from 'path';

const tokenPath = path.join(__dirname, 'token.json');

export const saveToken = (token: object) => {
    fs.writeFileSync(tokenPath, JSON.stringify(token));
};

export const loadToken = () => {
    if (fs.existsSync(tokenPath)) {
        const tokenData = fs.readFileSync(tokenPath, 'utf-8');
        return JSON.parse(tokenData);
    }
    return null;
};