grammar AssetSelection;

start: expr EOF;

// Root rule for parsing expressions
expr:
	traversalAllowedExpr								# TraversalAllowedExpression
	| upTraversal traversalAllowedExpr downTraversal	# UpAndDownTraversalExpression
	| upTraversal traversalAllowedExpr					# UpTraversalExpression
	| traversalAllowedExpr downTraversal				# DownTraversalExpression
	| NOT expr											# NotExpression
	| expr AND expr										# AndExpression
	| expr OR expr										# OrExpression
	| STAR												# AllExpression;

// Allowed expressions for traversals
traversalAllowedExpr:
	attributeExpr						# AttributeExpression
	| functionName LPAREN expr RPAREN	# FunctionCallExpression
	| LPAREN expr RPAREN				# ParenthesizedExpression;

upTraversal: DIGITS? PLUS;
downTraversal: PLUS DIGITS?;

// Function names as tokens
functionName: SINKS | ROOTS;

// Attribute expressions for specific attributes
attributeExpr:
	KEY COLON value						# KeyExpr
	| KEY_SUBSTRING COLON value			# KeySubstringExpr
	| TAG COLON value (EQUAL value)?	# TagAttributeExpr
	| OWNER COLON value					# OwnerAttributeExpr
	| GROUP COLON value					# GroupAttributeExpr
	| KIND COLON value					# KindAttributeExpr
	| CODE_LOCATION COLON value			# CodeLocationAttributeExpr;

// Define EQUAL token for tag:value=value syntax
EQUAL: '=';

// Value can be a quoted or unquoted string
value: QUOTED_STRING | UNQUOTED_STRING;

// Operators and keywords
AND: 'and';
OR: 'or';
NOT: 'not';

STAR: '*';
PLUS: '+';

// Digits
DIGITS: [0-9]+;

// Other tokens
COLON: ':';
LPAREN: '(';
RPAREN: ')';
COMMA: ',';

// Attributes
KEY: 'key';
KEY_SUBSTRING: 'key_substring';
OWNER: 'owner';
GROUP: 'group';
TAG: 'tag';
KIND: 'kind';
CODE_LOCATION: 'code_location';

// Function names
SINKS: 'sinks';
ROOTS: 'roots';

// String tokens
QUOTED_STRING: '"' (~["\\\r\n])* '"';
UNQUOTED_STRING: [a-zA-Z_][a-zA-Z0-9_]*;

// Whitespace
WS: [ \t\r\n]+ -> skip;