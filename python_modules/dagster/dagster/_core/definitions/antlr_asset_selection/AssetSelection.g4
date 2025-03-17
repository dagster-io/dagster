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
	KEY COLON keyValue						# KeyExpr
	| TAG COLON value (EQUAL value)?		# TagAttributeExpr
	| OWNER COLON value						# OwnerAttributeExpr
	| GROUP COLON value						# GroupAttributeExpr
	| KIND COLON value						# KindAttributeExpr
	| COLUMN COLON value					# ColumnAttributeExpr
	| TABLE_NAME COLON value				# TableNameAttributeExpr
	| COLUMN_TAG COLON value (EQUAL value)?	# ColumnTagAttributeExpr
	| CODE_LOCATION COLON value				# CodeLocationAttributeExpr
	| CHANGED_IN_BRANCH COLON value			# ChangedInBranchAttributeExpr;

// Define EQUAL token for tag:value=value syntax
EQUAL: '=';

// Value can be a quoted or unquoted string
value: QUOTED_STRING | UNQUOTED_STRING;
keyValue:
	QUOTED_STRING
	| UNQUOTED_STRING
	| UNQUOTED_WILDCARD_STRING;

// Operators and keywords
AND: 'and' | 'AND';
OR: 'or' | 'OR';
NOT: 'not' | 'NOT';

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
OWNER: 'owner';
GROUP: 'group';
TAG: 'tag';
KIND: 'kind';
CODE_LOCATION: 'code_location';
COLUMN: 'column';
TABLE_NAME: 'table_name';
COLUMN_TAG: 'column_tag';
CHANGED_IN_BRANCH: 'changed_in_branch';

// Function names
SINKS: 'sinks';
ROOTS: 'roots';

// String tokens
QUOTED_STRING: '"' (~["\\\r\n])* '"';
UNQUOTED_STRING: [a-zA-Z_][a-zA-Z0-9_/]*;
UNQUOTED_WILDCARD_STRING: [a-zA-Z_*][a-zA-Z0-9_*/]*;

// Whitespace
WS: [ \t\r\n]+ -> skip;