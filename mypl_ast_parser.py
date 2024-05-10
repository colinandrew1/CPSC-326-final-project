"""MyPL AST parser implementation.

NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast import *


class ASTParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

        
    def parse(self):
        """Start the parser, returning a Program AST node."""
        program_node = Program([], [])
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def(program_node)
            else:
                self.fun_def(program_node)
        self.eat(TokenType.EOS, 'expecting EOF')
        return program_node

        
    #----------------------------------------------------------------------
    # Helper functions
    #----------------------------------------------------------------------

    def error(self, message):
        """Raises a formatted parser error.

        Args:
            message -- The basic message (expectation)

        """
        lexeme = self.curr_token.lexeme
        line = self.curr_token.line
        column = self.curr_token.column
        err_msg = f'{message} found "{lexeme}" at line {line}, column {column}'
        raise ParserError(err_msg)


    def advance(self):
        """Moves to the next token of the lexer."""
        self.curr_token = self.lexer.next_token()
        # skip comments
        while self.match(TokenType.COMMENT):
            self.curr_token = self.lexer.next_token()

            
    def match(self, token_type):
        """True if the current token type matches the given one.

        Args:
            token_type -- The token type to match on.

        """
        return self.curr_token.token_type == token_type

    
    def match_any(self, token_types):
        """True if current token type matches on of the given ones.

        Args:
            token_types -- Collection of token types to check against.

        """
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    
    def eat(self, token_type, message):
        """Advances to next token if current tokey type matches given one,
        otherwise produces and error with the given message.

        Args: 
            token_type -- The totken type to match on.
            message -- Error message if types don't match.

        """
        if not self.match(token_type):
            self.error(message)
        self.advance()

        
    def is_bin_op(self):
        """Returns true if the current token is a binary operator."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)


    #----------------------------------------------------------------------
    # Recursive descent functions
    #----------------------------------------------------------------------

    # TODO: Finish the recursive descent functions below. Note that
    # you should copy in your functions from HW-2 and then instrument
    # them to build the corresponding AST objects.

    def struct_def(self, program_node):
        # print("in struct def: ", self.curr_token.lexeme)
        """Check for well-formed struct definition."""
        self.eat(TokenType.STRUCT, "expecting struct")
        struct_node = StructDef(None, None)
        struct_node.struct_name = self.curr_token
        self.eat(TokenType.ID, "expecting identifier")
        self.eat(TokenType.LBRACE, "expecting {")
        fields = []
        self.fields(fields)
        self.advance()
        struct_node.fields = fields
        program_node.struct_defs.append(struct_node)

        
    def fields(self, fields_list):
        # print("in fields: ", self.curr_token.lexeme)
        """Check for well-formed struct fields."""
        while not self.match(TokenType.RBRACE):
            field = VarDef(None, None)
            data_type_node = DataType(None, None)
            self.data_type(data_type_node)
            field.data_type = data_type_node
            field.var_name = self.curr_token
            self.eat(TokenType.ID, "expecting identifier")
            self.eat(TokenType.SEMICOLON, "expecting semicolon")
            fields_list.append(field)
        
            
    def fun_def(self, program_node):
        """Check for well-formed function definition."""
        # print("in fun_def: ", self.curr_token.lexeme)
        function_node = FunDef(None, None, None, None)
        if self.match(TokenType.VOID_TYPE):
            data_type_node = DataType(False, self.curr_token)
            self.advance()
            function_node.return_type = data_type_node
        else:
            data_type_node = DataType(None, None)
            self.data_type(data_type_node)
            function_node.return_type = data_type_node
        function_node.fun_name = self.curr_token
        self.eat(TokenType.ID, "expecting identifier")
        self.eat(TokenType.LPAREN, "expecting (")
        params = []
        if not self.match(TokenType.RPAREN):
            self.params(params)   
        function_node.params = params
        self.eat(TokenType.RPAREN, "expecting )")
        self.eat(TokenType.LBRACE, "expecting {")
        stmts = []
        while not self.match(TokenType.RBRACE):
            self.stmt(stmts)
        self.eat(TokenType.RBRACE, "expecting }")
        function_node.stmts = stmts
        program_node.fun_defs.append(function_node)


    def params(self, params_list):
        """Check for well-formed function formal parameters."""
        # print("in params: ", self.curr_token.lexeme)
        var_def_node = VarDef(None, None)
        data_type_node = DataType(None, None)
        self.data_type(data_type_node)
        var_def_node.data_type = data_type_node
        var_def_node.var_name = self.curr_token
        params_list.append(var_def_node)
        self.eat(TokenType.ID, "expecting identifier")
        while(self.match(TokenType.COMMA)):
            self.advance()
            var_def_node = VarDef(None, None)
            data_type_node = DataType(None, None)
            self.data_type(data_type_node)
            var_def_node.data_type = data_type_node
            var_def_node.var_name = self.curr_token
            self.eat(TokenType.ID, "expecting identifier")
            params_list.append(var_def_node)


    def data_type(self, data_type_node):
        """Check for data types."""
        # print("in data_type: ", self.curr_token.lexeme)
        if self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE]):
            data_type_node.is_array = False
            data_type_node.type_name = self.curr_token
            self.base_type()
        elif self.match(TokenType.ID):
            data_type_node.is_array = False
            data_type_node.type_name = self.curr_token
            self.advance()
        elif self.match(TokenType.ARRAY):
            data_type_node.is_array = True
            self.advance()
            if self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE]):
                data_type_node.type_name = self.curr_token
                self.base_type()
            elif self.match(TokenType.ID):
                data_type_node.type_name = self.curr_token
                self.advance()
            else:
                self.error("Expecting ID or primitive type")
        else:
            self.error("Expecting data type")


    def base_type(self):
        """Check for base types."""
        # print("in base_type: ", self.curr_token.lexeme)
        if self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE]):
            self.advance()
        else:
            self.error("expecting primitive type")
        

    def stmt(self, stmts_list):
        """Check for well-formed statements."""
        # print("in stmt: ", self.curr_token.lexeme)
        if self.match(TokenType.WHILE):
            while_stmt_node = WhileStmt(None, None)
            self.while_stmt(while_stmt_node)
            stmts_list.append(while_stmt_node)
        elif self.match(TokenType.IF):
            if_stmt_node = IfStmt(None, None, None)
            self.if_stmt(if_stmt_node)
            stmts_list.append(if_stmt_node)
        elif self.match(TokenType.FOR):
            for_stmt_node = ForStmt(None, None, None, None)
            self.for_stmt(for_stmt_node)
            stmts_list.append(for_stmt_node)
        elif self.match(TokenType.RETURN):
            return_stmt_node = ReturnStmt(None)
            self.return_stmt(return_stmt_node)
            stmts_list.append(return_stmt_node)
            self.eat(TokenType.SEMICOLON, "expecting semicolon")
        elif self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.STRING_TYPE, TokenType.BOOL_TYPE, TokenType.ID, TokenType.ARRAY]):
            # we know that it COULD BE vdecl, assign, call
            prev_token = self.curr_token.token_type
            prev_token_b = self.curr_token
            # setting a previous token variable
            self.advance()
            if self.match(TokenType.ID) or self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.STRING_TYPE, TokenType.BOOL_TYPE]):
                var_decl_node = VarDecl(None, None)
                var_def_node = VarDef(None, None)
                data_type_node = DataType(None, None)
                
                if prev_token == TokenType.ARRAY and self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.STRING_TYPE, TokenType.BOOL_TYPE, TokenType.ID]):
                    #if we have an array and a valid data type, we will advance
                    self.data_type(data_type_node)
                    data_type_node.is_array = True
                else:
                    data_type_node.is_array = False
                    data_type_node.type_name = prev_token_b


                var_def_node.data_type = data_type_node
                var_decl_node.var_def = var_def_node
                var_def_node.var_name = self.curr_token
                expr_node = Expr(False, None, None, None)
                self.eat(TokenType.ID, "expecting identifier")

                self.vdecl_stmt(expr_node)
                var_decl_node.expr = expr_node
                self.eat(TokenType.SEMICOLON, "expecting ;")
                stmts_list.append(var_decl_node)
            elif self.match(TokenType.LPAREN):
                call_expr_node = CallExpr(None, None)
                call_expr_node.fun_name = prev_token_b
                self.call_expr(call_expr_node)
                self.eat(TokenType.SEMICOLON, "expecting ;")
                stmts_list.append(call_expr_node)
            else:
                if prev_token != TokenType.ID:
                    self.error("expecting identifier")
                assign_stmt_node = AssignStmt(None, None)
                var_refs_list = []
                var_ref_node = VarRef(None, None)
                var_ref_node.var_name = prev_token_b
                var_refs_list.append(var_ref_node)
                assign_stmt_node.lvalue = var_refs_list
                self.assign_stmt(assign_stmt_node)
                self.eat(TokenType.SEMICOLON, "expecting ;")
                stmts_list.append(assign_stmt_node)
        else:
            self.error("expecting statement stmt")


    def vdecl_stmt(self, expr_node):
        """Check for variable declaration statements."""
        # self.eat(TokenType.ID, "expecting identifier")
        # print("in vdecl_stmt: ", self.curr_token.lexeme)
        if self.match(TokenType.ASSIGN):
            self.advance()
            self.expr(expr_node)
            

    def assign_stmt(self, assign_stmt_node):
        """Check for well-formed function formal parameters."""
        # print("in assign_stmt: ", self.curr_token.lexeme)
        # logic to determine if we need to call lvalue or not
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.MINUS):
                self.error("expecting identifier")
        else:
            # print
            if self.match(TokenType.ID):
                self.advance()
            # create VarRef object
            self.lvalue(assign_stmt_node.lvalue)
            self.eat(TokenType.ASSIGN, "expecting =")
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        assign_stmt_node.expr = expr_node
    

    def lvalue(self, var_refs_list):
        """Check for well-formed function formal parameters."""
        # print("in lvalue: ", self.curr_token.lexeme)
        #self.eat(TokenType.ID, "expecting identifier")
        # because of this may need to include the id in the var_refs_list above in assign_stmt
        if self.match(TokenType.LBRACKET):
            self.advance()
            expr_node = Expr(False, None, None, None)
            var_refs_list[0].array_expr = expr_node
            self.expr(expr_node)
            self.eat(TokenType.RBRACKET, "expecting ]")
        while self.match(TokenType.DOT):
            self.advance()
            var_ref_node = VarRef(None, None)
            var_ref_node.var_name = self.curr_token
            self.eat(TokenType.ID, "expecting identifier")
            if self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, None, None, None)
                var_ref_node.array_expr = expr_node
                self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "expecting ]")
            var_refs_list.append(var_ref_node)


    def if_stmt(self, if_stmt_node):
        """Check for well-formed if statements."""
        # print("in if_stmt: ", self.curr_token.lexeme)
        self.advance()  #dont need eat() bc when we are here we alr know curr_token is if
        self.eat(TokenType.LPAREN, "expecting (")
        if self.match(TokenType.RPAREN):
            self.error("expecting expression")
        basic_if_node = BasicIf(None, None)
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        basic_if_node.condition = expr_node
        self.eat(TokenType.RPAREN, "expecting )")
        self.eat(TokenType.LBRACE, "expecting {")
        stmts_list = []
        while not self.match(TokenType.RBRACE):
            self.stmt(stmts_list)
        basic_if_node.stmts = stmts_list
        # when we reach this point, we have found '}'
        self.advance()
        if_stmt_node.if_part = basic_if_node
        if_stmt_node.else_ifs = []
        if_stmt_node.else_stmts = []
        self.if_stmt_t(if_stmt_node)


    def if_stmt_t(self, if_stmt_node):
        """Check for if statement tail."""
        # print("in if_stmt_t: ", self.curr_token.lexeme)
        if self.match(TokenType.ELSEIF):
            basic_if_node = BasicIf(None, None)
            self.advance()
            self.eat(TokenType.LPAREN, "expecting (")
            if self.match(TokenType.RPAREN):
                self.error("expecting expression")
            expr_node = Expr(False, None, None, None)
            self.expr(expr_node)
            basic_if_node.condition = expr_node
            self.eat(TokenType.RPAREN, "expecting )")
            self.eat(TokenType.LBRACE, "expecting {")
            stmts_list = []
            while not self.match(TokenType.RBRACE):
                self.stmt(stmts_list)
            basic_if_node.stmts = stmts_list
            if_stmt_node.else_ifs.append(basic_if_node)
            self.advance()
            self.if_stmt_t(if_stmt_node)
        elif self.match(TokenType.ELSE):
            stmts_list = []
            self.advance()
            self.eat(TokenType.LBRACE, "expecting {")
            while not self.match(TokenType.RBRACE):
                self.stmt(stmts_list)
            self.advance()
            if_stmt_node.else_stmts = stmts_list
        

    def while_stmt(self, while_stmt_node):
        """Check for well-formed function formal parameters."""
        # print("in while_stmt: ", self.curr_token.lexeme)
        self.advance()  #dont need eat() bc when we are here we alr know curr_token is if
        self.eat(TokenType.LPAREN, "expecting (")
        if self.match(TokenType.RPAREN):
            self.error("expecting expression")
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        while_stmt_node.condition = expr_node
        self.eat(TokenType.RPAREN, "expecting )")
        self.eat(TokenType.LBRACE, "expecting {")
        stmts_list = []
        while not self.match(TokenType.RBRACE):
            self.stmt(stmts_list)
        while_stmt_node.stmts = stmts_list
        # when we reach this point, we have found '}'
        self.advance()


    def for_stmt(self, for_stmt_node):
        """Check for well-formed for statement."""
        # print("in for_stmt: ", self.curr_token.lexeme)
        self.advance()
        self.eat(TokenType.LPAREN, "expecting (")
        # have to chack valid data types here because we needed to change vdecl for stmt
        if self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.STRING_TYPE, TokenType.BOOL_TYPE, TokenType.ID, TokenType.ARRAY]):
            var_decl_node = VarDecl(None, None)
            var_def_node = VarDef(None, None)
            data_type_node = DataType(False, self.curr_token)
            var_def_node.data_type = data_type_node
            self.advance()
            expr_node = Expr(False, None, None, None)
            var_def_node.var_name = self.curr_token
            self.eat(TokenType.ID, "expecting identifier")
            self.vdecl_stmt(expr_node)
            var_decl_node.var_def = var_def_node
            var_decl_node.expr = expr_node
            for_stmt_node.var_decl = var_decl_node
        self.eat(TokenType.SEMICOLON, "expecting ;")
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        for_stmt_node.condition = expr_node
        self.eat(TokenType.SEMICOLON, "expecting ;")

        assign_stmt_node = AssignStmt(None, None)
        var_refs_list = []
        var_ref_node = VarRef(None, None)
        var_ref_node.var_name = self.curr_token
        var_refs_list.append(var_ref_node)
        assign_stmt_node.lvalue = var_refs_list
        self.assign_stmt(assign_stmt_node)
        for_stmt_node.assign_stmt = assign_stmt_node

        self.eat(TokenType.RPAREN, "expecting )")
        self.eat(TokenType.LBRACE, "expecting {")
        stmts_list = []
        while not self.match(TokenType.RBRACE):
            self.stmt(stmts_list)
        for_stmt_node.stmts = stmts_list
        self.advance()


    def call_expr(self, call_expr_node):
        """Check for well-formed function call expression."""
        # print("in call_expr: ", self.curr_token.lexeme)
        args_list = []
        self.eat(TokenType.LPAREN, "expecting (")
        if not self.match(TokenType.RPAREN):
            expr_node = Expr(False, None, None, None)
            self.expr(expr_node)
            args_list.append(expr_node)
            while self.match(TokenType.COMMA):
                expr_node = Expr(False, None, None, None)
                self.advance()
                self.expr(expr_node)
                args_list.append(expr_node)
        self.eat(TokenType.RPAREN, "expecting )")
        call_expr_node.args = args_list


    def return_stmt(self, return_stmt_node):
        """Check for well-formed function formal parameters."""
        # print("in return stmt: ", self.curr_token.lexeme)
        self.advance()
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        return_stmt_node.expr = expr_node


    def expr(self, expr_node):
        """Check for well-formed function formal parameters."""
        # print("in expr: ", self.curr_token.lexeme)
        if self.match(TokenType.NOT):
            if expr_node.not_op == True:
                expr_node.not_op = False
                self.advance()
            else:
                expr_node.not_op = True
                self.advance()
            self.expr(expr_node)
        elif self.match(TokenType.LPAREN):
            complex_term_node = ComplexTerm(None)
            expr_node_complex_term = Expr(False, None, None, None)
            self.advance()
            self.expr(expr_node_complex_term)
            complex_term_node.expr = expr_node_complex_term
            expr_node.first = complex_term_node
            self.eat(TokenType.RPAREN, "expecting )")
        else:
            simple_term_node = SimpleTerm(None)
            self.rvalue(simple_term_node)
            if expr_node.first is None:
                expr_node.first = simple_term_node
            else:
                expr_node.rest = simple_term_node
            
        if self.match_any([TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE, TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ, TokenType.NOT_EQUAL]):
            expr_node.op = self.curr_token
            self.bin_op()
            expr_node_rest = Expr(False, None, None, None)
            self.expr(expr_node_rest)
            expr_node.rest = expr_node_rest


    def bin_op(self):
        """Check for binary operators."""
        # print("in bin_op: ", self.curr_token.lexeme)
        if self.match_any([TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE, TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ, TokenType.NOT_EQUAL]):
            self.advance()
            if self.match_any([TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE, TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ, TokenType.NOT_EQUAL]):
                self.error("Too many operators")
        else:
            self.error("expecting binary operator type")


    def rvalue(self, simple_term_node):
        """Check for well-formed function formal parameters."""
        # print("in rvalue: ", self.curr_token.lexeme)
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            simple_rvalue_node = SimpleRValue(None)
            simple_rvalue_node.value = self.curr_token
            simple_term_node.rvalue = simple_rvalue_node
            self.base_rvalue()
        elif self.match(TokenType.NULL_VAL):
            simple_rvalue_node = SimpleRValue(None)
            simple_rvalue_node.value = self.curr_token
            simple_term_node.rvalue = simple_rvalue_node
            self.advance()
        elif self.match(TokenType.NEW):
            new_rvalue_node = NewRValue(None, None, None)
            self.new_rvalue(new_rvalue_node)
            simple_term_node.rvalue = new_rvalue_node
        elif self.match(TokenType.ID):
            prev_token = self.curr_token
            self.advance()
            if self.match(TokenType.LPAREN):
                call_expr_node = CallExpr(None, None)
                call_expr_node.fun_name = prev_token
                self.call_expr(call_expr_node)
                simple_term_node.rvalue = call_expr_node
            else:
                var_rvalue_node = VarRValue(None)
                path_list = []
                var_rvalue_node.path = path_list
                var_ref_node = VarRef(None, None)
                var_ref_node.var_name = prev_token
                path_list.append(var_ref_node)
                self.var_rvalue(var_rvalue_node)
                simple_term_node.rvalue = var_rvalue_node
        elif self.match(TokenType.SEMICOLON):
            self.error("unexpected ;")


    def new_rvalue(self, new_rvalue_node):
        """Check for well-formed function formal parameters."""
        # print("in new rvalue: ", self.curr_token.lexeme)
        self.advance()  # past 'new'        
        if self.match_any([TokenType.ID, TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.STRING_TYPE, TokenType.BOOL_TYPE]):
            # we know we COULD have a valid new_rvalue statement
            new_rvalue_node.type_name = self.curr_token
            self.advance()
            if self.match(TokenType.LPAREN):
                struct_params_list = []
                self.advance()
                # option a -- not an array expression
                if not self.match(TokenType.RPAREN):
                    expr_node = Expr(False, None, None, None)
                    self.expr(expr_node)
                    struct_params_list.append(expr_node)
                    while not self.match(TokenType.RPAREN):
                        self.eat(TokenType.COMMA, "expecting ,")
                        expr_node = Expr(False, None, None, None)
                        self.expr(expr_node)
                        struct_params_list.append(expr_node)
                new_rvalue_node.struct_params = struct_params_list
                self.advance()
            elif self.match(TokenType.LBRACKET):
                # option b -- and array expression
                self.eat(TokenType.LBRACKET, "expecting [")
                expr_node = Expr(False, None, None, None)
                self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "expecting ]")
                new_rvalue_node.array_expr = expr_node
            else:
                self.error("expecting { or [")
        else:
            self.error("expecting identifier or base type")

    
    def base_rvalue(self):
        """Check for base rvalue types."""
        # print("in base_rvalue: ", self.curr_token.lexeme)
        if self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL]):
            self.advance()
        else:
            self.error("expecting base rvalue")

    
    def var_rvalue(self, var_rvalue_node):
        """Check for variable rvalues."""
        # print("in var_rvalue: ", self.curr_token.lexeme)
        if self.match(TokenType.LBRACKET):
            expr_node = Expr(False, None, None, None)
            self.advance()
            self.expr(expr_node)
            # required bc we have to advance above and dont want this logic in rvalue
            if len(var_rvalue_node.path) == 1:
                var_rvalue_node.path[0].array_expr = expr_node
            self.eat(TokenType.RBRACKET, "expecting ]")
        while self.match(TokenType.DOT):
            self.advance()
            var_ref_node = VarRef(None, None)
            var_ref_node.var_name = self.curr_token
            self.eat(TokenType.ID, "expecting identifier")
            if self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, None, None, None)
                self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "expecting ]")
                var_ref_node.array_expr = expr_node
            var_rvalue_node.path.append(var_ref_node)
    
