merge_sort([], []).
merge_sort([X], [X]).
merge_sort(List, Sorted) :-
    length(List, Len),
    Len > 1,
    split_list(List, Left, Right),
    merge_sort(Left, SortedLeft),
    merge_sort(Right, SortedRight),
    merge(SortedLeft, SortedRight, Sorted).

split_list(List, Left, Right) :-
    length(List, Len),
    Half is Len // 2,
    length(Left, Half),
    append(Left, Right, List).

merge([], List, List).
merge(List, [], List).
merge([H1|T1], [H2|T2], [H1|Merged]) :-
    H1 =< H2,
    merge(T1, [H2|T2], Merged).
merge([H1|T1], [H2|T2], [H2|Merged]) :-
    H1 > H2,
    merge([H1|T1], T2, Merged).
    
append([], L, L).
append([H|T], L2, [H|R]) :-
    append(T, L2, R).


query(merge_sort([3,1,2,5,7,12],X)).