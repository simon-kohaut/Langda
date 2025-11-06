% member/2 for ProbLog
member(X, [X|_]).
member(X, [_|T]) :- member(X, T).

% --------- Basic meta-interpreter ---------
% Prove "true" always succeeds
prove(true).

prove(Goal) :-
	% For all other goals, use the clause/2 facts/rules defined in the program
	clause(Goal, Body),
	prove(Body).

% Prove compound goal A,B: prove A first, then prove B
prove((A,B)) :-
	prove(A),
	prove(B).

% --------- Extended logic processing ---------
% 1. implies(P,Q): P ⇒ Q, when P is unprovable or Q is provable
prove(implies(P,Q)) :-
	( \+ prove(P) % if P is unprovable
	; prove(Q) ). % or Q is provable

% 2. opposite(P): "opposite"/negation of P; that is, P is unprovable
prove(opposite(P)) :-
	\+ prove(P).

% 3. expand(A,B): first use expand/2 rule to expand A into B, then prove B
% You need to define several expand/2 facts or rules in the program
prove(expand(A,B)) :-
	expand(A,B).

% 4. includes(Set,X): set inclusion relation, equivalent to member/2
prove(includes(Set,X)) :-
	member(X,Set).

% 5. extend(List,Elem,Extended): add Elem to the head of List to get Extended
prove(extend(List,Elem,Extended)) :-
	Extended = [Elem|List].

% 6. refute(P): refute, equivalent to "unprovable"
prove(refute(P)) :-
	\+ prove(P).



% --------- Examples ---------- %
% Define some expand rules:
expand(double(X), Y) :- Y is X*2.
expand(square(X), Y) :- Y is X*X.

parent(alice, bob).
parent(bob, carol).

ancestor(X,Y) :- parent(X,Y).
ancestor(X,Y) :- parent(X,Z), ancestor(Z,Y).


% --------- Queries ---------- %
query(prove(implies(parent(alice,bob), ancestor(alice,bob)))).

query(prove(opposite(parent(carol,alice)))).

query(prove(expand(double(3),6))).

query(prove(includes([a,b,c],b))).

query(prove(extend([1,2],3,[3,1,2]))).