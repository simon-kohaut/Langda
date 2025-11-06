langda(LLM:"This Prolog program should implement an interpretable merge_sort/2 algorithm").

append([], L, L).
append([H|T], L2, [H|R]) :-
    append(T, L2, R).

query(merge_sort([3,1,2,5,7,12],X)).