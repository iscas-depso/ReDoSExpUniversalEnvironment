#!/usr/bin/env node

/**
 * Node.js 21 Benchmark Program
 * Uses modern JavaScript features for enhanced performance and readability
 */

const fs = require('fs');
const { performance } = require('perf_hooks');

class BenchmarkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'BenchmarkError';
    }
}

function main() {
    // Check command line arguments
    if (process.argv.length !== 5) {
        console.error(`Usage: node ${process.argv[1]} <base64_regex> <filename> <match_mode>`);
        console.error('  base64_regex: Base64-encoded regular expression');
        console.error('  filename: Path to the file containing text to match');
        console.error('  match_mode: 1 for full match, 0 for partial match');
        process.exit(1);
    }

    const [, , base64Regex, filename, matchModeStr] = process.argv;

    try {
        // Decode the base64 regex
        const regex = decodeBase64(base64Regex);
        
        // Parse match mode
        const matchMode = parseMatchMode(matchModeStr);
        
        // Read file content
        const data = readFileContent(filename);
        
        // Measure and output results
        measurePerformance(data, regex, matchMode === 1);
        
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

function decodeBase64(base64String) {
    try {
        if (!base64String || base64String.length === 0) {
            throw new BenchmarkError('Base64 string cannot be empty');
        }
        
        const decoded = Buffer.from(base64String, 'base64').toString('utf8');
        
        if (decoded.length === 0) {
            throw new BenchmarkError('Decoded regex cannot be empty');
        }
        
        return decoded;
    } catch (error) {
        throw new BenchmarkError(`Failed to decode base64 regex: ${error.message}`);
    }
}

function readFileContent(filename) {
    try {
        return fs.readFileSync(filename, { encoding: 'utf8' });
    } catch (error) {
        throw new BenchmarkError(`Cannot open file ${filename}: ${error.message}`);
    }
}

function parseMatchMode(matchModeStr) {
    const matchMode = parseInt(matchModeStr, 10);
    
    if (isNaN(matchMode) || (matchMode !== 0 && matchMode !== 1)) {
        throw new BenchmarkError('match_mode must be 0 or 1');
    }
    
    return matchMode;
}

function measurePerformance(data, patternStr, fullMatch) {
    const startTime = performance.now();

    try {
        // Create regex with appropriate flags
        const flags = fullMatch ? '' : 'g';
        const pattern = new RegExp(patternStr, flags);
        let count = 0;

        if (fullMatch) {
            // Full match: entire text must match the regex (use ^ and $ anchors)
            const fullPattern = new RegExp('^(?:' + patternStr + ')$');
            count = fullPattern.test(data.trim()) ? 1 : 0;
        } else {
            // Partial match: find all matches using compatible approach
            const matches = data.match(new RegExp(patternStr, 'g'));
            count = matches ? matches.length : 0;
        }

        const endTime = performance.now();
        const elapsedMs = endTime - startTime;

        // Output with high precision formatting
        console.log(`${elapsedMs.toFixed(6)} - ${count}`);

    } catch (error) {
        throw new BenchmarkError(`Failed to compile regex: ${error.message}`);
    }
}

// Enhanced error handling for modern Node.js
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error.message);
    process.exit(1);
});

process.on('unhandledRejection', (reason) => {
    console.error('Unhandled Promise Rejection:', reason);
    process.exit(1);
});

// Run the main function if this module is executed directly
if (require.main === module) {
    main();
} 