import numpy as np
from random import sample
from string import digits
from itertools import product


def generate_numbers():
    numbers = []
    for number in product(digits, repeat=3):
        numbers.append(("".join(number)).lstrip("0"))
    numbers[0] = "0"
    return numbers

def generate_examples_plus(numbers, examples):
    operator = "+"
    for number in product(numbers, repeat=2):
        level = 0
        example = operator.join(number)
        evaled = eval(example)
        if evaled <= 10:
            if number[0] in ["1"] or number[1] in ["1"]:
                level += 1
            elif number[0] in ["2"] or number[1] in ["2"]:
                level += 2
            else:
                level += 3
        else:
            if number[0] in ["1"] or number[1] in ["1"]:
                level += 2
            elif number[0] in ["10"] or number[1] in ["10"]:
                level += 3
            else:
                level += 4
        examples.append({"example": example, "level": level, "operator": operator, "eval": evaled})
    return examples

def generate_examples_minus(numbers, examples):
    operator = "-"
    for number in product(numbers, repeat=2):
        level = 0
        example = operator.join(number)
        evaled = eval(example)
        if evaled == 0:
            level = 1
        elif evaled > 0:
            if number[0] in ["1"] or number[1] in ["1"]:
                level += 1
            elif number[0] in ["2"] or number[1] in ["2"]:
                level += 2
            else:
                level += 3
        else:
            if number[0] in ["1"] or number[1] in ["1"]:
                level += 2
            elif number[0] in ["10"] or number[1] in ["10"]:
                level += 3
            else:
                level += 4
        examples.append({"example": example, "level": level, "operator": operator, "eval": evaled})
    return examples

def generate_examples_multi(numbers, examples):
    operator = "*"
    for number in product(numbers, repeat=2):
        level = 0
        example = operator.join(number)
        evaled = eval(example)
        if number[0] in ["1", "10"] or number[1] in ["1", "10"]:
            level += 1
        elif number[0] in ["2"] or number[1] in ["2"]:
            if evaled <= 20:
                level += 2
            else:
                level += 3
        elif evaled <= 20 or number[0] in ["20"] or number[1] in ["20"]:
            level += 3
        else:
            level += 4
        examples.append({"example": example, "level": level, "operator": operator, "eval": evaled})
    return examples

def generate_examples_div(numbers, examples):
    operator = "/"
    for number in product(numbers, repeat=2):
        level = 0
        example = operator.join(number)
        evaled = eval(example)
        if evaled != int(evaled):
            continue
        if evaled == 1:
            level = 1
        elif number[0] in ["6", "7", "8", "9"] or number[1] in ["6", "7", "8", "9"]:
            level += 4
        elif number[0] in ["1", "10"] or number[1] in ["1", "10"]:
            level += 1
        elif number[0] in ["2", "3"] or number[1] in ["2", "3"]:
            level += 2
        elif number[0] in ["4", "5"] or number[1] in ["4", "5"]:
            level += 3
        else:
            level += 4
        examples.append({"example": example, "level": level, "operator": operator, "eval": int(evaled)})
    return examples

def generate_examples(upto=10):
    numbers = generate_numbers()
    examples = []
    examples = generate_examples_plus(numbers[1:upto+1], examples)
    examples = generate_examples_minus(numbers[1:upto+1], examples)
    examples = generate_examples_multi(numbers[1:upto+1], examples)
    examples = generate_examples_div(numbers[1:upto+1], examples)
    return examples
    
def calculate_weights(len_examples=20, len_levels=1):
    each_level = len_examples / len_levels

    left = levels[:len_levels // 2 + len_levels % 2]
    right = levels[:len_levels // 2][::-1]
    left_right = np.array(left + right)

    weights = np.floor(np.sqrt(np.pi * each_level * left_right))
    coef = 1 if len_examples >= np.sum(weights) else -1
    difference = abs(len_examples - np.sum(weights))
    if difference:
        weights[0] += coef
    i = 1
    while abs(len_examples - np.sum(weights)) > 1:
        index = i % len(weights)
        weights[index] += coef
        weights[-index] += coef
        i += 1
    return weights
    
def prepare_test(examples, num):
    len_levels = len(examples)
    weights = calculate_weights(num, len_levels)
    test = []
    for idx, level in enumerate(examples):
        chosen = sample(level, weights[idx])
        test.append(chosen)
    return test



