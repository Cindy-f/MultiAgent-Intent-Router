import OpenAI from 'openai';

export type LlmProvider = 'openai' | 'ollama' | 'groq' | 'nvidia';

export interface LlmSettings {
    provider: LlmProvider;
    client: OpenAI;
    model: string;
    label: string;
}

const NVIDIA_BASE_URL = 'https://integrate.api.nvidia.com/v1';
const GROQ_BASE_URL = 'https://api.groq.com/openai/v1';
const OLLAMA_BASE_URL = 'http://localhost:11434/v1';

function firstEnv(...names: string[]): string | undefined {
    for (const name of names) {
        const value = process.env[name];
        if (value?.trim()) {
            return value.trim();
        }
    }
    return undefined;
}

function detectProvider(): LlmProvider {
    const explicit = process.env.LLM_PROVIDER?.toLowerCase();
    if (explicit === 'ollama' || explicit === 'groq' || explicit === 'nvidia' || explicit === 'openai') {
        return explicit;
    }

    const key = firstEnv('OPENAI_API_KEY', 'API_KEY', 'GROQ_API_KEY', 'NVIDIA_API_KEY');
    if (key?.startsWith('nvapi-')) {
        return 'nvidia';
    }
    if (firstEnv('GROQ_API_KEY')) {
        return 'groq';
    }
    if (process.env.OPENAI_BASE_URL?.includes('11434')) {
        return 'ollama';
    }
    if (process.env.LLM_PROVIDER?.toLowerCase() === 'ollama') {
        return 'ollama';
    }

    return 'openai';
}

function requireKey(provider: string, ...names: string[]): string {
    const key = firstEnv(...names);
    if (!key) {
        throw new Error(
            `Missing API key for ${provider}. Set one of: ${names.join(', ')} in .env`
        );
    }
    return key;
}

/**
 * Resolves LLM client settings. Supports OpenAI, Ollama (local/free),
 * Groq (free tier), and NVIDIA NIM (OpenAI-compatible).
 */
export function resolveLlmSettings(): LlmSettings {
    const provider = detectProvider();

    switch (provider) {
        case 'ollama':
            return {
                provider,
                label: 'Ollama (local)',
                client: new OpenAI({
                    baseURL: firstEnv('OPENAI_BASE_URL') || OLLAMA_BASE_URL,
                    apiKey: firstEnv('OPENAI_API_KEY') || 'ollama',
                }),
                model: firstEnv('OPENAI_MODEL') || 'llama3.1',
            };

        case 'groq':
            return {
                provider,
                label: 'Groq',
                client: new OpenAI({
                    baseURL: firstEnv('OPENAI_BASE_URL') || GROQ_BASE_URL,
                    apiKey: requireKey('Groq', 'GROQ_API_KEY', 'OPENAI_API_KEY', 'API_KEY'),
                }),
                model: firstEnv('OPENAI_MODEL') || 'llama-3.3-70b-versatile',
            };

        case 'nvidia':
            return {
                provider,
                label: 'NVIDIA NIM',
                client: new OpenAI({
                    baseURL: firstEnv('OPENAI_BASE_URL') || NVIDIA_BASE_URL,
                    apiKey: requireKey(
                        'NVIDIA NIM',
                        'NVIDIA_API_KEY',
                        'OPENAI_API_KEY',
                        'API_KEY'
                    ),
                }),
                model: firstEnv('OPENAI_MODEL') || 'meta/llama-3.3-70b-instruct',
            };

        case 'openai':
        default: {
            const baseURL = firstEnv('OPENAI_BASE_URL');
            const apiKey = requireKey('OpenAI', 'OPENAI_API_KEY', 'API_KEY');
            return {
                provider: 'openai',
                label: baseURL ? 'OpenAI-compatible API' : 'OpenAI',
                client: new OpenAI({
                    apiKey,
                    ...(baseURL ? { baseURL } : {}),
                }),
                model: firstEnv('OPENAI_MODEL') || 'gpt-4o-mini',
            };
        }
    }
}
