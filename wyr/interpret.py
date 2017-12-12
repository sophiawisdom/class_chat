import string
import random
categories = ["Family","Friends","Discussion"]
def load_database():
    with open("questions.txt") as file:
        questions = file.read().split("\n")
    questions = [q for q in questions if (not q.startswith("#")) and q]
    types = {}
    m = 0
    n = [data.index(i + ":") for i in categories]
    n.append(len(data)-1) # for end point
    returndict = {}
    for place, value in enumerate(categories):
        returndict[value] = data[n[place]+1:n[place+1]]
    return returndict
class wyr_error(Exception):
    pass
database = load_database()
def get_question(cats,exclude=[]):
    # categories is a database of length the same as database or categories and is a Truthy or Falsy value for each indicating whether those are acceptable.
    print("Exclude len: {0}".format(len(exclude)))
    keys = []
    for i in range(len(cats)): # must be more elegant way. What is it?
        if cats[i]:
            keys.append(categories[i])
    data = []
    for i in keys:
        data.extend(database[i])
    s = data.pop(random.randint(0,len(data)-1))
    while s in exclude:
        try:
            s = data.pop(random.randint(0,len(data)-1))
        except BaseException:
            exclude = []
    return s
