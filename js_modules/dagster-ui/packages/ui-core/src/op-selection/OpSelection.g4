grammar OpSelection;

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
attributeExpr: NAME COLON keyValue # NameExpr;

// Value can be a quoted or unquoted string
value: QUOTED_STRING | UNQUOTED_STRING;
keyValue:
	QUOTED_STRING
	| UNQUOTED_STRING
	| UNQUOTED_WILDCARD_STRING;

// Tokens for operators and keywords
AND: 'and' | 'AND';
OR: 'or' | 'OR';
NOT: 'not' | 'NOT';

STAR: '*';
PLUS: '+';

DIGITS: [0-9]+;

COLON: ':';

LPAREN: '(';
RPAREN: ')';

// Tokens for attributes
NAME: 'name';

// Tokens for function names
SINKS: 'sinks';
ROOTS: 'roots';

// Tokens for strings
QUOTED_STRING: '"' (~["\\\r\n])* '"';
UNQUOTED_STRING: [a-zA-Z_][a-zA-Z0-9_]*;
UNQUOTED_WILDCARD_STRING: [a-zA-Z_*][a-zA-Z0-9_*]*;

// Whitespace
WS: [ \t\r\n]+ -> skip;