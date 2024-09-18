# bsc-llm
A collection of proof-of-concept scripts for utilizing LLMs in the Beam Search with Cuts framework.

Beam Search with Cuts (BSC) is a modular framework to combine any pre-trained neural sequence generation model with requirements encoded as Constraint Satisfaction Problems (CPSs). For details on BSC see [1]. OpenAI's GPT family are used as the integrated LLM models. Gurobipy is used for solving Integer Programming instances.

Dependencies:
- Python (>=3.6)
- OpenAI API Key (stored in environment variable OPENAI_API_KEY)
- Gurobipy

Beware; There are numerous calls made to the API in each execution of the script.

==================================================================

Problem 1: Division of food items (food.py)

The goal of this problem is to divide a given set of food items between n persons. The weight for each item is given and the total weight of the food assigned to each person should not exceed the given capacity. What each person gets to eat should make sense in terms of digestive health and nutritional value.

This problem is solved by entrusting the task of dividing food items onto the LLM, while a Bin Packing requirement encoded in IP is responsible for the capacity constraint.


Example:

- 3 persons, 1000g capacity

- Items: Egg 100g, Leftover pizza 500g, Milk 700g, Expensive Chocolate 200g, Celery 300g, Soup 500g, Blue Cheese 100g, Ice cream 300g, Nuts 200g

- Additional consideration: Make sure egg and milk are not consumed together.

This example is included in the file named food_instance. You can change the content of this file or enter the details of an arbitrary example manually.


Output:


- LLM-only output:

Person 1: leftover pizza, celery
Person 2: soup, nuts
Person 3: expensive chocolate, ice cream, egg

Observation: We can see that the LLM fails to include two items in the division, violating a strict requirement of the problem due to its myopic reasoning.



- CSP-only output:

Person 1: leftover pizza, celery, blue cheese
Person 2: soup, ice cream, nuts
Person 3: egg, milk, expensive chocolate

Observation: The CSP approach satisfies the requirement but obviously fails to consider common sense or any additional instructions given.



- Beam Search with Cuts output:

Solution 1:
Person 1: expensive chocolate, nuts, leftover pizza
Person 2: egg, soup, celery, blue cheese
Person 3: milk, ice cream

Solution 2:
Person 1: soup, expensive chocolate, celery
Person 2: leftover pizza, blue cheese, ice cream
Person 3: egg, nuts, milk

Observation: We can that both solutions are common sense and follow instructions, in addition to satisfy the strict requirements of the problem.

Procedure: LLM is asked to provide the solution piece by piece. A number of partial solutions are generated and maintained at each iteration. Solutions that are not capable to be extended to complete feasible solutions are cut. Some of the example cut partial solutions are as follows:

Cut partial solution 1: Person 1 (leftover pizza, soup, blue cheese, ...
Cut partial solution 2: Person 1 (celery, leftover pizza)
Cut partial solution 3: Person 1 (celery, blue cheese, leftover pizza) - Person 2 (soup, egg, ice cream, ...

The above solutions are cut because capacity is exceeded, the first group is closed off prematurely, and the required composition to fit the remaining items is violated, respectively.
