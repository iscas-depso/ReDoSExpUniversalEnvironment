#!/usr/bin/env node

/**
 * Node.js 21 Benchmark Program with V8 Non-Backtracking RegExp Engine
 * Uses V8's experimental linear-time RegExp engine to prevent ReDoS attacks
 * Requires Node.js with V8 8.8+ and appropriate CLI flags
 */

const fs = require('fs');
const { performance } = require('perf_hooks');

class BenchmarkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'BenchmarkError';
    }
}

function detectV8LinearEngineSupport() {
    try {
        // Try to create a regex with the /l flag to detect linear engine support
        new RegExp('test', 'l');
        return true;
    } catch (e) {
        return false;
    }
}

function main() {
    // Check command line arguments
    if (process.argv.length !== 5) {
        console.error(`Usage: node ${process.argv[1]} <base64_regex> <filename> <match_mode>`);
        console.error('  base64_regex: Base64-encoded regular expression');
        console.error('  filename: Path to the file containing text to match');
        console.error('  match_mode: 1 for full match, 0 for partial match');
        console.error('');
        console.error('Note: This benchmark uses V8\'s experimental non-backtracking RegExp engine');
        console.error('Run with: node --enable-experimental-regexp-engine benchmark.js ...');
        process.exit(1);
    }

    const [, , base64Regex, filename, matchModeStr] = process.argv;

    try {
        // Check V8 version and linear engine support
        const hasLinearSupport = detectV8LinearEngineSupport();
        
        // Decode the base64 regex
        const regex = decodeBase64(base64Regex);
        
        // Parse match mode
        const matchMode = parseMatchMode(matchModeStr);
        
        // Read file content
        const data = readFileContent(filename);
        
        // Measure and output results
        measurePerformance(data, regex, matchMode === 1, hasLinearSupport);
        
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

function measurePerformance(data, patternStr, fullMatch, hasLinearSupport) {
    const startTime = performance.now();

    try {
        let count = 0;
        let pattern;

        if (hasLinearSupport) {
            // Use linear engine with /l flag for better performance and security
            const flags = fullMatch ? 'l' : 'gl';
            pattern = new RegExp(patternStr, flags);
            
            if (fullMatch) {
                // Full match: entire text must match the regex (use ^ and $ anchors)
                const fullPattern = new RegExp('^(?:' + patternStr + ')$', 'l');
                count = fullPattern.test(data.trim()) ? 1 : 0;
            } else {
                // Partial match: find all matches using the linear engine
                const matches = data.match(pattern);
                count = matches ? matches.length : 0;
            }
        } else {
            // Fallback to standard engine when linear engine is not available
            const flags = fullMatch ? '' : 'g';
            pattern = new RegExp(patternStr, flags);

            if (fullMatch) {
                // Full match: entire text must match the regex (use ^ and $ anchors)
                const fullPattern = new RegExp('^(?:' + patternStr + ')$');
                count = fullPattern.test(data.trim()) ? 1 : 0;
            } else {
                // Partial match: find all matches using standard approach
                const matches = data.match(new RegExp(patternStr, 'g'));
                count = matches ? matches.length : 0;
            }
        }

        const endTime = performance.now();
        const elapsedMs = endTime - startTime;

        // Output with high precision formatting
        console.log(`${elapsedMs.toFixed(6)} - ${count}`);

    } catch (error) {
        // If linear engine fails with unsupported constructs, fall back to standard
        if (hasLinearSupport && (error.message.includes('not supported') || error.message.includes('Invalid regular expression'))) {
            console.error('Warning: Pattern contains constructs not supported by linear engine, falling back to standard engine');
            measurePerformance(data, patternStr, fullMatch, false);
            return;
        }
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

// Display V8 engine information on startup (for debugging)
if (process.env.NODE_DEBUG && process.env.NODE_DEBUG.includes('benchmark')) {
    console.error(`V8 Version: ${process.versions.v8}`);
    console.error(`Linear Engine Support: ${detectV8LinearEngineSupport()}`);
}

// Run the main function if this module is executed directly
if (require.main === module) {
    main();
} 