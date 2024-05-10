"""IR code generator for converting MyPL to VM Instructions. 

NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_ast import *
from mypl_var_table import *
from mypl_frame import *
from mypl_opcode import *
from mypl_vm import *


class CodeGenerator (Visitor):

    def __init__(self, vm):
        """Creates a new Code Generator given a VM. 
        
        Args:
            vm -- The target vm.
        """
        # the vm to add frames to
        self.vm = vm
        # the current frame template being generated
        self.curr_template = None
        # for var -> index mappings wrt to environments
        self.var_table = VarTable()
        # struct name -> StructDef for struct field info
        self.struct_defs = {}

    
    def add_instr(self, instr):
        """Helper function to add an instruction to the current template."""
        self.curr_template.instructions.append(instr)

        
    def visit_program(self, program):
        for struct_def in program.struct_defs:
            struct_def.accept(self)
        for fun_def in program.fun_defs:
            fun_def.accept(self)

    
    def visit_struct_def(self, struct_def):
        # remember the struct def for later
        self.struct_defs[struct_def.struct_name.lexeme] = struct_def

        
    def visit_fun_def(self, fun_def):

        self.curr_template = VMFrameTemplate(fun_def.fun_name.lexeme, len(fun_def.params), [])
        self.var_table.push_environment()

        for i in range(len(fun_def.params)):
            self.var_table.add(fun_def.params[i].var_name.lexeme)
            self.add_instr(STORE(i))
        
        for stmt in fun_def.stmts:
            stmt.accept(self)
        
        if fun_def.return_type.type_name.lexeme == 'void':
            self.add_instr(PUSH(None))
            self.add_instr(RET())

        self.var_table.pop_environment()

        # for instr in self.curr_template.instructions:
        #     print(instr)

        self.vm.add_frame_template(self.curr_template)
  
    
    def visit_return_stmt(self, return_stmt):
        return_stmt.expr.accept(self)
        self.add_instr(RET())

        
    def visit_var_decl(self, var_decl):
        if var_decl.expr.first is not None:
            var_decl.expr.accept(self)
        else:
            self.add_instr(PUSH(None))
        self.var_table.add(var_decl.var_def.var_name.lexeme)
        address = self.var_table.get(var_decl.var_def.var_name.lexeme)
        self.add_instr(STORE(address))

    
    def visit_assign_stmt(self, assign_stmt):
        address = self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme)
        if len(assign_stmt.lvalue) == 1:
            if assign_stmt.lvalue[0].array_expr is not None:
                self.add_instr(LOAD(address))
                assign_stmt.lvalue[0].array_expr.accept(self)
                assign_stmt.expr.accept(self)
                self.add_instr(SETI())
            else:
                assign_stmt.expr.accept(self)
                address = self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme)
                self.add_instr(STORE(address))

        else:
            self.add_instr(LOAD(address))
            if assign_stmt.lvalue[0].array_expr is not None:
                assign_stmt.lvalue[0].array_expr.accept(self)
                self.add_instr(GETI())

            for i in range(1, len(assign_stmt.lvalue)):
                if i == len(assign_stmt.lvalue)-1:
                    if assign_stmt.lvalue[i].array_expr is not None:
                        # could still have a path expression:  n.next[0]
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme))
                        assign_stmt.lvalue[i].array_expr.accept(self)
                        assign_stmt.expr.accept(self)
                        self.add_instr(SETI())
                    else:
                        assign_stmt.expr.accept(self)
                        self.add_instr(SETF(assign_stmt.lvalue[i].var_name.lexeme))
                else:
                    if assign_stmt.lvalue[i].array_expr is not None:
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme))
                        assign_stmt.lvalue[i].array_expr.accept(self)
                        self.add_instr(GETI())
                    else:
                        self.add_instr(GETF(assign_stmt.lvalue[i].var_name.lexeme))


    def visit_while_stmt(self, while_stmt):
        start_idx = len(self.curr_template.instructions)
        while_stmt.condition.accept(self)
        self.add_instr(JMPF(-1))
        jmpf_idx = len(self.curr_template.instructions) - 1
        self.var_table.push_environment()
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()
        self.add_instr(JMP(start_idx))
        self.add_instr(NOP())
        nop_idx = len(self.curr_template.instructions) - 1
        self.curr_template.instructions[jmpf_idx].operand = nop_idx

        
    def visit_for_stmt(self, for_stmt):
        self.var_table.push_environment()
        for_stmt.var_decl.accept(self)
        start_idx = len(self.curr_template.instructions)
        for_stmt.condition.accept(self)
        self.add_instr(JMPF(-1))
        jmpf_idx = len(self.curr_template.instructions) - 1
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        for_stmt.assign_stmt.accept(self)
        self.var_table.pop_environment()
        self.add_instr(JMP(start_idx))
        self.add_instr(NOP())
        nop_idx = len(self.curr_template.instructions) - 1
        self.curr_template.instructions[jmpf_idx].operand = nop_idx

    def visit_if_stmt(self, if_stmt):
        if_stmt.if_part.condition.accept(self)
        self.add_instr(JMPF(-1))
        if_jmpf_idx = len(self.curr_template.instructions) - 1
        self.var_table.push_environment()
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()
        self.add_instr(JMP(-1)) # after the if body executes, go to very end past else if and else
        if_jmp_idx = len(self.curr_template.instructions) - 1
        self.add_instr(NOP())
        if_nop_idx = len(self.curr_template.instructions) - 1
        self.curr_template.instructions[if_jmpf_idx].operand = if_nop_idx

        else_if_indexes = []
        for else_if_block in if_stmt.else_ifs:
            else_if_block.condition.accept(self)
            self.add_instr(JMPF(-1))
            elif_jmpf_idx = len(self.curr_template.instructions) - 1
            self.var_table.push_environment()
            for stmt in else_if_block.stmts:
                stmt.accept(self)
            self.var_table.pop_environment()
            self.add_instr(JMP(-1)) # jump to the very end if we enter the body of an elseif
            elseif_jmp_idx = len(self.curr_template.instructions) - 1
            self.add_instr(NOP())
            elif_nop_idx = len(self.curr_template.instructions) - 1
            self.curr_template.instructions[elif_jmpf_idx].operand = elif_nop_idx
            else_if_indexes.append(elseif_jmp_idx)

        self.var_table.push_environment()
        for stmt in if_stmt.else_stmts:
            stmt.accept(self)
        self.var_table.pop_environment()

        self.add_instr(NOP())
        else_nop_idx = len(self.curr_template.instructions) - 1
        self.curr_template.instructions[if_jmp_idx].operand = else_nop_idx
        for i in range(len(else_if_indexes)):
            self.curr_template.instructions[else_if_indexes[i]].operand = else_nop_idx
        

    def visit_call_expr(self, call_expr):
        if call_expr.fun_name.lexeme == 'print':
            call_expr.args[0].accept(self)
            self.add_instr(WRITE())
        elif call_expr.fun_name.lexeme == 'input':
            self.add_instr(READ())
        elif call_expr.fun_name.lexeme == 'itos':
            call_expr.args[0].accept(self)
            self.add_instr(TOSTR())
        elif call_expr.fun_name.lexeme == 'dtos':
            call_expr.args[0].accept(self)
            self.add_instr(TOSTR())
        elif call_expr.fun_name.lexeme == 'stoi':
            call_expr.args[0].accept(self)
            self.add_instr(TOINT())
        elif call_expr.fun_name.lexeme == 'dtoi':
            call_expr.args[0].accept(self)
            self.add_instr(TOINT())
        elif call_expr.fun_name.lexeme == 'itod':
            call_expr.args[0].accept(self)
            self.add_instr(TODBL())
        elif call_expr.fun_name.lexeme == 'stod':
            call_expr.args[0].accept(self)
            self.add_instr(TODBL())
        elif call_expr.fun_name.lexeme == 'length':
            call_expr.args[0].accept(self)
            self.add_instr(LEN())
        elif call_expr.fun_name.lexeme == 'get':
            call_expr.args[0].accept(self)
            call_expr.args[1].accept(self)
            self.add_instr(GETC())
        else:
            for i in range(len(call_expr.args)):
                call_expr.args[i].accept(self)
            self.add_instr(CALL(call_expr.fun_name.lexeme))

        
    def visit_expr(self, expr):
        if (expr.op is not None) and (expr.op.lexeme == '>' or expr.op.lexeme == '>='):
            expr.rest.accept(self)
        else:
            expr.first.accept(self)

        if expr.op is not None:
            if expr.op.lexeme == '>' or expr.op.lexeme == '>=':
                expr.first.accept(self)
            else:
                expr.rest.accept(self)
            
            if expr.op.lexeme == '+':
                self.add_instr(ADD())
            elif expr.op.lexeme == '-':
                self.add_instr(SUB())
            elif expr.op.lexeme == '*':
                self.add_instr(MUL())
            elif expr.op.lexeme == '/':
                self.add_instr(DIV())
            elif expr.op.lexeme == 'and':
                self.add_instr(AND())
            elif expr.op.lexeme == 'or':
                self.add_instr(OR())
            elif expr.op.lexeme == '==':
                self.add_instr(CMPEQ())
            elif expr.op.lexeme == '!=':
                self.add_instr(CMPNE())
            elif expr.op.lexeme == '<' or expr.op.lexeme == '>':
                self.add_instr(CMPLT())
            elif expr.op.lexeme == '<=' or expr.op.lexeme == '>=':
                self.add_instr(CMPLE()) 

        if expr.not_op:
            self.add_instr(NOT())
            

    def visit_data_type(self, data_type):
        # nothing to do here
        pass

    
    def visit_var_def(self, var_def):
        # nothing to do here
        pass

    
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)

        
    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)

        
    def visit_simple_rvalue(self, simple_rvalue):
        val = simple_rvalue.value.lexeme
        if simple_rvalue.value.token_type == TokenType.INT_VAL:
            self.add_instr(PUSH(int(val)))
        elif simple_rvalue.value.token_type == TokenType.DOUBLE_VAL:
            self.add_instr(PUSH(float(val)))
        elif simple_rvalue.value.token_type == TokenType.STRING_VAL:
            val = val.replace('\\n', '\n')
            val = val.replace('\\t', '\t')
            self.add_instr(PUSH(val))
        elif val == 'true':
            self.add_instr(PUSH(True))
        elif val == 'false':
            self.add_instr(PUSH(False))
        elif val == 'null':
            self.add_instr(PUSH(None))


    def visit_new_rvalue(self, new_rvalue):
        # struct
        if new_rvalue.array_expr is None:
            self.add_instr(ALLOCS())
            for i in range(len(new_rvalue.struct_params)):
                self.add_instr(DUP())
                new_rvalue.struct_params[i].accept(self)
                self.add_instr(SETF(self.struct_defs[new_rvalue.type_name.lexeme].fields[i].var_name.lexeme))
        # array
        else:
            new_rvalue.array_expr.accept(self)
            self.add_instr(ALLOCA())


    def visit_var_rvalue(self, var_rvalue):
        address = self.var_table.get(var_rvalue.path[0].var_name.lexeme)
        if len(var_rvalue.path) == 1:
            if var_rvalue.path[0].array_expr is not None:
                self.add_instr(LOAD(address))
                var_rvalue.path[0].array_expr.accept(self)
                self.add_instr(GETI())
            else:
                self.add_instr(LOAD(address))
                
        else:
            self.add_instr(LOAD(address))
            if var_rvalue.path[0].array_expr is not None:
                var_rvalue.path[0].array_expr.accept(self)
                self.add_instr(GETI())

            for i in range(1, len(var_rvalue.path)):
                if i == len(var_rvalue.path)-1:
                    if var_rvalue.path[i].array_expr is not None:
                        # could still have a path expression:  n.next[0]
                        self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme))
                        var_rvalue.path[i].array_expr.accept(self)
                        self.add_instr(GETI())
                    else:
                        self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme))
                else:
                    if var_rvalue.path[i].array_expr is not None:
                        self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme))
                        var_rvalue.path[i].array_expr.accept(self)
                        self.add_instr(GETI())
                    else:
                        self.add_instr(GETF(var_rvalue.path[i].var_name.lexeme))
