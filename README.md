# bsc-llm
A collection of proof-of-concept scripts for utilizing LLMs in the Beam Search with Cuts framework.

Beam Search with Cuts (BSC) is a modular framework to combine any pre-trained neural sequence generation model with requirements encoded as Constraint Satisfaction Problems (CPSs). For details on BSC see [1]. OpenAI's GPT family are used as the integrated LLM models. Gurobipy is used for solving Integer Programming instances.

Dependencies:
- Python (>=3.6)
- OpenAI API Key (stored in environment variable OPENAI_API_KEY)
- Gurobipy


==================================================================
Division of food items:

The goal of this problem is to divide a given set of food items between n persons. The weight for each item is given and the total weight of the food assigned to each person should not exceed the given capacity. What each person gets to eat should make sense in terms of digestive health and nutritional value.

Example:
