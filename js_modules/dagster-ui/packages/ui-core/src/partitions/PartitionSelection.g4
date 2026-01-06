grammar PartitionSelection;

// Entry point - a partition selection is a comma-separated list of items
start: partitionList? EOF;

// A list of partition items separated by commas
partitionList
    : partitionItem (COMMA partitionItem)*
    ;

// Each item can be a range, wildcard, or single partition key
partitionItem
    : range         # RangePartitionItem
    | wildcard      # WildcardPartitionItem
    | partitionKey  # SinglePartitionItem
    ;

// Range syntax: [start...end] with optional quotes on keys
range
    : LBRACKET partitionKey RANGE_DELIM partitionKey RBRACKET
    ;

// Wildcard pattern (only valid unquoted, contains exactly one asterisk)
wildcard
    : WILDCARD_PATTERN
    ;

// A partition key can be quoted or unquoted
partitionKey
    : QUOTED_STRING     # QuotedPartitionKey
    | UNQUOTED_STRING   # UnquotedPartitionKey
    ;

// =============================================================================
// LEXER RULES
// =============================================================================

// Structural tokens - order matters! More specific patterns first.
LBRACKET: '[';
RBRACKET: ']';
RANGE_DELIM: '...';
COMMA: ',';

// Quoted strings support escape sequences for quotes and backslashes
// Examples: "my,key", "my\"quote", "bracket[test]", "has...ellipsis"
QUOTED_STRING
    : '"' ( ESCAPE_SEQ | ~["\\\r\n] )* '"'
    ;

fragment ESCAPE_SEQ
    : '\\' ["\\/]  // Escaped quote, backslash, or forward slash
    ;

// Wildcard patterns - must contain exactly one asterisk
// Must be before UNQUOTED_STRING so it matches first
// Examples: 2024-*, *-suffix, prefix-*-suffix
WILDCARD_PATTERN
    : UNQUOTED_CHAR* '*' UNQUOTED_CHAR*
    ;

// Unquoted strings - simple partition keys without special characters
// Examples: 2024-01-01, my_partition, region-us-east-1
UNQUOTED_STRING
    : UNQUOTED_CHAR+
    ;

// Characters allowed in unquoted partition keys
// Includes common characters found in partition keys: alphanumeric, underscore,
// hyphen, colon, dot, forward slash, at sign
fragment UNQUOTED_CHAR
    : [a-zA-Z0-9_:./@-]
    ;

// Whitespace is skipped
WS: [ \t\r\n]+ -> skip;
