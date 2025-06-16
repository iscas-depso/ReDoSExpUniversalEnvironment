// Test script for V8 experimental non-backtracking RegExp engine
console.log('Testing V8 Non-Backtracking RegExp Engine...');
console.log(`Node.js version: ${process.version}`);
console.log(`V8 version: ${process.versions.v8}`);

// Test 1: Check if linear engine flag is supported
console.log('\n=== Test 1: Linear Engine Flag Support ===');
try {
    const linearRe = new RegExp('test', 'l');
    console.log('✓ Linear engine flag (/l) is supported');
} catch (e) {
    console.log('✗ Linear engine flag (/l) not supported:', e.message);
}

// Test 2: Test performance on potentially problematic pattern
console.log('\n=== Test 2: Performance Test (ReDoS Pattern) ===');
const testString = 'a'.repeat(20);  // Long string without 'b' at end
const problematicPattern = '(a*)*b';

// Test with standard engine
console.log('Testing with standard RegExp engine...');
const startStandard = process.hrtime.bigint();
try {
    const standardRe = new RegExp(problematicPattern);
    const result1 = standardRe.test(testString);
    const endStandard = process.hrtime.bigint();
    console.log(`Standard engine result: ${result1}, time: ${Number(endStandard - startStandard) / 1000000}ms`);
} catch (e) {
    console.log('Standard engine error:', e.message);
}

// Test with linear engine (if supported)
console.log('Testing with linear RegExp engine...');
const startLinear = process.hrtime.bigint();
try {
    const linearRe = new RegExp(problematicPattern, 'l');
    const result2 = linearRe.test(testString);
    const endLinear = process.hrtime.bigint();
    console.log(`Linear engine result: ${result2}, time: ${Number(endLinear - startLinear) / 1000000}ms`);
} catch (e) {
    console.log('Linear engine error:', e.message);
}

// Test 3: Test our detection function
console.log('\n=== Test 3: Engine Detection Function ===');
function detectV8LinearEngineSupport() {
    try {
        new RegExp('test', 'l');
        return true;
    } catch (e) {
        return false;
    }
}

const hasLinearSupport = detectV8LinearEngineSupport();
console.log(`Linear engine detected: ${hasLinearSupport}`);

console.log('\n=== Test Complete ===');