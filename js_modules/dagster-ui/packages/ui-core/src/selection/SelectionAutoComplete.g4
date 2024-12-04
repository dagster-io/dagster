grammar SelectionAutoComplete;

// Root rule for parsing expressions
start: expr EOF;

// Root expression rule
expr
    : traversalAllowedExpr afterExpressionWhitespace                                                                # TraversalAllowedExpression
    | upTraversalExp traversalAllowedExpr downTraversalExp afterExpressionWhitespace                                # UpAndDownTraversalExpression
    | upTraversalExp traversalAllowedExpr afterExpressionWhitespace                                                 # UpTraversalExpression
    | traversalAllowedExpr downTraversalExp afterExpressionWhitespace                                               # DownTraversalExpression
    | notToken afterLogicalOperatorWhitespace expr afterExpressionWhitespace                                        # NotExpression
    | expr afterExpressionWhitespace andToken afterLogicalOperatorWhitespace expr afterExpressionWhitespace         # AndExpression
    | expr afterExpressionWhitespace orToken afterLogicalOperatorWhitespace expr afterExpressionWhitespace          # OrExpression
    | expr afterExpressionWhitespace andToken afterLogicalOperatorWhitespace                                        # IncompleteAndExpression
    | expr afterExpressionWhitespace orToken afterLogicalOperatorWhitespace                                         # IncompleteOrExpression
    | notToken afterLogicalOperatorWhitespace                                                                       # IncompleteNotExpression
    | expr afterExpressionWhitespace value afterLogicalOperatorWhitespace                                           # UnmatchedExpressionContinuation
    | STAR afterExpressionWhitespace                                                                                # AllExpression
    | value afterExpressionWhitespace                                                                               # UnmatchedValue
    ;


// Allowed expressions within traversal contexts
traversalAllowedExpr
    : attributeName colonToken attributeValue           # AttributeExpression
    | functionName parenthesizedExpr                    # FunctionCallExpression
    | parenthesizedExpr                                 # ParenthesizedExpressionWrapper
    | incompleteExpressionsWrapper                      # IncompleteExpression
    ;


parenthesizedExpr
    : leftParenToken expr rightParenToken               # ParenthesizedExpression
    ;

// Incomplete expressions wrapper
incompleteExpressionsWrapper
    : attributeName colonToken                          # IncompleteAttributeExpressionMissingValue
    | functionName expressionLessParenthesizedExpr      # ExpressionlessFunctionExpression
    | functionName leftParenToken                       # UnclosedExpressionlessFunctionExpression
    | functionName leftParenToken expr                  # UnclosedFunctionExpression
    | leftParenToken expr                               # UnclosedParenthesizedExpression
    | expressionLessParenthesizedExpr                   # ExpressionlessParenthesizedExpressionWrapper
    | leftParenToken                                    # UnclosedExpressionlessParenthesizedExpression 
    | PLUS+                                             # IncompleteTraversalExpression
    | colonToken attributeValue                         # IncompleteAttributeExpressionMissingKey
    ;

expressionLessParenthesizedExpr
    : leftParenToken rightParenToken                    # ExpressionlessParenthesizedExpression
    ;

upTraversalExp
  : traversal                                           # UpTraversal
  ;

downTraversalExp
  : traversal                                           # DownTraversal
  ;

traversal
    : STAR
    | PLUS+
    ;

// Attribute and function names (to be validated externally)
attributeName
    : IDENTIFIER
    ;


attributeValue
    : value
    ;

functionName
    : IDENTIFIER
    ;

orToken
    : OR
    ;

andToken
    : AND
    ;

notToken
    : NOT
    ;

colonToken
    : COLON
    ;

leftParenToken
    : LPAREN
    ;

rightParenToken
    : RPAREN
    ;

afterExpressionWhitespace
    : WS*
    ;

afterLogicalOperatorWhitespace
   : WS*
   ;
    

// Value can be a quoted string, unquoted string, or identifier
value
    : QUOTED_STRING # QuotedStringValue
    | INCOMPLETE_LEFT_QUOTED_STRING # IncompleteLeftQuotedStringValue
    | INCOMPLETE_RIGHT_QUOTED_STRING # IncompleteRightQuotedStringValue
    | IDENTIFIER # UnquotedStringValue
    ;

// Tokens for operators and keywords
AND : 'and';
OR : 'or';
NOT : 'not';

STAR : '*';
PLUS : '+';

COLON : ':';

LPAREN : '(';
RPAREN : ')';

EQUAL : '=';

// Tokens for strings
QUOTED_STRING  : '"' (~["\\\r\n])* '"' ;
INCOMPLETE_LEFT_QUOTED_STRING: '"' (~["\\\r\n():])* ;
INCOMPLETE_RIGHT_QUOTED_STRING:  (~["\\\r\n:()])* '"' ;

// Identifiers (attributes and functions)
IDENTIFIER : [a-zA-Z_][a-zA-Z0-9_]*;


// Whitespace
WS : [ \t\r\n]+;
