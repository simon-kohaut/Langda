hole(X,Y,X,Y):-
    swap(X,Y,no_swap).

hole(X,Y,Y,X):-
    swap(X,Y,swap).

bubble([X],[],X).
bubble([H1,H2|T],[X1|T1],X):-
    hole(H1,H2,X1,X2),
    bubble([X2|T],T1,X).

bubblesort([],L,L).

bubblesort(L,L3,Sorted) :-
    langda(LLM:"Recursively call bubblesort on L2 and put the current maximum value X into the sorted part [X|L3].").

forth_sort(L,L2) :- bubblesort(L,[],L2).

langda(LLM:"The logical predicate that determines whether to exchange").
    
query(forth_sort([3,1,2,5,7,12],X)).