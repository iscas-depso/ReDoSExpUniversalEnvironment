const fs = require('fs');
const path = require('path');

class HistoryManager {
    constructor(filePath) {
        this.filePath = filePath;
    }

    async append(entry) {
        try {
            const line = JSON.stringify({ ...entry, timestamp: new Date().toISOString() }) + '\n';
            await fs.promises.appendFile(this.filePath, line, 'utf8');
        } catch (error) {
            console.error('Failed to write history:', error);
        }
    }

    async getRecent(limit = 50) {
        try {
            const content = await fs.promises.readFile(this.filePath, 'utf8');
            const lines = content.trim().split('\n');
            return lines
                .map(line => {
                    try { return JSON.parse(line); } catch { return null; }
                })
                .filter(Boolean)
                .reverse()
                .slice(0, limit);
        } catch (err) {
            if (err.code === 'ENOENT') return [];
            console.error('Failed to read history:', err);
            return [];
        }
    }
}

module.exports = HistoryManager;
