"""Implementation of the MyPL Virtual Machine (VM).

NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_error import *
from mypl_opcode import *
from mypl_frame import *


class HeapObject:
    def __init__(self, oid):
        self.oid = oid
        self.parents = [] 
        self.references = []
    
    def add_parent(self, parent):
        self.parents.append(parent)

    def add_reference(self, ref):
        self.references.append(ref)

    def __repr__(self):
        string_representation = " parents: " + str(self.parents) + " references: " + str(self.references)
        return string_representation
        

class VM:

    def __init__(self):
        """Creates a VM."""
        self.struct_heap = {}        # id -> dict
        self.array_heap = {}         # id -> list
        self.next_obj_id = (2024, "heap_object")      # next available object id (int)
        self.frame_templates = {}    # function name -> VMFrameTemplate
        self.call_stack = []         # function call stack
        self.call_stack_id = 0
        self.root_set = []
        self.object_graph = {}
        self.yellow_light_from_return = False


    def run_garbage_collector(self):
        initial_marked_objects = self.get_parents()
        parents = initial_marked_objects[0]
        marked_objects = list(self.mark_phase(parents)) + initial_marked_objects[1]
        self.sweep_phase(marked_objects)
        

    def mark_phase(self, parents):
        marked_objects = set()
        for obj_id in parents:
            marked_objects.add(obj_id)
            marked = set(self.get_references(obj_id))
            marked_objects = marked_objects | marked
        return marked_objects


    def get_references(self, obj_id):
        marked_objects = []
        root = self.object_graph[obj_id]
        if root.references == []:
            return []
        else:
            for ref in root.references:
                marked_objects.append(ref)
                marked_objects += self.get_references(ref)
        return marked_objects
                 

    def sweep_phase(self, marked_objects):
        # print(self.struct_heap.keys())
        struct_keys = [key[0] for key in self.struct_heap.keys()]
        array_keys = [key[0] for key in self.array_heap.keys()]
        object_graph_copy = self.object_graph.copy()
        for key in object_graph_copy:
            if key not in marked_objects:
                if key in struct_keys:
                    del self.struct_heap[(key,"heap_object")]
                if key in array_keys:
                    del self.array_heap[(key,"heap_object")]
                del self.object_graph[key]
        # print(self.struct_heap)
        # print("******************")


    def get_parents(self):
        parents = []
        referenced_children = []
        self.root_set = list(set(self.root_set))
        for i in range(len(self.root_set)):
            obj_id = self.root_set[i][1]
            if len(self.object_graph[obj_id].parents) == 0:
                parents.append(obj_id)
            else:
                referenced_children.append(obj_id)
        return (parents, referenced_children)


    def clean_root_set(self, call_stack_id):
        # make sure this works as expected - i think it should be fine
        root_set_copy = self.root_set[:]
        for obj in root_set_copy:
            if obj[0] == call_stack_id:
                self.root_set.remove(obj)



        
    def __repr__(self):
        """Returns a string representation of frame templates."""
        s = ''
        for name, template in self.frame_templates.items():
            s += f'\nFrame {name}\n'
            for i in range(len(template.instructions)):
                s += f'  {i}: {template.instructions[i]}\n'
        return s

    
    def add_frame_template(self, template):
        """Add the new frame info to the VM. 

        Args: 
            frame -- The frame info to add.

        """
        self.frame_templates[template.function_name] = template

    
    def error(self, msg, frame=None):
        """Report a VM error."""
        if not frame:
            raise VMError(msg)
        pc = frame.pc - 1
        instr = frame.template.instructions[pc]
        name = frame.template.function_name
        msg += f' (in {name} at {pc}: {instr})'
        raise VMError(msg)

    
    #----------------------------------------------------------------------
    # RUN FUNCTION
    #----------------------------------------------------------------------
    
    def run(self, debug=False):
        """Run the virtual machine."""

        # grab the "main" function frame and instantiate it
        if not 'main' in self.frame_templates:
            self.error('No "main" functrion')
        frame = VMFrame(self.frame_templates['main'])
        self.call_stack.append(frame)


        # run loop (continue until run out of call frames or instructions)
        while self.call_stack and frame.pc < len(frame.template.instructions):
            # get the next instruction
            instr = frame.template.instructions[frame.pc]
            # increment the program count (pc)
            frame.pc += 1
            # for debugging:
            if debug:
                print('\n')
                print('\t FRAME.........:', frame.template.function_name)
                print('\t PC............:', frame.pc)
                print('\t INSTRUCTION...:', instr)
                val = None if not frame.operand_stack else frame.operand_stack[-1]
                print('\t NEXT OPERAND..:', val)
                cs = self.call_stack
                fun = cs[-1].template.function_name if cs else None
                print('\t NEXT FUNCTION..:', fun)

            # print(instr.opcode)
            
            #------------------------------------------------------------
            # Literals and Variables
            #------------------------------------------------------------
            

            if instr.opcode == OpCode.PUSH:
                frame.operand_stack.append(instr.operand)

            elif instr.opcode == OpCode.POP:
                frame.operand_stack.pop()

            elif instr.opcode == OpCode.LOAD:
                val = frame.variables[instr.operand]
                frame.operand_stack.append(val)
        
            elif instr.opcode == OpCode.STORE:
                val = frame.operand_stack.pop()
                if instr.operand <= len(frame.variables) - 1:
                    frame.variables[instr.operand] = val
                else:
                    frame.variables.append(val)

                if type(val) == tuple:
                    self.root_set.append((self.call_stack_id, val[0]))

                # print(val)

                if self.yellow_light_from_return:
                    if type(val) == tuple:
                        self.root_set.append((self.call_stack_id, val[0]))
                    self.run_garbage_collector()
                    self.yellow_light_from_return = False

            #------------------------------------------------------------
            # Operations
            #------------------------------------------------------------

            elif instr.opcode == OpCode.ADD:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in arithmetic operations")
                frame.operand_stack.append(y+x)
            
            elif instr.opcode == OpCode.SUB:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in arithmetic operations")
                frame.operand_stack.append(y-x)

            elif instr.opcode == OpCode.MUL:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in arithmetic operations")
                frame.operand_stack.append(y*x)

            elif instr.opcode == OpCode.DIV:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == 0:
                    self.error("Division by zero error")
                if x == None or y == None:
                    self.error("null cannot be used in arithmetic operations")
                if type(x) == int and type(y) == int:
                    frame.operand_stack.append(y//x)
                else:
                    frame.operand_stack.append(y/x)
            
            elif instr.opcode == OpCode.AND:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in logical operations")
                frame.operand_stack.append(y and x)

            elif instr.opcode == OpCode.OR:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in logical operations")
                frame.operand_stack.append(y or x)

            elif instr.opcode == OpCode.NOT:
                x = frame.operand_stack.pop()
                if x == None:
                    self.error("null cannot be used in logical operations")
                frame.operand_stack.append(not x)

            elif instr.opcode == OpCode.CMPLT:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in operations")
                frame.operand_stack.append(y < x)

            elif instr.opcode == OpCode.CMPLE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("null cannot be used in operations")
                frame.operand_stack.append(y <= x)

            elif instr.opcode == OpCode.CMPEQ:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                frame.operand_stack.append(y == x)

            elif instr.opcode == OpCode.CMPNE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                frame.operand_stack.append(y != x)


            #------------------------------------------------------------
            # Branching
            #------------------------------------------------------------

            elif instr.opcode == OpCode.JMP:
                frame.pc = instr.operand

            elif instr.opcode == OpCode.JMPF:
                val = frame.operand_stack.pop()
                if val == False:
                    frame.pc = instr.operand
            
                    
            #------------------------------------------------------------
            # Functions
            #------------------------------------------------------------

            elif instr.opcode == OpCode.CALL:
                callee_name = instr.operand
                callee_template = self.frame_templates[callee_name]
                callee_frame = VMFrame(callee_template)
                self.call_stack.append(callee_frame)
                for i in range(callee_template.arg_count):
                    arg = frame.operand_stack.pop()
                    callee_frame.operand_stack.append(arg)
                frame = callee_frame
                self.call_stack_id += 1

            elif instr.opcode == OpCode.RET:
                return_val = frame.operand_stack.pop()
                self.call_stack.pop()
                if len(self.call_stack) > 0:
                    frame = self.call_stack[-1]
                    frame.operand_stack.append(return_val)
                    self.clean_root_set(self.call_stack_id)
                    self.call_stack_id -= 1
                    if frame.template.instructions[frame.pc].opcode in [OpCode.STORE, OpCode.SETF, OpCode.SETI]:
                        self.yellow_light_from_return = True
                    else:
                        self.run_garbage_collector()


            
            #------------------------------------------------------------
            # Built-In Functions
            #------------------------------------------------------------

            elif instr.opcode == OpCode.WRITE:
                val = frame.operand_stack.pop()
                if type(val) == bool:
                    if val == True:
                        val = 'true'
                    elif val == False:
                        val = 'false'
                if val == None:
                    print('null', end='')
                else:
                    print(val, end='')
            
            elif instr.opcode == OpCode.READ:
                val = input()
                frame.operand_stack.append(val)
            
            elif instr.opcode == OpCode.LEN:
                obj = frame.operand_stack.pop()
                if obj == None:
                    self.error("argument to len cannot be null")
                if type(obj) == str:
                    frame.operand_stack.append(len(obj))
                else:
                    array = self.array_heap[obj]
                    frame.operand_stack.append(len(array))

            elif instr.opcode == OpCode.GETC:
                string = frame.operand_stack.pop()
                idx = frame.operand_stack.pop()
                if idx == None:
                    self.error("index cannot be null")
                if string == None:
                    self.error("string cannot be null")
                if (idx < 0 or idx > len(string)-1):
                    self.error("index out of bounds")
                frame.operand_stack.append(string[idx])

            elif instr.opcode == OpCode.TOINT:
                val = frame.operand_stack.pop()
                if val == None:
                    self.error("argument cannot be null")
                try:
                    frame.operand_stack.append(int(val))
                except ValueError:
                    self.error("invalid argument")

            elif instr.opcode == OpCode.TODBL:
                val = frame.operand_stack.pop()
                if val == None:
                    self.error("argument cannot be null")
                try:
                    frame.operand_stack.append(float(val))
                except ValueError:
                    self.error("invalid argument")

            elif instr.opcode == OpCode.TOSTR:
                val = frame.operand_stack.pop()
                if val == None:
                    self.error("argument cannot be null")
                try:
                    frame.operand_stack.append(str(val))
                except ValueError:
                    self.error("invalid argument")

            
            #------------------------------------------------------------
            # Heap
            #------------------------------------------------------------

            elif instr.opcode == OpCode.ALLOCS:
                self.struct_heap[self.next_obj_id] = {}
                # print(self.struct_heap)
                frame.operand_stack.append(self.next_obj_id)
                self.object_graph[self.next_obj_id[0]] = HeapObject(self.next_obj_id[0])
                self.next_obj_id = (self.next_obj_id[0]+1,"heap_object")


            elif instr.opcode == OpCode.SETF:
                val = frame.operand_stack.pop()
                # print(val, instr.operand)
                oid = frame.operand_stack.pop()
                oid_num = oid[0]
                val_num = None
                if oid == None:
                    self.error("null object")
                if type(val) == tuple:
                    val_num = val[0]
                    self.struct_heap[oid][instr.operand] = val
                    self.object_graph[oid_num].add_reference(val_num)
                    self.object_graph[val_num].add_parent(oid_num)
                    # print(val_num)
                else:
                    self.struct_heap[oid][instr.operand] = val
                # print(self.object_graph)
                # print(self.struct_heap)
                #print("val", val)

                #print("*************************")

                if self.yellow_light_from_return:
                    if type(val) == tuple:
                        self.root_set.append((self.call_stack_id, val[0]))
                    self.run_garbage_collector()
                    self.yellow_light_from_return = False


            elif instr.opcode == OpCode.GETF:
                oid = frame.operand_stack.pop()
                oid_num = None
                if type(oid) == tuple:
                    oid_num = oid[0]
                if oid == None:
                    self.error("null object")
                if oid_num is not None:
                    frame.operand_stack.append(self.struct_heap[oid][instr.operand])
                    # print(self.struct_heap[oid_num][instr.operand])
                else:
                    frame.operand_stack.append(self.struct_heap[oid][instr.operand])
                    # print(self.struct_heap[oid][instr.operand])


            elif instr.opcode == OpCode.ALLOCA:
                oid = self.next_obj_id
                array_len = frame.operand_stack.pop()
                if(array_len == None):
                    self.error("array length cannot be null")
                elif (array_len < 0):
                    self.error("array length cannot be negative")
                self.array_heap[oid] = [None for _ in range(array_len)]
                frame.operand_stack.append(self.next_obj_id)
                # self.object_graph[oid] = HeapObject(oid)
                self.object_graph[self.next_obj_id[0]] = HeapObject(self.next_obj_id[0])
                self.next_obj_id = (self.next_obj_id[0]+1,"heap_object")


            elif instr.opcode == OpCode.SETI:
                val = frame.operand_stack.pop()
                idx = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()
                oid_num = oid[0]
                val_num = None
                if (oid == None):
                    self.error("array cannot be null")
                if(idx == None):
                    self.error("index cannot be null")
                elif (idx < 0 or idx > len(self.array_heap[oid])-1):
                    self.error("array index out of bounds")
                if type(val) == tuple:
                    val_num = val[0]
                    self.array_heap[oid][idx] = val
                    self.object_graph[oid_num].add_reference(val_num)
                    self.object_graph[val_num].add_parent(oid_num)
                else:
                    self.array_heap[oid][idx] = val

                if self.yellow_light_from_return:
                    if type(val) == tuple:
                        self.root_set.append((self.call_stack_id, val[0]))
                    self.run_garbage_collector()
                    self.yellow_light_from_return = False


            elif instr.opcode == OpCode.GETI:
                idx = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()
                oid_num = oid[0]
                if (oid == None):
                    self.error("array cannot be null")
                if(idx == None):
                    self.error("index cannot be null")
                elif (idx < 0 or idx > len(self.array_heap[oid_num])-1):
                    self.error("index out of bounds")
                val = self.array_heap[oid][idx]
                frame.operand_stack.append(val)
            
            #------------------------------------------------------------
            # Special 
            #------------------------------------------------------------

            elif instr.opcode == OpCode.DUP:
                x = frame.operand_stack.pop()
                frame.operand_stack.append(x)
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.NOP:
                # do nothing
                pass

            else:
                self.error(f'unsupported operation {instr}')

        print()
        print("struct", [key[0] for key in self.struct_heap.keys()])
        print("struct", [key[0] for key in self.array_heap.keys()])