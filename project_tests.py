"""Unit tests for CPSC 326 Final Project - Mark and Sweep Garbage Collector. 


NAME: Colin McClelland
DATE: Spring 2024
CLASS: CPSC 326

These unit tests examine the value of the struct heap and the array heap at the termination of the program


"""

import pytest
import io

from mypl_error import *
from mypl_iowrapper import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast_parser import *
from mypl_var_table import *
from mypl_code_gen import *
from mypl_vm import *

def build(program):
    in_stream = FileWrapper(io.StringIO(program))
    vm = VM()
    cg = CodeGenerator(vm)
    ASTParser(Lexer(FileWrapper(io.StringIO(program)))).parse().accept(cg)
    return vm

def test_no_heap_allocated_objects(capsys):
    program = (
        'void main() {\n'
        '    int x = 0;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: []\n'

def test_no_hep_allocs_but_struct_def_present(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        'void main() {\n'
        '    int x = 0;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: []\n'
    
def test_simple_int_array(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  //2024 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_simple_int_array_and_statically_allocated_variable(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  //2024 \n'
        '    int x = 5; \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_two_simple_int_arrays(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  //2024 \n'
        '    array int ys = new int[5];  //2025 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2025]\n'

def test_three_simple_int_arrays(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  //2024 \n'
        '    array int ys = new int[5];  //2025 \n'
        '    array int zs = new int[5];  //2026 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2025, 2026]\n'

def test_simple_struct_alloc(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);    //2024 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: []\n'

def test_simple_struct_alloc_with_statically_allocated_variable(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);    //2024 \n'
        '    int x = 5; \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: []\n'

def test_two_simple_struct_allocs(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);    //2024 \n'
        '    MyInt x = new MyInt(6);    //2025 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025] , array: []\n'

def test_three_simple_struct_alloc(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);//2024 \n'
        '    MyInt x = new MyInt(6);//2025 \n'
        '    MyInt x = new MyInt(7);//2026 \n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025, 2026] , array: []\n'

def test_simple_struct_alloc_and_simple_array_alloc(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);    //2024 \n'
        '    array int xs = new int[5];  //2025 \n'

        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: [2025]\n'

def test_many_simple_struct_alloc_and_simple_array_alloc(capsys):
    program = (
        'struct MyInt {\n'
        '    int val;\n'
        '}\n'
        'void main() {\n'
        '    MyInt x = new MyInt(5);    //2024 \n'
        '    array int xs = new int[5];  //2025 \n'
        '    MyInt y = new MyInt(5);    //2026 \n'
        '    array int ys = new int[5];  //2027 \n'
        '    MyInt z = new MyInt(5);    //2028 \n'
        '    array int zs = new int[5];  //2029 \n'
        '    MyInt f = new MyInt(5);    //2030 \n'
        '    array int fs = new int[5];  //2031 \n'

        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2026, 2028, 2030] , array: [2025, 2027, 2029, 2031]\n'

# def test_array_alloc_in_loop(capsys):
#     program = (
#         'void main() {\n'
#         '    for (int i = 0; i < 5; i = i + 1) {\n'
#         '        array int xs = new int[i];\n'
#         '    }\n'
#         '}\n'
#     )
#     build(program).run()
#     captured = capsys.readouterr()
#     print(captured.out)
#     assert captured.out == 'struct: [] , array: [2024, 2025, 2026, 2027, 2028]\n'

# def test_struct_alloc_in_loop(capsys):
#     program = (
#         'struct MyInt {\n'
#         '    int val;\n'
#         '}\n'
#         'void main() {\n'
#         '    for (int i = 0; i < 5; i = i + 1) {\n'
#         '        MyInt x = new MyInt(5);\n'
#         '    }\n'
#         '}\n'
#     )
#     build(program).run()
#     captured = capsys.readouterr()
#     print(captured.out)
#     assert captured.out == 'struct: [2024, 2025, 2026, 2027, 2028] , array: []\n'
