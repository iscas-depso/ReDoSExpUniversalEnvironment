package main

import (
	"encoding/base64"
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
	"strconv"
	"time"
)

func decodeBase64(base64String string) (string, error) {
	decoded, err := base64.StdEncoding.DecodeString(base64String)
	if err != nil {
		return "", err
	}
	return string(decoded), nil
}

func readFile(filename string) (string, error) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func measure(data string, pattern string, fullMatch bool) {
	start := time.Now()

	r, err := regexp.Compile(pattern)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to compile regex: %v\n", err)
		os.Exit(1)
	}

	var count int

	if fullMatch {
		// Full match: entire text must match the regex
		match := r.FindString(data)
		if match == data {
			count = 1
		} else {
			count = 0
		}
	} else {
		// Partial match: find all matches in the text
		matches := r.FindAllString(data, -1)
		count = len(matches)
	}

	elapsed := time.Since(start)
	elapsedMs := float64(elapsed) / float64(time.Millisecond)

	fmt.Printf("%.6f - %d\n", elapsedMs, count)
}

func main() {
	if len(os.Args) != 4 {
		fmt.Printf("Usage: %s <base64_regex> <filename> <match_mode>\n", os.Args[0])
		fmt.Println("  base64_regex: Base64-encoded regular expression")
		fmt.Println("  filename: Path to the file containing text to match")
		fmt.Println("  match_mode: 1 for full match, 0 for partial match")
		os.Exit(1)
	}

	// Decode the base64 regex
	regex, err := decodeBase64(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to decode base64 regex: %v\n", err)
		os.Exit(1)
	}

	// Read file content
	data, err := readFile(os.Args[2])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Cannot open file %s: %v\n", os.Args[2], err)
		os.Exit(1)
	}

	// Parse match mode
	matchMode, err := strconv.Atoi(os.Args[3])
	if err != nil || (matchMode != 0 && matchMode != 1) {
		fmt.Fprintf(os.Stderr, "Error: match_mode must be 0 or 1\n")
		os.Exit(1)
	}

	// Measure and output results
	measure(data, regex, matchMode == 1)
}
