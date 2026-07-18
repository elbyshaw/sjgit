filelist = ['./ams', './dd', './pd', './dv']
people = []

for file in filelist:
    with open(file, 'r') as myfile:
        # FIX 1: Iterating over 'myfile' instead of 'file'
        for line in myfile: 
            person = line.strip()
            if person not in people:
                people.append(person)

people.sort()

with open('./output', 'w') as ofile:
    for person in people:
        # FIX 2: Added \n so names are on separate lines
        ofile.write(person + "\n") 
    
    # FIX 3: Added a newline before the count so it's on its own line
    ofile.write(f"\nTotal unique people: {len(people)}\n")
