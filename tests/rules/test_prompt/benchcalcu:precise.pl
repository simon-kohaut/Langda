% Cryptoaddition:
% Find the unique answer to:

% Define available digits
digit(0). digit(1). digit(2). digit(3). digit(4).
digit(5). digit(6). digit(7). digit(8). digit(9).

% The first digit of a multi-digit number cannot be 0
leftdigit(D) :- digit(D), D =\= 0.

% All elements are different
all_different([]).
all_different([H|T]) :- \+ member(H, T), all_different(T).

member(X, [X|_]).
member(X, [_|T]) :- member(X, T).

% Simulate a column addition: Cin is the input carry, Cout is the output carry
sumdigit(Cin, A, B, Sum, Cout) :-
    X is Cin + A + B,
    ( X < 10, Sum = X, Cout = 0
    ; 
    X >= 10, Sum is X - 10, Cout = 1 ).

% Main predicate: AB + BCD = CDE
query_sum([A,B,C,D,E]) :-
    langda(LLM:"please construct the alphabet math puzzle: AB + BCD = CDE with following laws:
        1. Firstly define all the digits, the first digit of a multi-digit number cannot be 0 (with the help of digit/1 and leftdigit/1),
        2. Different letters refer to different numbers with the help of all_different/1,
        3. calculate with the help of sumdigit/5, don't forget to carry.").

% Initiate query example:
query(query_sum([A,B,C,D,E])).