digit(img_1,1).
digit(img_2,2).
digit(img_3,3).
langda(LLM:"img_4 corresponds to number 4").
langda(LLM:"img_5 corresponds to number 5").
langda(LLM:"img_6 corresponds to number 6").
digit(img_7,7).
langda(LLM:"img_8 corresponds to number 8").
langda(LLM:"img_9 corresponds to number 9").
digit(img_0,0).

addition(X,Y,Z) :- 
    langda(LLM:"addition logic, input as img_1 to img_0").
query(addition(img_5,img_6,Z)).