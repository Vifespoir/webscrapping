"""Sandbox to read shelves files, useful for debugging."""
import shelve
import pprint


pp = pprint.PrettyPrinter(indent=4)

ProductHunter_Shelf = shelve.open('ProductHunter')
EmailHunter_Shelf = shelve.open('EmailHunter')

for item in ProductHunter_Shelf:
    pp.pprint(ProductHunter_Shelf[item])

for item in EmailHunter_Shelf:
    pp.pprint(EmailHunter_Shelf[item])
