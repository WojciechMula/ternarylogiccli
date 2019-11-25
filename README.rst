================================================================================
                        Ternary logic CLI
================================================================================

AVX512__ has got the instruction ``VPTERN`` (``_mm512_ternarylogic_epi{32,64}``
which evaluates arbitrary `three-argument boolean`__ function. A programmer
gives three input argument and an 8-bit constant which defines the function.

This CLI program lets you provide a function in textual form and obtain
appropriate constant.  C++ programmers may use `contsexpr-based library`__
by **Samuel Neves**.

__ https://en.wikipedia.org/wiki/AVX-512
__ http://0x80.pl/articles/avx512-ternary-functions.html
__ https://github.com/sneves/avx512-utils

Expressions may contain parentheses and operators ``and``/``&``, ``or``/``|``,
``xor``/``^``, ``not``/``~``. There might be up to three variables, their
names are derived from the expression.

See also a `programming library <https://github.com/WojciechMula/ternary-logic>`_
that gives similar API, but works with SSE, AVX, AVX2 and x86 instruction sets.


Example 1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tautology::

    $ ./ternarylogiccli.py "x & ~x"
     # | x | - | - | x & ~x
    ---+---+---+---+--------
     0 | 0 | 0 | 0 |    0   
     1 | 0 | 0 | 1 |    0   
     2 | 0 | 1 | 0 |    0   
     3 | 0 | 1 | 1 |    0   
     4 | 1 | 0 | 0 |    0   
     5 | 1 | 0 | 1 |    0   
     6 | 1 | 1 | 0 |    0   
     7 | 1 | 1 | 1 |    0   

    _mm512_ternarylogic_epi32(x, -, -, 0x00)


Example 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Condition expression::

    $ ./ternarylogiccli.py "(cond and true_val) or (~cond and false_val)"
     # | cond | true_val | false_val | (cond & true_val) | (~cond & false_val)
    ---+------+----------+-----------+-----------------------------------------
     0 |  0   |    0     |     0     |                    0                    
     1 |  0   |    0     |     1     |                    1                    
     2 |  0   |    1     |     0     |                    0                    
     3 |  0   |    1     |     1     |                    1                    
     4 |  1   |    0     |     0     |                    0                    
     5 |  1   |    0     |     1     |                    0                    
     6 |  1   |    1     |     0     |                    1                    
     7 |  1   |    1     |     1     |                    1                    

    _mm512_ternarylogic_epi32(cond, true_val, false_val, 0xca)


Example 3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ ./ternarylogiccli.py "a and b or c"
     # | a | b | c | a & b | c
    ---+---+---+---+-----------
     0 | 0 | 0 | 0 |     0     
     1 | 0 | 0 | 1 |     1     
     2 | 0 | 1 | 0 |     0     
     3 | 0 | 1 | 1 |     1     
     4 | 1 | 0 | 0 |     0     
     5 | 1 | 0 | 1 |     1     
     6 | 1 | 1 | 0 |     1     
     7 | 1 | 1 | 1 |     1     


Example 3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ./ternarylogiccli.py "x ^ (y & ~z)"
     # | x | y | z | x ^ (y & ~z)
    ---+---+---+---+--------------
     0 | 0 | 0 | 0 |       0      
     1 | 0 | 0 | 1 |       0      
     2 | 0 | 1 | 0 |       1      
     3 | 0 | 1 | 1 |       0      
     4 | 1 | 0 | 0 |       1      
     5 | 1 | 0 | 1 |       1      
     6 | 1 | 1 | 0 |       0      
     7 | 1 | 1 | 1 |       1      

    _mm512_ternarylogic_epi32(x, y, z, 0xb4)
