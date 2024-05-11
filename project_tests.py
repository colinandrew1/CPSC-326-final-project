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

# test below are example of when the garbage collector should not be invoked

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

# test below are example of when the garbage collector should be invoked

def test_single_array_deallocated_one_remains(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    my_fun(); \n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    array int ys = new int[7];  // 2025\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_many_array_allocs_one_goes(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array int ys = new int[5];  // 2025\n'
        '    my_fun();\n'
        '    array int zs = new int[5];  // 2027\n'
        '    array int as = new int[5];  // 2028\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    array int bs = new int[7];  // 2026\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2025, 2027, 2028]\n'

def test_many_stay_many_go_arrays(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array int ys = new int[5];  // 2025\n'
        '    my_fun();\n'
        '    array int zs = new int[5];  // 2029\n'
        '    array int as = new int[5];  // 2030\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    array int bs = new int[7];  // 2026\n'
        '    array int cs = new int[7];  // 2027\n'
        '    array int ds = new int[7];  // 2028\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2025, 2029, 2030]\n'

def test_single_struct_deallocated_one_remains(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(5, null); //2024\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    Node node2 = new Node(5, null); //2025\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: []\n'

def test_many_array_allocs_one_goes(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(5, null); //2024\n'
        '    Node node2 = new Node(5, null); //2025\n'
        '    my_fun(); \n'
        '    Node node3 = new Node(5, null); //2027\n'
        '    Node node4 = new Node(5, null); //2028\n'
        
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    Node node5 = new Node(5, null); //2026\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025, 2027, 2028] , array: []\n'

def test_many_stay_many_go_structs(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(5, null); //2024\n'
        '    Node node2 = new Node(5, null); //2025\n'
        '    my_fun(); \n'
        '    Node node3 = new Node(5, null); //2029\n'
        '    Node node4 = new Node(5, null); //2030\n'
        
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    Node node5 = new Node(5, null); //2026\n'
        '    Node node6 = new Node(5, null); //2027\n'
        '    Node node7 = new Node(5, null); //2028\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025, 2029, 2030] , array: []\n'

def test_return_array(capsys):
    program = (
        'void main() {\n'
        '    array int xs;\n'
        '    xs = my_fun();  //2024\n'
        '}\n'
        '\n'
        'array int my_fun() {\n'
        '    array int ys = new int[7];  // 2024\n'
        '    return ys;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_return_array_one_goes(capsys):
    program = (
        'void main() {\n'
        '    array int xs;\n'
        '    xs = create_array();  //2024\n'
        '}\n'
        '\n'
        'array int create_array() {\n'
        '    array int ys = new int[7];  // 2024\n'
        '    array int zs = new int[7];  // 2025\n'
        '    return ys;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_return_struct(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1;\n'
        '    node1 = create_node();  //2025\n'
        '}\n'
        '\n'
        'Node create_node() {\n'
        '    Node ys = new Node(5, null);  // 2024\n'
        '    Node zs = new Node(6, null);  // 2025\n'
        '    return zs;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2025] , array: []\n'

def test_path_expression_return(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array Node nodes = new Node[6];  // 2025\n'
        '    Node newer_node = create_new_node(); //2029\n'
        '}\n'
        '\n'
        'Node create_new_node() {\n'
        '    array int zs = new int[7];  // 2026\n'
        '    array int as = new int[8];  // 2027\n'
        '    Node new_node = new Node(1, new Node(2, new Node(3, new Node(4, null)))); // 2028, 2029, 2030, 2031\n'
        '    return new_node.next;   // 2029\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2029] , array: [2024, 2025]\n'

def test_return_array_and_set_field(capsys):
    program = (
        'struct ValAndList {\n'
        '    int val;\n'
        '    array int list;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    ValAndList x = new ValAndList(5, null);  // 2024\n'
        '    x.list = my_fun();    //2025\n'
        '}\n'
        '\n'
        'array int my_fun() {\n'
        '    array int zs = new int[7];  // 2025\n'
        '    array int as = new int[8];  // 2026\n'
        '    return zs;   // 2025\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: [2025]\n'

def test_array_allocs_in_for_loop(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    my_fun(); \n'
        '    array int ys = new int[5];  // 2030\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    for (int i = 0; i < 5; i = i+1) {\n'
        '        array int xs = new int[2];  //2025, 2026, 2027, 2028, 2029\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2030]\n'

def test_return_array_in_for_loop(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array int zs = my_fun();  // 2028\n'
        '    array int ys = new int[5];  // 2029\n'
        '}\n'
        '\n'
        'array int my_fun() {\n'
        '    for (int i = 0; i < 5; i = i+1) {\n'
        '        array int xs = new int[2];  //2025, 2026, 2027, 2028\n'
        '        if (i == 3) {\n'
        '            return xs;  //2028\n'
        '        }\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2028, 2029]\n'

def test_alloc_in_while_loop(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    my_fun(); \n'
        '    array int ys = new int[5];  // 2030\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    int i = 0;\n'
        '    while (i < 5) {\n'
        '        array int xs = new int[2];  //2025, 2026, 2027, 2028, 2029\n'
        '        i = i + 1;\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2030]\n'

def test_return_array_in_while_loop(capsys):
    program = (
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array int zs = my_fun();    // 2028\n'
        '    array int ys = new int[5];  // 2029\n'
        '}\n'
        '\n'
        'array int my_fun() {\n'
        '    int i = 0;\n'
        '    while (i < 5) {\n'
        '        array int xs = new int[2];  //2025, 2026, 2027, 2028\n'
        '        if (i == 3) {\n'
        '            return xs;  // 2028\n'
        '        }\n'
        '        i = i + 1;\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2028, 2029]\n'

def test_return_struct_with_path(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    array int xs = new int[5];  // 2024\n'
        '    array Node nodes = new Node[6];  // 2025\n'
        '    Node newer_node = create_new_node(); // 2028, 2029, 2030, 2031\n'
        '}\n'
        '\n'
        'Node create_new_node() {\n'
        '    array int zs = new int[7];  // 2026\n'
        '    array int as = new int[8];  // 2027\n'
        '    Node new_node = new Node(1, new Node(2, new Node(3, new Node(4, null)))); // 2028, 2029, 2030, 2031\n'
        '    return new_node;   // 2028, 2029, 2030, 2031\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2028, 2029, 2030, 2031] , array: [2024, 2025]\n'

def test_nested_functions_no_return(capsys):
    program = (
        'void main() {\n'
        '    int x = 0;\n'
        '    array string xs = new string[2];   //2024 \n'
        '    my_fun();\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    array string ys = new string[2]; //2025\n'
        '    my_other_fun();\n'
        '}\n'
        '\n'
        'void my_other_fun() {\n'
        '    array string zs = new string[2]; //2026\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_nested_functions_inner_most_returns_but_not_to_main(capsys):
    program = (
        'void main() {\n'
        '    int x = 0;\n'
        '    array string xs = new string[2];   //2024 \n'
        '    my_fun();\n'
        '}\n'
        '\n'
        'void my_fun() {\n'
        '    array string ys = new string[2]; //2025 \n'
        '    array string as = my_other_fun(); //2026 \n'
        '}\n'
        '\n'
        'array string my_other_fun() {\n'
        '    array string zs = new string[2]; //2026 \n'
        '    return zs;\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024]\n'

def test_inner_returns_array_back_to_main(capsys):
    program = (
        'void main() {\n'
        '    int x = 0;\n'
        '    array string xs = new string[2]; //2024\n'
        '    array string js = my_fun();\n'
        '}\n'
        '\n'
        'array string my_fun() {\n'
        '    array string ys = new string[2]; //2025\n'
        '    array string cs = my_other_fun(); //2026\n'
        '    return cs; //2026\n'
        '}\n'
        '\n'
        'array string my_other_fun() {\n'
        '    array string zs = new string[2]; //2026\n'
        '    return zs; //2026\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [] , array: [2024, 2026]\n'

def test_set_struct_field(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(1, null); // 2024\n'
        '    set_next(node1);\n'
        '}\n'
        '\n'
        'void set_next(Node n) {\n'
        '    n.next = new Node(2, null); // 2025\n'
        '    Node node2 = new Node(3, null); // 2026\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025] , array: []\n'

def test_multi_layer_set_field(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(1, null); // 2024\n'
        '    set_next(node1);\n'
        '}\n'
        '\n'
        'void set_next(Node n) {\n'
        '    n.next = new Node(2, null); // 2025\n'
        '    Node node2 = new Node(3, null); // 2026\n'
        '    set_next_next(n);\n'
        '}\n'
        '\n'
        'void set_next_next(Node n) {\n'
        '    n.next.next = new Node(3, null);    // 2027\n'
        '    Node node3 = new Node(4, null); // 2028\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025, 2027] , array: []\n'

def test_conditional_set_field_true(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(1, null); // 2024\n'
        '    my_fun(node1, 5);   // 2025\n'
        '}\n'
        '\n'
        'void my_fun(Node n, int val) {\n'
        '    if (val == 5) {\n'
        '        n.next = new Node(2, null); // 2025\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024, 2025] , array: []\n'

def test_conditional_set_field_false(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    Node node1 = new Node(1, null); // 2024\n'
        '    my_fun(node1, 6);  \n'
        '}\n'
        '\n'
        'void my_fun(Node n, int val) {\n'
        '    if (val == 5) {\n'
        '        n.next = new Node(2, null); // 2025\n'
        '    }\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: []\n'

def test_array_of_structs(capsys):
    program = (
        'struct Node {\n'
        '    int val;\n'
        '    Node next;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    array Node nodes = new Node[3]; //2024\n'
        '    my_fun(nodes);  // 2025, 2026, 2027, 2028\n'
        '}\n'
        '\n'
        'void my_fun(array Node nodes) {\n'
        '    nodes[0] = new Node(1, null);   // 2025\n'
        '    nodes[1] = new Node(2, null);   // 2026\n'
        '    nodes[2] = new Node(3, null);   // 2027\n'
        '    nodes[2].next = new Node(4, null);  // 2028\n'
        '    array int xs = new int[1];  // 2029\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2025, 2026, 2027, 2028] , array: [2024]\n'

def test_struct_of_arrays(capsys):
    program = (
        'struct ArrayCollection {\n'
        '    array int xs;\n'
        '    array string ys;\n'
        '    array bool zs;\n'
        '    array double js;\n'
        '}\n'
        '\n'
        'void main() {\n'
        '    ArrayCollection ac = new ArrayCollection(null,null,null,null);  // 2024\n'
        '    ac.xs = set_int_array(); // 2026\n'
        '    ac.ys = set_string_array(); // 2028\n'
        '    ac.zs = set_bool_array(); // 2030\n'
        '    ac.js = set_double_array(); // 2032\n'
        '}\n'
        '\n'
        'array int set_int_array() {\n'
        '    array int a = new int[1];   // 2025\n'
        '    return new int[1];  // 2026\n'
        '}\n'
        '\n'
        'array string set_string_array() {\n'
        '    array string a = new string[1];    // 2027\n'
        '    return new string[1];   // 2028\n'
        '}\n'
        '\n'
        'array bool set_bool_array() {\n'
        '    array bool a = new bool[1]; // 2029\n'
        '    return new bool[1]; // 2030\n'
        '}\n'
        '\n'
        'array double set_double_array() {\n'
        '    array double a = new double[1]; // 2031\n'
        '    return new double[1];   // 2032\n'
        '}\n'
    )
    build(program).run()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == 'struct: [2024] , array: [2026, 2028, 2030, 2032]\n'

