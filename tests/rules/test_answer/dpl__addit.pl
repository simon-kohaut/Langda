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

addition(X,Y,Z) :- digit(X,X2), digit(Y,Y2), Z is X2+Y2.

query(addition(img_5,img_6,Z)).