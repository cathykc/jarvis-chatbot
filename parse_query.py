def getFood(input):
    split = input.split()
    i = 0
    for s in split:
        if s is 'schedule' or 'book' or 'plan':
            # get the next one
            food = ""
            i += 1
            s = split[i]
            # while next is not a key workd
            while (s != 'at') and (s != 'in') and (s !='with'):
                food += s + " "
                if (i + 1) >= len(split):
                    return food
                i += 1
                s = split[i]
            return food
    return None


def getPlace(input):
    split = input.split()
    i = 0
    place = ""
    for s in split:
        if s == 'in':
            i += 1
            s = split[i]
            while (s != 'at') and (s !='with'):
                place += s + " "
                if (i + 1) >= len(split):
                    return place
                i += 1
                s = split[i]
            return place
        else:
            i+=1
    return None


def getPerson(input):
    split = input.split()
    i = 0
    for s in split:
        if s == 'with':
            # get the next word
            persons = ""
            i += 1
            s = split[i]
            # while next is not a key workd
            while (s != 'at') and (s != 'in'):
                persons += s + " "
                if (i + 1) >= len(split):
                    return persons
                i += 1
                s = split[i]
            return persons
        else:
            i+=1
    return None

def getTime(input):
    split = input.split()
    i = 0
    for s in split:
        if s == 'at':
            # get the next one
            return str(split[i + 1])
        else:
            i+=1
    return None