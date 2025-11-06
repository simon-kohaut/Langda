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
    % Value range and first digit non-zero
    leftdigit(A), leftdigit(B), leftdigit(C),
 
    digit(D), digit(E),

    % Units digit B + D → E, produces carry C1
    sumdigit(0, B, D, E, C1),

    % Tens digit A + C + C1 → D, produces carry C2
    sumdigit(C1, A, C, D, C2),

    % Hundards digit B + C2 → C, no carry
    sumdigit(C2, 0, B, C, 0),

    % Make sure all letters are different
    all_different([A,B,C,D,E]).

% Initiate query example:
query(query_sum([A,B,C,D,E])).