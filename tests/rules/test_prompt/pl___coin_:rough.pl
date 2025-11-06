PH::make_coin(C,PH).
coin(C) :- make_coin(C,0.8).
coins_r(SC,SC,0).
coins_r(SC,S,CNT) :-
    CNT > 0,
    langda(LLM:"Sample CNT independent coins and accumulate the number of heads facing up SC, and finally get the total number of heads after tossing CNT coins S").
total(S) :- coins_r(0,S,4).

query(total(_)).