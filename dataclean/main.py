from typing import Optional, List, Union, Tuple, TypeVar, Generic, Callable
from pydantic import BaseModel, Field
import functools

from dataclasses import dataclass


from pysat.formula import CNF
from pysat.formula import IDPool
from pysat.solvers import Solver


# Infix typefoo magic scripting
from functools import partial


T = TypeVar("T")
U = TypeVar("U")


@dataclass
class Accessor(Generic[T, U]):
    name: str
    get: Callable[[T], U]
    set: Callable[[Tuple[T, U]], T]

    def isOutputing(self):
        return self.name[0] == "ο"

    def __repr__(self):
        return self.name

    def __getattr__(self, name):
        return then(
            self,
            Accessor(
                name=name,
                get=lambda x: getattr(x, name),
                set=lambda x, v: setattr(x, name, v),
            ),
        )

    def __getitem__(self, index):
        return then(
            self,
            Accessor(
                name=f"[{index}]",
                get=lambda x: x[index],
                set=lambda x, v: setlist(x, index, v),
            ),
        )

    def __eq__(self, other):
        return Equality(self, other)

    def __contains__(self, other):
        return Containment(other, self)


def then(self, x):
    return Accessor(
        name=f"{self.name}.{x.name}",
        get=lambda y: x.get(self.get(y)),
        set=lambda y, v: x.set(self.get(y), v),
    )


def setlist(l, index, value):
    l[index] = value


def ε(a, b):
    return Containment(a, b)


@dataclass
class Equality(Generic[T]):
    left: Accessor
    right: Union[Accessor, T]
    pos: bool = True

    def isOutputing(self):
        return (isinstance(self.left, Accessor) and self.left.isOutputing()) or (
            isinstance(self.right, Accessor) and self.right.isOutputing()
        )

    def __invert__(self):
        return Equality(left=self.left, right=self.right, pos=not self.pos)

    def __repr__(self):
        return f"{self.left} = {self.right}"

    def __hash__(self):
        return hash(repr(self))

    def __call__(self, input_object):
        if (
            self.left.name[0] == "ι"
            and isinstance(self.right, Accessor)
            and self.right.name[0] == "ι"
        ):
            return self.left.get(input_object) == self.right.get(input_object)
        elif self.left.name[0] == "ι" and not isinstance(self.right, Accessor):
            return self.left.get(input_object) == self.right
        else:
            return None


@dataclass
class Containment(Generic[T]):
    left: Union[Accessor, List[T]]
    right: Union[Accessor, List[T]]
    pos: bool = True

    def isOutputing(self):
        return (isinstance(self.left, Accessor) and self.left.isOutputing()) or (
            isinstance(self.right, Accessor) and self.right.isOutputing()
        )

    def __invert__(self):
        return Containment(left=self.left, right=self.right, pos=not self.pos)

    def __repr__(self):
        return f"{self.left} ε {self.right}"

    def __hash__(self):
        return hash(repr(self))

    def __call__(self, input_object):
        if (
            isinstance(self.left, Accessor)
            and self.left.name[0] == "ι"
            and isinstance(self.right, Accessor)
            and self.right.name[0] == "ι"
        ):
            return self.left.get(input_object) in self.right.get(input_object)
        elif (
            isinstance(self.left, Accessor)
            and self.left.name[0] == "ι"
            and not isinstance(self.right, Accessor)
        ):
            return self.left.get(input_object) in self.right
        elif (
            not isinstance(self.left, Accessor)
            and isinstance(self.right, Accessor)
            and self.right.name[0] == "ι"
        ):
            return self.left in self.right.get(input_object)
        else:
            return None


Sentence = Union[Equality, Containment]


class Transducer(Generic[T, U]):
    def __init__(self):
        self._constraints = CNF()
        self._id_pool = IDPool(start_from=1)

    def _constraint_to_id(self, c):
        return self._id_pool.id(c)

    def _id_to_constraint(self, i):
        return self._id_pool.obj(i)

    def __getattr__(self, name):
        if name == "ι":
            return Accessor(name=name, get=lambda x: x, set=lambda x, v: None)
        elif name == "ο":
            return Accessor(name=name, get=lambda x: x, set=lambda x, v: None)
        else:
            raise KeyError(f"Invalid argument {name}")

    def disjunction(self, *constraints):
        self._constraints.append([self._constraint_to_id(x) for x in constraints])

    def implies(self, consequence, *conditions):
        self._constraints.append(
            [
                self._constraint_to_id(consequence),
                *[-self._constraint_to_id(c) for c in conditions],
            ]
        )

    def run(self, input_object):
        compute_truth_values = [
            (i, (self._id_to_constraint(i))(input_object))
            for i in range(1, self._id_pool.top + 1)
        ]
        assumptions = [
            i if x else -i for (i, x) in compute_truth_values if x is not None
        ]

        print("ASSUMPTIONS", end=" ")
        print([self._id_to_constraint(i) for i in assumptions if i > 0], end=" ")
        print([self._id_to_constraint(-i) for i in assumptions if i < 0])

        with Solver(bootstrap_with=self._constraints.clauses) as s:
            for m in s.enum_models(assumptions=assumptions):
                print("MODEL", end=" ")
                print(
                    [
                        self._id_to_constraint(i)
                        for i in m
                        if i > 0 and self._id_to_constraint(i).isOutputing()
                    ],
                    end=" ",
                )
                print(
                    [
                        self._id_to_constraint(-i)
                        for i in m
                        if i < 0 and self._id_to_constraint(-i).isOutputing()
                    ]
                )


class InputUser(BaseModel):
    theme: str
    exploitant: str


class OutputUser(BaseModel):
    exploitant: str
    theme: str
    scope: List[str]


transducer = Transducer()


synonymesEDF = ["Électricité de Fance", "EdF"]

for syno in synonymesEDF:
    transducer.implies(
        # sortie
        transducer.ο.exploitant == "EDF",
        # conditions
        transducer.ι.exploitant == syno,
    )

transducer.implies(
    ε("REP", transducer.ο.scope),  # output
    # conditions
    transducer.ο.exploitant == "EDF",
    ε(transducer.ι.theme, ["Conduite normale", "Thème REP"]),
)


testInputUser = InputUser(theme="Conduite normale", exploitant="EDF")


if __name__ == "__main__":
    print("dataclean")
