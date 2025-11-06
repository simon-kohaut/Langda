% Based on Monty Hall problem on https://github.com/friguzzi/cplint

1/3::prize(1) ; 1/3::prize(2) ; 1/3::prize(3).

select_door(1).

member(X,[X|T]).
member(X,[H|T]) :- member(X,T).

0.5::open_door(A) ; 0.5::open_door(B) :-
  langda(LLM:"If there are two doors that are not selected and neither of them hides a prize
  Let the two doors be numbered A and B (and A < B ensures that each pair is counted only once).
  When faced with two empty doors, the host randomly and fairly chooses one to open.").

open_door(A) :-
  langda(LLM:"If only one door is not selected and does not contain a prize. 
  This means that the other unselected door is exactly the one that contains the prize.
  Then this rule will match the only empty door A and open it with certainty (probability 1).").

win_keep :-
  select_door(A),
  prize(A).

win_switch :-
  member(A, [1,2,3]),
  \+ select_door(A),
  prize(A),
  \+ open_door(A).

query(prize(_)).
query(select_door(_)).
query(win_keep).
query(win_switch).