
% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).
weight ~ normal(0.2, 0.1).

% Real-time weather conditions:
langda(LLM:"Please get current weather data for user position: /* User */, and return in format:
weather(Condition, WindSpeed, Temperature).
Where:
- Condition: clear/cloudy/light_rain/heavy_rain
- WindSpeed: current wind speed in m/s
- Temperature: current temperature in Celsius", 
LOT:"search").

battery_efficiency(Efficiency) :-
    weather(_, _, Temp),
    (Temp < 0, Efficiency = 0.8; % Very cold
     Temp >= 0, Temp < 10, Efficiency = 0.85; % Cold
     Temp >= 10, Temp =< 35, Efficiency = 1.0; % Normal
     Temp > 35, Efficiency = 0.95 % Hot
     ).   

% Visual line of sight
vlos(X) :-
    weather(Condition, _, _),
    (
        Condition = light_rain, distance(X, operator) < 20;
        Condition = cloudy, distance(X, operator) < 50;
        Condition = clear, distance(X, operator) < 100;
        Condition = clear, over(X, bay), distance(X, operator) < 400
    ).

% Sufficient charge to return to operator
can_return(X) :-
    weather(_, WindSpeed, _),
    W is 1 + WindSpeed / 25,
    battery_efficiency(E),
    B is initial_charge, O is charge_cost,
    D is distance(X, operator), 0 < B + (2 * O * D * W / E).

sensitive_section(X) :- langda(LLM:"
    According to the police: /* Police */, what should we do about the zone? You need to use special_zone to refer to the zone, for example: distance(X, special_zone) < 100. 
    If 'nothing happens' set the range to 0, for example distance(X, special_zone) < 0. 
    If it is clearly stated that flying is prohibited outside the area, use for example distance(X, special_zone) > 100").

% Permits related to local features
permits(X) :- 
    distance(X, service) < 15; distance(X, primary) < 15;
    distance(X, secondary) < 10; distance(X, tertiary) < 5;
    distance(X, crossing) < 5; distance(X, rail) < 5;
    over(X, park).

% Definition of a valid mission
landscape(X) :- 
    \+ sensitive_section(X),
    (
    vlos(X), weight < 25, can_return(X); 
    permits(X), can_return(X)
    ).

