"""The MyPL Lexer class.

NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_error import *


class Lexer:

    character_to_token_type = {
    # End-of-stream, identifiers, comments
    '': TokenType.EOS,
    'ID': TokenType.ID,
    'COMMENT': TokenType.COMMENT,
    
    # Punctuation
    '.': TokenType.DOT,
    ',': TokenType.COMMA,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET,
    ';': TokenType.SEMICOLON,
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,
    
    # Operators
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.TIMES,
    '/': TokenType.DIVIDE,
    '=': TokenType.ASSIGN,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    
    # Relational comparators
    '==': TokenType.EQUAL,
    '!=': TokenType.NOT_EQUAL,
    '<': TokenType.LESS,
    '<=': TokenType.LESS_EQ,
    '>': TokenType.GREATER,
    '>=': TokenType.GREATER_EQ,
    
    # Values
    'INT_VAL': TokenType.INT_VAL,
    'DOUBLE_VAL': TokenType.DOUBLE_VAL,
    'STRING_VAL': TokenType.STRING_VAL,
    'BOOL_VAL': TokenType.BOOL_VAL,
    'NULL_VAL': TokenType.NULL_VAL,
    
    # Primitive data types
    'int': TokenType.INT_TYPE,
    'double': TokenType.DOUBLE_TYPE,
    'string': TokenType.STRING_TYPE,
    'bool': TokenType.BOOL_TYPE,
    'void': TokenType.VOID_TYPE,
    
    # Reserved words
    'struct': TokenType.STRUCT,
    'array': TokenType.ARRAY,
    'for': TokenType.FOR,
    'while': TokenType.WHILE,
    'if': TokenType.IF,
    'elseif': TokenType.ELSEIF,
    'else': TokenType.ELSE,
    'new': TokenType.NEW,
    'return': TokenType.RETURN,
    }

    two_character_symbols = ['==', '!=', '>=', '<=']

    """For obtaining a token stream from a program."""

    def __init__(self, in_stream):
        """Create a Lexer over the given input stream.

        Args:
            in_stream -- The input stream. 

        """
        self.in_stream = in_stream
        self.line = 1
        self.column = 0


    def read(self):
        """Returns and removes one character from the input stream."""
        self.column += 1
        return self.in_stream.read_char()

    
    def peek(self):
        """Returns but doesn't remove one character from the input stream."""
        return self.in_stream.peek_char()

    
    def eof(self, ch):
        """Return true if end-of-file character"""
        return ch == ''

    
    def error(self, message, line, column):
        raise LexerError(f'{message} at line {line}, column {column}')

    
    def next_token(self):
        """Return the next token in the lexer's input stream."""
        # read initial character
        ch = self.read()
        start_col = self.column

        # Read all whitespace
        if ch.isspace():
            if ch == '\n':
                self.line += 1
                self.column = 0
            return self.next_token()


        # Check for EOF
        if (self.eof(ch)):
            return(Token(TokenType.EOS, '', self.line, start_col))
        

        # Comments
        if ch == '/' and self.peek() == '/':
            self.read() #advance past the second '/'
            comment = ""
            while (self.peek() != '\n' and not self.eof(self.peek())):
                comment += self.read()
            return Token(TokenType.COMMENT, comment, self.line, start_col)


        # Check for reserved words
        if ch.isalpha():
            word = ""
            word += ch
            while self.peek().isalpha() or self.peek() == '_' or self.peek().isdigit():
                next_digit = self.read()
                word += next_digit

            if word in self.character_to_token_type:
                return Token(self.character_to_token_type[word], word, self.line, start_col)
            elif word == "null":
                return Token(TokenType.NULL_VAL, word, self.line, start_col)
            elif word == "true" or word == "false":
                return Token(TokenType.BOOL_VAL, word, self.line, start_col)
            elif word == "true" or word == "false":
                return Token(TokenType.BOOL_VAL, word, self.line, start_col)
            # Identifiers
            else:
                return Token(TokenType.ID, word, self.line, start_col)

        # Single character tokens
        peeked = ch + self.peek()
        if ch in self.character_to_token_type and peeked not in self.two_character_symbols:
            return Token(self.character_to_token_type[ch], ch, self.line, start_col)
        

        # two character symbols
        if peeked in self.character_to_token_type: #and not self.peek().isalpha() and not self.peek().isdigit() and self.peek != '_':
            self.read()
            return Token(self.character_to_token_type[peeked], peeked, self.line, start_col)


        # Check for string values
        if ch == '"':
            string_value = ""
            next_ch = self.read()
            while next_ch != '"' and "\n" not in string_value:
                string_value += next_ch
                next_ch = self.read()
            if "\n" in string_value:
                raise LexerError("non terminated string")
            return Token(TokenType.STRING_VAL, string_value, self.line, start_col)
        

        # Check for int and double values
        if ch.isdigit():
            if ch == "0" and self.peek().isdigit():
                raise LexerError("leading zero not permitted")
            number = ""
            number += ch
            while self.peek().isdigit() or self.peek() == ".":
                if '.' in number and self.peek() == '.':
                    break
                next_digit = self.read()
                if next_digit == '.' and not self.peek().isdigit():
                    raise LexerError("double missing digit after decimal point")
                number += next_digit
            if "." not in number:
                return Token(TokenType.INT_VAL, number, self.line, start_col)
            elif "." in number:
                return Token(TokenType.DOUBLE_VAL, number, self.line, start_col)


        # Unrecognized token
        else:
            raise LexerError("Unrecognized symbol")
        
        