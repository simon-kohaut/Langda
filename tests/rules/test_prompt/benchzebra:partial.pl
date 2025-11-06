zebra(Houses) :-
	houses(Houses),
	langda(LLM:"The owner of the red house is English."),
	langda(LLM:"The Spanish has a dog."),
	langda(LLM:"The owner of the green house drinks coffee."),
	my_member(house(_, ukrainian, _, tea, _), Houses),
	right_of(house(green,_,_,_,_), house(ivory,_,_,_,_), Houses),
	langda(LLM:"The snail owner smokes Winstons."),
	my_member(house(yellow, _, _, _, kools), Houses),
	langda(LLM:"The middle house drinks milk (the 3rd house)."),
	Houses = [house(_, norwegian, _, _, _)|_],
	next_to(house(_,_,_,_,chesterfields), house(_,_,fox,_,_), Houses),
	next_to(house(_,_,_,_,kools), house(_,_,horse,_,_), Houses),
	my_member(house(_, _, _, orange_juice, lucky_strikes), Houses),
	my_member(house(_, japanese, _, _, parliaments), Houses),
	langda(LLM:"The Norwegian lives next to the blue house."),
	langda(LLM:"Someone has a zebra."),
	langda(LLM:"Some people drink water.").

houses([
	house(_, _, _, _, _),
	house(_, _, _, _, _),
	house(_, _, _, _, _),
	house(_, _, _, _, _),
	house(_, _, _, _, _)
]).

right_of(A, B, [B, A | _]).
right_of(A, B, [_ | Y]) :- right_of(A, B, Y).

next_to(A, B, [A, B | _]).
next_to(A, B, [B, A | _]).
next_to(A, B, [_ | Y]) :- next_to(A, B, Y).

my_member(X, [X|_]).
my_member(X, [_|Y]) :- my_member(X, Y).

query(zebra(Houses)).