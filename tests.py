from random import random, choice


def formula(level, operator_index):
    log_formula = 2**(level+1) / (operator_index+1)**2
    multiplier = 1
    if log_formula >= 10 and random() > 0.5:
        multiplier = -1
    random_number = multiplier * round(random() * log_formula, level // 10)
    return random_number if int(random_number) != random_number else int(random_number)

def get_operator(level):
    operators = ["+", "-", "/", "*", "**"]
    index = choice(range(len(operators[:level // 2 + 1])))
    return index, operators[index]

def concat_example(var1, operator, var2):
    return f"{var1} {operator} {var2}".replace("+ -", "- ").replace("- -", "+ ")

def generate_example(level):
    operator_index, operator = get_operator(level)
    variable1 = formula(level, operator_index)
    variable2 = formula(level, operator_index)
    concat_example(variable1, operator, variable2)
    try:
        answer = eval(concat_example(variable1, operator, variable2))
    except ZeroDivisionError:
        variable2 += 1
        answer = eval(concat_example(variable1, operator, variable2))
    if level <= 2 and answer < 0:
        return concat_example(variable2, operator, variable1)
    if answer != int(answer):
        return generate_example(level)
    return concat_example(variable1, operator, variable2)

def generate_tests(level=1, n=10):
    examples = set()
    test = []
    while len(examples) < n:
        examples.add(generate_example(level))
    for idx, t in enumerate(examples, start=1):
        test.append({"number": idx, "example": t, "eval": int(eval(t))})
    return test

def prepare_test_for_sql(test, users_id, tests_id, timegiven):
    for row in test:
        row.update({"users_id": users_id, "tests_id": tests_id, "timegiven": timegiven})
    return test


