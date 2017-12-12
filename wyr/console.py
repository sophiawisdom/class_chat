import sys
import interpret
pref = [int(a) for a in sys.argv[1:4]]
print(pref)
if len(pref) != 3:
    raise ValueError("Not enough preference arguments given. {0} given, 3 \
necessary.".format(len(pref)))
excl = []
while 1:
    s = input(">>>")
    if s.startswith("pref:"):
        pref = [int(a) for a in s.split()[1:]]
    else:
        m = interpret.get_question(pref,excl)
        excl.append(m)
        print(m)
