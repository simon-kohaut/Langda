PH::make_coin(C,PH).
coin(C) :- make_coin(C,0.8).
coins_r(SC,SC,0).
coins_r(SC,S,CNT) :-
    CNT > 0,
    langda(LLM:"With the counter CNT decreasing to 0, each step:
    If the CNTth coin coin(CNT) turns up heads, the success count SC increases by 1;
    Otherwise, it remains unchanged;
    Finally, all steps are accumulated to S.").

total(S) :- coins_r(0,S,4).

query(total(_)).