import shelve
import pprint


def print(text):
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pprint(text)

ProductHunter_Shelf = shelve.open('ProductHunter')
EmailHunter_Shelf = shelve.open('EmailHunter')

#for item in ProductHunter_Shelf:
#    print(ProductHunter_Shelf[item])

#print(ProductHunter_Shelf['searches'])
for item in EmailHunter_Shelf:
    print(EmailHunter_Shelf[item])
#print(EmailHunter_Shelf['email'])
