import openai
import os
import gurobipy as gp
from gurobipy import GRB
import copy
import random

my_api_key = os.getenv("OPENAI_API_KEY")

expansion_cnt_total = 16 # how many expansions are considered in total at each step
beam_width = 8 # how many partial solutions are maintained


mode = input("Load instace from file or enter manually? (load / manual)\n")

if mode == "load":
  with open('food_instance', 'r') as file:
    lines = [line.strip() for line in file.readlines()]
    l = 0
    while l < len(lines):
      if lines[l] == "PERSONS":
        num_persons = int(lines[l+1])
        l+=2
      elif lines[l] == "CAPACITY":
        person_cap = int(lines[l+1])
        l+=2
      elif lines[l] == "CONSIDERATION":
        consideration = lines[l+1]
        l+=2 
      elif lines[l] == "ITEMS":
        items = []
        l += 1
        while lines[l] != "NO MORE":
          items.append(lines[l])
          l += 1
        l += 1
      elif lines[l] == "WEIGHTS":
        item_weights = []
        l += 1
        while lines[l] != "NO MORE":
          item_weights.append(int(lines[l]))
          l += 1
        l += 1      
elif mode == "manual":           
  num_persons = int(input("Enter the number of persons: \n"))
  person_cap = int(input("Enter the max weight limit of the food assigned to each person: \n"))
  items = []
  item_weights = []
  while (to_add := input("Enter the name of the next item (type \"no more\" to end): \n")) != "no more":
    items.append(to_add)
    item_weights.append(int(input("Enter the weight of the item: \n")))
  consideration = input("Enter the consideration that should be kept in mind while dividing the items between persons.\n")




def solveBin(partial_solution, num_persons, person_cap, items, item_weights):
  model = gp.Model () 
  model.Params.LogToConsole = 0
  x = model.addVars(len(items), num_persons, vtype=GRB.BINARY)
  model.addConstrs(gp.quicksum(x[i,j] for j in range(num_persons)) == 1 for i in range(len(items)))
  model.addConstrs(gp.quicksum(item_weights[i] * x[i,j] for i in range(len(items))) <= person_cap for j in range (num_persons))

  closed_persons = []
  unassigned_items = [i for i in items]
  curr_person = 0
  for par in partial_solution:
    if par == "end":
      closed_persons.append(curr_person)
      curr_person += 1
      continue
    model.addConstr(x[items.index(par),curr_person] == 1)
    unassigned_items.remove(par)

  model.addConstrs(x[items.index(item),j] == 0 for item in unassigned_items for j in closed_persons)
  
  model.setParam('TimeLimit', 10)
  model.setParam('MIPFocus', 1)
  model.optimize()

  if model.status in {gp.GRB.OPTIMAL, gp.GRB.SUBOPTIMAL}:
    # print("Model feasible")
    return True
  elif model.status == gp.GRB.INFEASIBLE:
    # print("Model infeasible")
    return False
  else:
    # print("timeout or unknown")
    return False



for i in range(len(items)):
  items[i] = items[i].lower()

items_string = ""
for i in range(len(items)):
  items_string = items_string + "\n" + items[i] + ": " + str(item_weights[i]) + " g"

client = openai.OpenAI(
    api_key=my_api_key,
)


init_prompt = f"""I'll give you a list of food items and their weights. Divide them between {num_persons} persons to eat in one sitting, what each person eats in total should not exceed {person_cap} grams.
            
Make sure the combination of food items that each person eats make sense, so that the person will not be hungry or sick at the end. {consideration}.

The list:
{items_string}

Start by telling me what is the first item that person 1 should eat. Just say the name of the item and nothing else."""



my_messages = []
partial_solutions = []
complete_solutions = []

for b in range(1):
  my_messages.append([
        {
            "role": "user",
            "content": init_prompt,
        }
    ])
  partial_solutions.append([])


# print("User:", init_prompt, "\n=============================")

cnt = 0
while cnt<len(items)+num_persons+1 and len(my_messages) > 0:
  print("============================")
  my_messages_candidates = []
  partial_solutions_candidates = []
  expansion_cnt = expansion_cnt_total // len(my_messages)
  for b in range(len(my_messages)):
    expansions_generated = 0
    expansions_considered = 0
    while expansions_considered < expansion_cnt:
      expansions_considered += 1
      mes_candidate = copy.deepcopy(my_messages[b])
      par_candidate = copy.deepcopy(partial_solutions[b])
      chat_completion = client.chat.completions.create(
        messages=mes_candidate,
        #model="gpt-3.5-turbo",
        model="gpt-4o",
        temperature = 1.5,
      )
      res = chat_completion.choices[0].message.content.lower()
      if len(res) > 100:
        print("Issue with response, skipping this partial solution.")
        break

      # print("response", res, "for", par_candidate)
      found = False
      for item in items:
        if item in res:
          res = item
          found = True
          break
      if "end" in res:
        res = "end"
        found = True  
      if not found:
        continue
      if res != "end" and res in par_candidate:
        continue      
      par_candidate.append(res)
      # print("considering", par_candidate)
      if par_candidate in partial_solutions_candidates:
        continue
      print("Considering partial solution:", par_candidate)  
      feas = solveBin(par_candidate, num_persons, person_cap, items, item_weights)
      print("Feasible?", feas)
      if feas:
        persons_used = par_candidate.count("end")
        if persons_used == num_persons:
          if par_candidate not in complete_solutions:
            print("Feasible complete solution finalized.")
            complete_solutions.append(par_candidate)
          continue

        mes_candidate.append({"role": "assistant", "content": res})
        if res == "end":
          mes = f"Now move on to person {persons_used+1}, tell me the first item that person {persons_used+1} should eat. Just say the name of the item and nothing else." 
        else:
          mes = f"Give me 1 more item that person {persons_used+1} should eat. Just say the name of the item and nothing else. Say \"end\" if you want to close off the list for items that person {persons_used+1} should eat. But make sure that the sum of the weights for this person is close to {person_cap} grams, so that the person is not left hungry."  
        mes_candidate.append({"role": "user", "content": mes})

        my_messages_candidates.append(mes_candidate)
        partial_solutions_candidates.append(par_candidate)
        print("Partial solution added.")
        # print(mes_candidate[1:])
        expansions_generated += 1

  random_indices = random.sample(range(len(my_messages_candidates)), min(beam_width, len(my_messages_candidates)))
  my_messages = [my_messages_candidates[i] for i in random_indices]
  partial_solutions = [partial_solutions_candidates[i] for i in random_indices]

  print(len(my_messages), "partial solutions selected")

  cnt += 1


