#!/usr/bin/env perl

use strict;
use warnings;
use Time::HiRes qw(gettimeofday);
use MIME::Base64 qw(decode_base64);

sub read_file {
    my ($filename) = @_;
    
    open my $fh, '<', $filename or die "Error: Cannot open file $filename: $!\n";
    
    # Read entire file
    my $data = do { local $/; <$fh> };
    close $fh;
    
    return $data;
}

sub measure {
    my ($data, $pattern, $full_match) = @_;
    
    my $start = gettimeofday();
    
    my $count = 0;
    
    if ($full_match) {
        # Full match: entire text must match the regex
        if ($data =~ /^$pattern$/s) {
            $count = 1;
        }
    } else {
        # Partial match: count all matches in the text
        $count = () = $data =~ /$pattern/g;
    }
    
    my $elapsed = (gettimeofday() - $start) * 1000;  # Convert to milliseconds
    
    printf("%.6f - %d\n", $elapsed, $count);
}

# Main program
if (@ARGV != 3) {
    print "Usage: $0 <base64_regex> <filename> <match_mode>\n";
    print "  base64_regex: Base64-encoded regular expression\n";
    print "  filename: Path to the file containing text to match\n";
    print "  match_mode: 1 for full match, 0 for partial match\n";
    exit 1;
}

my ($base64_regex, $filename, $match_mode) = @ARGV;

# Decode the base64 regex
my $regex;
eval {
    $regex = decode_base64($base64_regex);
};
if ($@) {
    die "Error: Failed to decode base64 regex: $@\n";
}

# Validate match mode
if ($match_mode ne '0' && $match_mode ne '1') {
    die "Error: match_mode must be 0 or 1\n";
}

# Read file content
my $data = read_file($filename);

# Measure and output results
measure($data, $regex, $match_mode);