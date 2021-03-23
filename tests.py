from random import choices, choice, shuffle
from math import ceil, floor
import numpy as np


class Example:
    """Initialize with create()"""
    def __init__(self, operator, level, difficulty, num):
        """
        operator is a math's operator
        level abstract is a multiplier for formulas
        difficulty depends on operator and is a divisor for formulas
        num is the number of examples
        """
        self.operator = operator
        self.level = level
        self.difficulty = difficulty
        self.num = num
        self.uniques = set()
        self.examples = []
        self.generate_examples()

    @classmethod
    def create(cls, operator, level, num):
        operators = cls.get_operators()
        if operator not in operators:
            return None
        return cls(operator, level, operators[operator], num)

    @classmethod
    def get_operators(cls):
        """Dictionary of operators and difficulties chosen empirically"""
        return {"+": 1.3, "-": 1.5, "/": 1.5, "*": 2, "**": 4}

    @staticmethod
    def formula(level, difficulty):
        return ceil(level**2 / difficulty**2)

    @staticmethod
    def find_denominators(number):
        denominators = []
        for i in range(1, number+1, 1):
            if number % i == 0:
                denominators.append(i)
        return denominators

    @staticmethod
    def make_choices(numbers, formula):
        if len(numbers) == 0:
            return 0
        elif len(numbers) == 1:
            return numbers[0]
        np_numbers = np.array(numbers)
        # Working on sample
        percentile = np.percentile(np_numbers, min(90, 10 * formula))
        std = np.std(np_numbers)
        minimum = min(0, max(0, floor(percentile-std)))
        maximum = min(len(np_numbers) - 1, ceil(percentile+std))
        # Selecting *optimal* sample
        scope = np_numbers[minimum:maximum + 1]
        # Working on sample's weights
        scope_left = scope[:ceil(len(scope)/2)]
        i = lambda sample, population: sample if len(sample)*2 == len(population) else sample[:-1]
        scope_right = i(scope_left, scope)[::-1]
        weights = np.concatenate((scope_left, scope_right))
        if sum(weights) == 0:
            weights = np.apply_along_axis(lambda x: x+1, 0, weights)
        return choices(scope, weights)[0]

    def generate_constant(self, percent=.0):
        p = lambda x: x + 1
        formula = self.formula(self.level * p(percent), self.difficulty)
        min_value = 0
        max_value =  max(min_value, formula)
        chosen = self.make_choices([i for i in range(min_value, max_value+1, 1)], formula)
        return str(chosen)

    def calculate_coefficient(self, percent=.0):
        p = lambda x: x + 1
        formula = self.formula(self.level * p(percent), self.difficulty)
        min_value = 2   # For better variety
        max_value = max(min_value, formula)
        chosen = self.make_choices([i for i in range(min_value, max_value + 1, 1)], formula)
        return chosen

    def pick_denominator(self, number, percent=.0):
        p = lambda x: x + 1
        denominators = self.find_denominators(int(number))
        chosen = self.make_choices(denominators, self.formula(self.level * p(percent), self.difficulty))
        return str(chosen)

    def evaluate_example(self, constants, cycle=1, coef=10):
        while True:
            if cycle >= (len(constants) - 1) * coef:
                return None
            example = self.operator.join(constants)
            try:
                evaled = eval(example)
                assert int(evaled) == evaled
                break
            except (ZeroDivisionError, AssertionError):
                # Right now both only in "/" operation
                index1 = -(cycle // coef) - 2
                index2 = -(cycle // coef) - 1
                # ZeroDivisionError:
                if int(constants[index1]) == 0:
                    if int(constants[index2]) == 0:
                        constants[index2] = self.generate_constant(cycle/coef)
                    constants[index1] = str(int(constants[index2]) * self.calculate_coefficient(cycle/coef))
                # AssertionError:
                else:
                    # Find all denominators and choose randomly according to formula weights
                    if len(self.find_denominators(int(constants[index1]))) == 2:
                        # This is a prime number
                        constants[index1] = str(int(constants[index1]) + 1)
                    constants[index2] = self.pick_denominator(constants[index1], cycle/coef)
                cycle += 1
        #print("example: ", example, "constants: ", constants, "operator: ", self.operator, "evaled: ", evaled)
        return example, constants, int(evaled)

    def generate_example(self):
        constant1 = self.generate_constant()
        constant2 = self.generate_constant()
        example, constants, evaled = self.evaluate_example([constant1, constant2])
        #print("example: ", example, "constants: ", constants, "operator: ", self.operator, "evaled: ", evaled)
        num = len(self.uniques)
        self.uniques.add((example, ','.join(constants), self.operator, evaled))
        if num != len(self.uniques):
            self.examples.append({
                "level": self.level,
                "difficulty": self.difficulty,
                "example": example,
                "constants": ','.join(constants),
                "operator": self.operator,
                "eval": evaled})

    def generate_examples(self, break_point=20):
        # breakpoint is the maximum iterations to generate examples
        break_point = break_point if break_point > self.num else self.num
        while len(self.examples) < self.num and break_point:
            self.generate_example()
            break_point -= 1


class Test:
    """
    Initialize with create()
    examples_params is a list of dictionaries
    total is the number of the whole set of examples
    shuffled is for shuffling examples
    """
    def __init__(self, examples_params, total, shuffled):
        self.examples_params = examples_params
        self.shuffled = shuffled
        self.total = total
        self.examples = []
        self.make()

    @classmethod
    def create(cls, examples_params, total=10, shuffled=False):
        if not cls.check_params(examples_params):
            return None
        return cls(examples_params, total, shuffled)

    @staticmethod
    def check_params(params):
        for param in params:
            if not all(example in param for example in ["operator", "level", "examples"]):
                return False
        return True

    def make(self):
        for params in self.examples_params:
            self.examples.append(list(Example.create(params["operator"], params["level"], params["examples"]).examples))
        while len(self.examples) < self.total:
            chosen = choice(self.examples_params)
            self.examples.append(list(Example.create(chosen["operator"], chosen["level"], chosen["examples"]).examples))
        if self.shuffled:
            shuffle(self.examples)
        """
        else:
            test = []
            for example in self.examples:
                test.append(sorted(example, key=lambda x: (x["operator"], x["level"])))
            self.examples = test
        """


def main():
    test = Test.create(test_params, 20)
    for examples in test.examples:
        print(examples)

if __name__ == "__main__":
    main()
