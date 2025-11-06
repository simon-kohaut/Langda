% Stach operations:
stack_op(push(X), Stack, [X|Stack]).
stack_op(pop, [_|Stack], Stack).
stack_op(dup, [X|Stack], [X,X|Stack]).
stack_op(swap, [X,Y|Stack], [Y,X|Stack]).
stack_op(over, [X,Y|Stack], [Y,X,Y|Stack]).
stack_op(rot, [X,Y,Z|Stack], [Z,X,Y|Stack]).

% Sorting operation
stack_op(sort, Stack, SortedStack) :-
    % Take out the top N elements of the stack and sort them
    get_top_n(Stack, 3, Elements, RestStack),
    insertion_sort(Elements, SortedElements),
    append(SortedElements, RestStack, SortedStack).

% Get the top N elements of the stack
get_top_n(Stack, N, Elements, Rest) :-
    length(Elements, N),
    append(Elements, Rest, Stack).

query(stack_op(push(1),[2,3,4],Y)).
query(stack_op(pop,[1,2,3,4],Y)).
query(stack_op(dup,[1,2,3,4],Y)).
query(stack_op(swap,[1,2,3,4],Y)).
query(stack_op(over,[1,2,3,4],Y)).
query(stack_op(rot,[1,2,3,4],Y)).