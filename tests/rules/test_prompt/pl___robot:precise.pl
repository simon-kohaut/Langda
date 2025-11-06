% source: David Poole. Abducing through negation as failure: stable models within the independent choice logic. JLP 2000.

carrying(key,s(T)) :-
     do(pickup(key),T),
     at(robot,Pos,T),
     at(key,Pos,T),
     pickup_succeeds(T).
carrying(key,s(T)) :-
     carrying(key,T),
     \+ do(putdown(key),T),
     \+ do(pickup(key),T),
     \+ drops(key,T).
 
0.7::pickup_succeeds(T); 0.3::pickup_fails(T).
 
drops(key,T) :-
     slippery(key,T),
     drop_slippery_key(T).
drops(key,T) :-
     \+ slippery(key,T),
     fumbles_key(T).
 
0.6::drop_slippery_key(T); 0.4::holds_slippery_key(T).
0.2::fumbles_key(T); 0.8::retains_key(T).
 
slippery(key,s(T)) :-
    slippery(key,T),
    stays_slippery(T).
slippery(key,0) :-
    initially_slippery(key).
 
0.75::stays_slippery(T); 0.25::stops_being_slippery(T).
0.5::initially_slippery(key); 0.5::initially_unslippery(key).
 
langda(LLM:"Define three at/3 predicates (they have three parameters: key, position and time), they describe respectively:
    If at time T the robot's action list contains goto(Pos), and this move succeeds, then at the next time s(T), the robot will be at the goal position Pos.
    If goto(Pos) is executed at time T, but goto_succeeds(T) is false (i.e. the move failed), then at time s(T) the robot remains where it is.
    If there is no goto(_) action at time T (goto_action(T) is false), then at time s(T) the robot remains stationary.").

langda(LLM:"Define two at/3 predicates (they have three parameters: key, position and time), they describe respectively:
    If at the same moment T the robot is "carrying" the key (carrying(key, T) is true) and the robot is at position Pos, then the key is also at that position Pos. In other words: as long as the robot is holding the key, the key and the robot always move in sync.
    If at time s(T) (the next time step) the robot does not have the key, then at s(T) the key is stationary.")

0.9::goto_succeeds(T); 0.1::goto_fails(T).
 
goto_action(T) :-
    do(goto(Pos),T).
 
do(goto(loc1),0).
do(pickup(key),s(0)).
do(goto(loc2),s(0)).
at(key,loc1,0).
at(robot,loc0,0).
 
query(carrying(key,s(s(s(0))))).
query(at(_,_,s(s(s(0))))).