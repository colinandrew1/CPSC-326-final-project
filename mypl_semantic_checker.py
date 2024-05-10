"""Semantic Checker Visitor for semantically analyzing a MyPL program.

NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_error import *
from mypl_token import Token, TokenType
from mypl_ast import *
from mypl_symbol_table import SymbolTable


BASE_TYPES = ['int', 'double', 'bool', 'string']
BUILT_INS = ['print', 'input', 'itos', 'itod', 'dtos', 'dtoi', 'stoi', 'stod',
             'length', 'get']

class SemanticChecker(Visitor):
    """Visitor implementation to semantically check MyPL programs."""

    def __init__(self):
        self.structs = {}
        self.functions = {}
        self.symbol_table = SymbolTable()
        self.curr_type = None


    # Helper Functions

    def error(self, msg, token):
        """Create and raise a Static Error."""
        if token is None:
            raise StaticError(msg)
        else:
            m = f'{msg} near line {token.line}, column {token.column}'
            raise StaticError(m)


    def get_field_type(self, struct_def, field_name):
        """Returns the DataType for the given field name of the struct
        definition.

        Args:
            struct_def: The StructDef object 
            field_name: The name of the field

        Returns: The corresponding DataType or None if the field name
        is not in the struct_def.

        """
        for var_def in struct_def.fields:
            if var_def.var_name.lexeme == field_name:
                return var_def.data_type
        return None

        
    # Visitor Functions
    
    def visit_program(self, program):
        # check and record struct defs
        for struct in program.struct_defs:
            struct_name = struct.struct_name.lexeme
            if struct_name in self.structs:
                self.error(f'duplicate {struct_name} definition', struct.struct_name)
            self.structs[struct_name] = struct
        # check and record function defs
        for fun in program.fun_defs:
            fun_name = fun.fun_name.lexeme
            if fun_name in self.functions: 
                self.error(f'duplicate {fun_name} definition', fun.fun_name)
            if fun_name in BUILT_INS:
                self.error(f'redefining built-in function', fun.fun_name)
            if fun_name == 'main' and fun.return_type.type_name.lexeme != 'void':
                self.error('main without void type', fun.return_type.type_name)
            if fun_name == 'main' and fun.params: 
                self.error('main function with parameters', fun.fun_name)
            self.functions[fun_name] = fun
        # check main function
        if 'main' not in self.functions:
            self.error('missing main function', None)
        # check each struct
        for struct in self.structs.values():
            struct.accept(self)
        # check each function
        for fun in self.functions.values():
            fun.accept(self)
        
        
    def visit_struct_def(self, struct_def):
        self.symbol_table.push_environment()
        for field in struct_def.fields:
            field.accept(self)
        self.symbol_table.pop_environment()


    def visit_fun_def(self, fun_def):
        # at this point we know that we have a valid main and there are no duplicate function names
        # we just need to handle a function at a time -- one call to visit_fun_def handles just one function
        # cases: duplicate param names, undefined param type or return type

        self.symbol_table.push_environment()
        self.symbol_table.add("return", fun_def.return_type)

        # check for valid return type
        fun_def.return_type.accept(self)

        # check for valid params
        for param in fun_def.params:
            # note different functions can have parameters with the same names -- scoped only to the given function
            param.accept(self)

        # check for valid stmts (traverse the tree/elsewhere)
        for stmt in fun_def.stmts:
            stmt.accept(self)

        self.symbol_table.pop_environment()


    def visit_return_stmt(self, return_stmt):
        # all return should do is visit expression -- eventually it will set the type of curr token
        # back where return get called we will make sure it matches the functions specified return type
        return_stmt.expr.accept(self)
        return_type = self.symbol_table.get("return")
        # with functions that dont return anything, need to make sure that self.curr_type is set appropriately
        if (self.curr_type.type_name.lexeme != return_type.type_name.lexeme or self.curr_type.is_array != return_type.is_array) and self.curr_type.type_name.lexeme != 'void':
            self.error("Mismatched return types", self.curr_type.type_name)

    
    def visit_var_decl(self, var_decl):
        var_decl.var_def.accept(self)
        lhs_type = self.curr_type

        # at this point we have stored the variable name and data type in the symbol table
        if var_decl.expr.first is not None:
            var_decl.expr.accept(self)

        # check for arrays
        if (lhs_type.is_array != self.curr_type.is_array) and (self.curr_type.type_name.token_type != TokenType.VOID_TYPE):
            self.error("expecting array - var decl", self.curr_type.type_name)

        
        # check for type match
        if (lhs_type.type_name.token_type != self.curr_type.type_name.token_type) and (self.curr_type.type_name.token_type != TokenType.VOID_TYPE):
            self.error("mismatched type - var_decl", self.curr_type.type_name)


    def visit_assign_stmt(self, assign_stmt):
        type = self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme)
        if type is not None and type.type_name.lexeme in self.structs:
            # we know that we have a reference to a struct instance -- may not be final variable in path
            if len(assign_stmt.lvalue) == 1:
                array_expr = False
                if assign_stmt.lvalue[0].array_expr is not None:
                    assign_stmt.lvalue[0].array_expr.accept(self)
                    if self.curr_type.type_name.lexeme != 'int':
                        self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
                    array_expr = True
                var_info = self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme)
                self.curr_type = DataType(var_info.is_array, var_info.type_name)
                if array_expr:
                    self.curr_type.is_array = False
            else:
                struct_def = self.structs[type.type_name.lexeme]
                for i in range(1, len(assign_stmt.lvalue)):
                    field_exists = False
                    array_expr = False
                    curr_field = None
                    for field in struct_def.fields:
                        if field.var_name.lexeme == assign_stmt.lvalue[i].var_name.lexeme:
                            field_exists = True
                            curr_field = field
                            if field.data_type.is_array and i != len(assign_stmt.lvalue)-1:
                                if assign_stmt.lvalue[i].array_expr == None:
                                    self.error("expecting array expression - assign", self.curr_type.type_name)
                            # check if it is another struct
                            if field.data_type.type_name.lexeme in self.structs:
                                struct_def = self.structs[field.data_type.type_name.lexeme]
                            self.curr_type = field.data_type
                            break 
                    if not field_exists:
                        self.error("Field does not exist in struct", self.curr_type.type_name)

                    if assign_stmt.lvalue[i].array_expr is not None:
                        assign_stmt.lvalue[i].array_expr.accept(self)
                        if self.curr_type.type_name.lexeme != 'int':
                            self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
                        array_expr = True
                    if i == len(assign_stmt.lvalue) - 1:
                        # the current type should be that of the field in question
                        type = field.data_type
                        self.curr_type = DataType(type.is_array, type.type_name)
                        if array_expr:
                            self.curr_type.is_array = False
                    
        else:
            for i in range(len(assign_stmt.lvalue)):
                array_expr = False
                if not self.symbol_table.exists(assign_stmt.lvalue[i].var_name.lexeme):
                    self.error("unrecognized variable -- assign", assign_stmt.lvalue[i].var_name)
                if assign_stmt.lvalue[i].array_expr is not None:
                    assign_stmt.lvalue[i].array_expr.accept(self)
                    if self.curr_type.type_name.lexeme != 'int':
                        self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
                    array_expr = True
                if i == len(assign_stmt.lvalue) - 1:
                    type = self.symbol_table.get(assign_stmt.lvalue[i].var_name.lexeme)
                    self.curr_type = DataType(type.is_array, type.type_name)
                    if array_expr:
                        self.curr_type.is_array = False
                
        lhs_type = self.curr_type
        assign_stmt.expr.accept(self)

        if (lhs_type.is_array != self.curr_type.is_array) and (self.curr_type.type_name.token_type != TokenType.VOID_TYPE):
            self.error("expecting array - assign stmt", self.curr_type.type_name)
        
        # check for type match
        if (lhs_type.type_name.token_type != self.curr_type.type_name.token_type) and (self.curr_type.type_name.token_type != TokenType.VOID_TYPE):
            self.error("mismatched type - assign stmt", self.curr_type.type_name)


    def visit_while_stmt(self, while_stmt):
        self.symbol_table.push_environment()
        while_stmt.condition.accept(self)
        if self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array == True:
            self.error("expecting boolean expression", self.curr_type.type_name)
        if while_stmt.stmts is not None:
            for stmt in while_stmt.stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
        

    def visit_for_stmt(self, for_stmt):
        self.symbol_table.push_environment()
        for_stmt.var_decl.accept(self)
        for_stmt.condition.accept(self)
        if self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array == True:
            self.error("expecting boolean expression", self.curr_type.type_name)
        for_stmt.assign_stmt.accept(self)
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()


    def visit_if_stmt(self, if_stmt):
        # check if curr token is bool
        if_stmt.if_part.condition.accept(self)
        if self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array == True:
            self.error("expecting boolean expression", self.curr_type.type_name)
        self.symbol_table.push_environment()
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()

        for else_if_block in if_stmt.else_ifs:
            self.symbol_table.push_environment()
            else_if_block.condition.accept(self)
            if self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array == True:
                self.error("expecting boolean expression", self.curr_type.type_name)
            for stmt in else_if_block.stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
        

        self.symbol_table.push_environment()
        for stmt in if_stmt.else_stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()


    def visit_call_expr(self, call_expr):
        # assume that we need to set the type of curr token to the type that is associated with the given function call

        if call_expr.fun_name.lexeme == "print":
            if len(call_expr.args) != 1:
                self.error("print accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme not in BASE_TYPES or self.curr_type.is_array == True:
                self.error("Arguments to print may only be base types", None)
            self.curr_type == DataType(False, Token(TokenType.VOID_TYPE, 'void', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "input":
            if len(call_expr.args) != 0:
                self.error("input accepts no argument", None) 
            self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "itos":
            if len(call_expr.args) != 1:
                self.error("itos accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "int":
                self.error("Arguments to itos may only be int type", None)
            self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "itod":
            if len(call_expr.args) != 1:
                self.error("itod accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "int":
                self.error("Arguments to itos may only be int type", None)
            self.curr_type = DataType(False, Token(TokenType.DOUBLE_TYPE, 'double', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "dtos":
            if len(call_expr.args) != 1:
                self.error("dtos accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "double":
                self.error("Arguments to dtos may only be double type", None)
            self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "dtoi":
            if len(call_expr.args) != 1:
                self.error("dtoi accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "double":
                self.error("Arguments to dtoi may only be int type", None)
            self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', self.curr_type.type_name.line, self.curr_type.type_name.column))
            
        elif call_expr.fun_name.lexeme == "stoi":
            if len(call_expr.args) != 1:
                self.error("stoi accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "string":
                self.error("Arguments to stoi may only be string type", None)
            self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', self.curr_type.type_name.line, self.curr_type.type_name.column))

        elif call_expr.fun_name.lexeme == "stod":
            if len(call_expr.args) != 1:
                self.error("stod accepts one argument", None)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "string":
                self.error("Arguments to stod may only be int type", None)
            self.curr_type = DataType(False, Token(TokenType.DOUBLE_TYPE, 'double', self.curr_type.type_name.line, self.curr_type.type_name.column))
            
        elif call_expr.fun_name.lexeme == "length":
            if len(call_expr.args) != 1:
                self.error("length accepts one argument", self.curr_type.type_name)
            call_expr.args[0].accept(self)
            if self.curr_type.type_name.lexeme != "string" and self.curr_type.is_array == False:
                self.error("Arguments to length may only be string or array", self.curr_type.type_name)
            self.curr_type = DataType(False, Token(TokenType.INT_TYPE, 'int', self.curr_type.type_name.line, self.curr_type.type_name.column))
                       
        elif call_expr.fun_name.lexeme == "get":
            if len(call_expr.args) != 2:
                self.error("length accepts two argument", None)
            call_expr.args[0].accept(self)
            # get_index_type = self.curr_type
            if self.curr_type.type_name.lexeme != "int":
                self.error("First argument to get may only be int type", None)

            call_expr.args[1].accept(self)
            if self.curr_type.type_name.lexeme != "string" or self.curr_type.is_array != False:
                self.error("Second argument to get may only be string type", None)
            self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', self.curr_type.type_name.line, self.curr_type.type_name.column))

        else:
            if call_expr.fun_name.lexeme not in self.functions:
                self.error("unrecognized function", self.curr_type.type_name)
            
            user_def_function = self.functions[call_expr.fun_name.lexeme]

            if len(call_expr.args) != len(user_def_function.params):
                self.error("Incorrect number of arguments", self.curr_type.type_name)

            for i in range(len(call_expr.args)):
                call_expr.args[i].accept(self)
                if (self.curr_type.type_name.lexeme != user_def_function.params[i].data_type.type_name.lexeme) and self.curr_type.type_name.lexeme != 'void':
                    self.error("Argument does not match type provided in function definition", self.curr_type.type_name)
                if self.curr_type.is_array != user_def_function.params[i].data_type.is_array and self.curr_type.type_name.lexeme != 'void':
                    self.error("Expecting array - call expr", self.curr_type.type_name)
            
            self.curr_type = DataType(user_def_function.return_type.is_array, Token(user_def_function.return_type.type_name.token_type, user_def_function.return_type.type_name.lexeme, self.curr_type.type_name.line, self.curr_type.type_name.column))
      

    def visit_expr(self, expr):
        arithmetic_ops = ['+', '-', '*', '/']
        void_compatible_relational_ops = ['==', '!=']
        non_void_relational_ops = ['<','<=', '>', '>=']
        logical_ops = ['and', 'or', 'not']

        expr.first.accept(self)
        lhs_type = self.curr_type
        if expr.op is not None:
            expr.rest.accept(self)
            rhs_type = self.curr_type

            # expression typing rules
            if (lhs_type.type_name.lexeme != rhs_type.type_name.lexeme) and not (lhs_type.type_name.lexeme == 'void' or rhs_type.type_name.lexeme == 'void'):
                self.error("mismatched type - expr", rhs_type.type_name)

            if (lhs_type.type_name.lexeme == rhs_type.type_name.lexeme):
                matched_types = True
            else:
                matched_types = False
            
            if lhs_type.type_name.lexeme == 'string' and matched_types and expr.op.lexeme == '+':
                self.curr_type = DataType(False, Token(TokenType.STRING_TYPE, 'string', lhs_type.type_name.line, lhs_type.type_name.column))

            elif (lhs_type.type_name.lexeme == 'int' or lhs_type.type_name.lexeme == 'double') and expr.op.lexeme in arithmetic_ops and matched_types:
                self.curr_type = DataType(False, Token(lhs_type.type_name.token_type, lhs_type.type_name.lexeme, lhs_type.type_name.line, lhs_type.type_name.column))

            elif (matched_types or (lhs_type.type_name.lexeme == 'void' or rhs_type.type_name.lexeme == 'void')) and expr.op.lexeme in void_compatible_relational_ops:
                self.curr_type = DataType(False, Token(TokenType.BOOL_TYPE, 'bool', lhs_type.type_name.line, lhs_type.type_name.column))

            elif matched_types and (lhs_type.type_name.lexeme in ['int', 'double', 'string']) and (expr.op.lexeme in non_void_relational_ops):
                self.curr_type = DataType(False, Token(TokenType.BOOL_TYPE, 'bool', lhs_type.type_name.line, lhs_type.type_name.column))

            elif lhs_type.type_name.lexeme == 'bool' and matched_types and expr.op.lexeme in logical_ops:
                self.curr_type = DataType(False, Token(TokenType.BOOL_TYPE, 'bool', lhs_type.type_name.line, lhs_type.type_name.column))
            else:
                self.error("mismatched type - expr 2", rhs_type.type_name)
    
        if expr.not_op and self.curr_type.type_name.token_type != TokenType.BOOL_TYPE:
            self.error("expecting boolean expression", self.curr_type.type_name)


    def visit_data_type(self, data_type):
        # note: allowing void (bad cases of void caught by parser)
        name = data_type.type_name.lexeme
        if name == 'void' or name in BASE_TYPES or name in self.structs:
            self.curr_type = data_type
        else: 
            self.error(f'invalid type "{name}"', data_type.type_name)
            
    
    def visit_var_def(self, var_def):
        var_def.data_type.accept(self)
        if self.symbol_table.exists(var_def.var_name.lexeme):
            if self.symbol_table.exists_in_curr_env(var_def.var_name.lexeme):
                self.error("duplicate variable", var_def.var_name)
            else:
                shadowed_var_type = self.symbol_table.get(var_def.var_name.lexeme)
                if shadowed_var_type == var_def.data_type:
                    self.error("duplicate variable", var_def.var_name)
        self.symbol_table.add(var_def.var_name.lexeme, var_def.data_type)

  
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)


    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)


    def visit_simple_rvalue(self, simple_rvalue):
        value = simple_rvalue.value
        line = simple_rvalue.value.line
        column = simple_rvalue.value.column
        type_token = None 
        if value.token_type == TokenType.INT_VAL:
            type_token = Token(TokenType.INT_TYPE, 'int', line, column)
        elif value.token_type == TokenType.DOUBLE_VAL:
            type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
        elif value.token_type == TokenType.STRING_VAL:
            type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
        elif value.token_type == TokenType.BOOL_VAL:
            type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
        elif value.token_type == TokenType.NULL_VAL:
            type_token = Token(TokenType.VOID_TYPE, 'void', line, column)
        self.curr_type = DataType(False, type_token)


    def visit_new_rvalue(self, new_rvalue):
        new_type = None
        if new_rvalue.array_expr is not None:
            array_type = new_rvalue.type_name
            new_rvalue.array_expr.accept(self)
            if self.curr_type.type_name.lexeme != 'int':
                self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
            new_type = DataType(True, Token(array_type.token_type, array_type.lexeme, array_type.line, array_type.column))
        elif new_rvalue.struct_params is not None:
            if new_rvalue.type_name.lexeme not in self.structs:
                self.error("Type does not exist", self.curr_type.type_name)
            struct_def = self.structs[new_rvalue.type_name.lexeme]
            if len(new_rvalue.struct_params) != len(struct_def.fields):
                self.error("Incorrect number of parameters", self.curr_type.type_name)
            for i in range(len(new_rvalue.struct_params)):
                new_rvalue.struct_params[i].accept(self)
                if (self.curr_type.type_name.lexeme != struct_def.fields[i].data_type.type_name.lexeme) and self.curr_type.type_name.lexeme != 'void':
                    self.error("Parameter does not match type provided in struct definition", self.curr_type.type_name)
                if self.curr_type.is_array != struct_def.fields[i].data_type.is_array and self.curr_type.type_name.lexeme != 'void':
                    self.error("Expecting array type - new rvalue", self.curr_type.type_name)
            for struct_param in new_rvalue.struct_params:
                struct_param.accept(self)
            # need to build up the current type
            new_type = DataType(False, Token(TokenType.ID, new_rvalue.type_name.lexeme, new_rvalue.type_name.line, new_rvalue.type_name.column))
        
        self.curr_type = new_type


    def visit_var_rvalue(self, var_rvalue):
        type = self.symbol_table.get(var_rvalue.path[0].var_name.lexeme)
        if type is not None and type.type_name.lexeme in self.structs:
            # we know that we have a reference to a struct instance -- may not be final variable in path
            struct_def = self.structs[type.type_name.lexeme]
            if len(var_rvalue.path) > 1:
                for i in range(1, len(var_rvalue.path)):
                    field_exists = False
                    for field in struct_def.fields:
                        if field.var_name.lexeme == var_rvalue.path[i].var_name.lexeme:
                            field_exists = True
                            if field.data_type.is_array and i != len(var_rvalue.path)-1:
                                if var_rvalue.path[i].array_expr == None:
                                    self.error("expecting array expression - var rvalue", self.curr_type.type_name)
                            # check if it is another struct
                            if field.data_type.type_name.lexeme in self.structs:
                                struct_def = self.structs[field.data_type.type_name.lexeme]
                            self.curr_type = field.data_type
                            break 
                    if not field_exists:
                        self.error("Field does not exist in struct", self.curr_type.type_name)
            else:
                if var_rvalue.path[0].array_expr is not None:
                    # still need to implement array functionality
                    var_rvalue.path[0].array_expr.accept(self)
                    if self.curr_type.type_name.lexeme != 'int':
                        self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
                    self.curr_type = self.symbol_table.get(var_rvalue.path[0].var_name.lexeme)
                    self.curr_type.is_array = False
                else:
                    self.curr_type = self.symbol_table.get(var_rvalue.path[0].var_name.lexeme)
        else:
            for i in range(len(var_rvalue.path)):
                array_expr = False
                if not self.symbol_table.exists(var_rvalue.path[i].var_name.lexeme):
                    self.error("unrecognized variable - var rvalue", self.curr_type.type_name)
                if var_rvalue.path[i].array_expr is not None:
                    # still need to implement array functionality
                    var_rvalue.path[i].array_expr.accept(self)
                    if self.curr_type.type_name.lexeme != 'int':
                        self.error("Arguments to array expression must be of type int", self.curr_type.type_name)
                    array_expr = True
                if i == len(var_rvalue.path) - 1:
                    # only want to set the curr type on the last var ref in the path
                    type = self.symbol_table.get(var_rvalue.path[i].var_name.lexeme)
                    self.curr_type = DataType(type.is_array, type.type_name)
                    if array_expr:
                        self.curr_type.is_array = False
                    if array_expr:
                        self.curr_type.is_array = False
                    # set the type of the argument -- at this point we know we have a valid array and valid index type

