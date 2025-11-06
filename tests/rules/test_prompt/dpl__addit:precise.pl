digit(img_1,1).
digit(img_2,2).
digit(img_3,3).
digit(img_4,4).
digit(img_5,5).
digit(img_6,6).
digit(img_7,7).
digit(img_8,8).
digit(img_9,9).
digit(img_0,0).


number([],Result,Result).
langda(LLM:" complete the number/3, it's function includes:
1.Convert the head image to the corresponding number Nr
2.Add the current number Nr to the "low bit" of the accumulated value Acc (the high bit is on the right)
3.Continue to recursively process the remaining images").
number(X,Y) :- number(X,0,Y).

multi_addition(X,Y,Z) :- langda(LLM:"Parse the image list from left to right into numbers. For example:
number([img_3,img_4], 0, R) will eventually get R = 34.").
query(multi_addition([img_7,img_9],[img_3,img_1,img_2],Z)).