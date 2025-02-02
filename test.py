import json

myList = []

for i in range(5):
    password = input("Enter your password: ")
    myList.append(password)
    print('password saved')


print(myList)
print(myList[3])

json_string = json.dumps(myList)
print(json_string)
print(json_string[3])
print(len(json_string))
print(len(myList))








#
# json_string = json.dumps(myList)
#
# print(json_string)
#
# myListParsed = json.loads(json_string)
# print(myListParsed)
# print(myListParsed[4])