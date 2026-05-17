import { GoogleServicesUtils } from '../services/GoogleServicesUtils';

export abstract class BaseAgent {
    constructor(protected readonly google: GoogleServicesUtils) {}
}
