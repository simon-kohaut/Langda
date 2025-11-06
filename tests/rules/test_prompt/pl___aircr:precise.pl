% Aircraft Flap Controller
% This example is inspired by one in Filieri et al, Reliability Analysis in Symbolic Pathfinder, ICSE 2013

% the range of the flap
legal_flap_position(FP) :- between(0,10,FP).

% the strength of the actuators
actuator_strength(a,2).
actuator_strength(b,1).

% random prior on which actuator to use
0.5::use_actuator(T,a); 0.5::use_actuator(T,b).

% wind strength model
0.7::wind(weak); 0.3::wind(strong).
0.25::wind_effect(T,-1); 0.5::wind_effect(T,0); 0.25::wind_effect(T,1) :- wind(weak).
0.2::wind_effect(T,-3); 0.3::wind_effect(T,-2); 0.3::wind_effect(T,2); 0.2::wind_effect(T,3) :- wind(strong).

% the flap is moved to an attempted position if that is legal
flap_position(Time,Pos) :-
     Time > 0,
     attempted_flap_position(Time,Pos),
     legal_flap_position(Pos).

% an overrun exception occurs else
overrun_exception(Time) :-
     attempted_flap_position(Time,Pos),
     \+ legal_flap_position(Pos).

% did we reach the goal?
goal_reached(Time) :-
     goal(G),
     flap_position(Time,G).

% if the previous position was not the goal, attempt a new position
% the position depends on the chosen actuator and the current wind
attempted_flap_position(Time,Pos) :-
     Time > 0,
     Prev is Time-1,
     langda(LLM:"
          1. Check if the goal has been reached:
           If Old already satisfies goal(Old), no new trial position is calculated.
          
          2.Determine the current actuator and its strength:
           Select actuator A (use_actuator) according to time Time, and get its thrust AS from actuator_strength(A).
          
          3. Calculate the direction and contribution of the actuator
           Take the global target position GP (goal(GP)), and compare the difference direction between GP and Old:
           - If the target is in front of the current direction, AE = +AS; if in the opposite direction, AE = −AS;
           - Specific calculation: AE = sign(GP − Old) × AS.
          
          4. Superimpose wind interference:
           Take the additional effect WE of the wind force on the position at that moment from wind_effect(Time).
          
          Combine the trial position of this step:
          Add the three parts and get the current attempt flapping position Pos.").

% we want to go from 6 to 4, i.e., move two steps left
flap_position(0,6).
goal(4).

% restrict attention to first five steps
at(5).
query(goal_reached(T))  :- at(S),between(1,S,T).
query(overrun_exception(T))  :- at(S),between(1,S,T).