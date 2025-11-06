merge_sort([], []).
merge_sort([X], [X]).
merge_sort(List, Sorted) :-
    langda(LLM:"Should contain following rules:
1.Get the length of the current list, Len, to determine whether to continue splitting.
2.Recursive boundary judgment: Only lists with a length greater than 1 need to be sorted, otherwise they are sorted by default.
3.Split the list into two parts, Left and Right, for subsequent recursive processing."),
    langda(LLM:"Should contain following rules:
1.Recursively call merge sort on the left half, and the result is SortedLeft.
2.Recursively sort the right half, and the result is SortedRight.
3.Merge the two sorted sublists into the final sorted result Sorted.").

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