#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy

#adds keys from d2 to d1; d2 is changed in place
def add_dicts_in_place(d1,d2,forceOverwrite=False): #throws TypeError
	for k in d2:
		if k in d1:
			if type(d1[k]) == type(d2[k]) == dict: #items to add are dictionaries
				add_dicts_in_place(d1[k],d2[k],forceOverwrite)
			else: #items to add are not dictionaries
				if forceOverwrite:
					d1[k] = d2[k]
				else:
					raise TypeError,"Elements '"+str(d1[k])+"' from d1 and '"+str(d2[k])+"' from d2 must be of type dict() to be added together."
		else: #if k not in d1, add key:value of k to d1
			d1[k] = d2[k]

#adds keys of d2 to a copy of d1 and returns a new dictionary keeping d1 and d2 intact
def add_dicts(d1,d2,forceOverwrite=False):
	dtemp = copy(d1)
	add_dicts_in_place(dtemp,d2,forceOverwrite)
	return dtemp


def test(testName):
	d1 = {"a":{"b":1},"5":0}
	d2 = {"a":{"b":"vache","bonjour":4},"hey":5}
	d3 = copy(d1)
	expectedResult = {"a":{"b":"vache","bonjour":4},"hey":5,"5":0}

	if testName == "addDicts":
		d1 = {"a":{"b":1},"5":0}
		d2 = {"a":{"b":"vache","bonjour":4},"hey":5}
		add_in_place(d1,d2,True)
		print d1,"== expectedResult" if d1 == expectedResult else "!= expectedResult"
	if testName == "sumOfDicts":
		dTmp = add_dicts(d3,d2,True)
		print dTmp,"== expectedResult" if dTmp == expectedResult else "!= expectedResult"



if __name__ == "__main__":
	test("addDicts")
	test("sumOfDicts")
