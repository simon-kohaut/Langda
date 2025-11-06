langda(LLM:"This Prolog program should implement an interpretable bubblesort/3 algorithm.").

forth_sort(L,L2) :- bubblesort(L,[],L2).

query(forth_sort([3,1,2,5,7,12],X)).