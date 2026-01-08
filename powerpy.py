#!/usr/bin/env python3

from __future__ import annotations

import itertools
import math

from abc import ABC, abstractmethod
from typing import Iterable, Iterator, TypeVar

# TODO: Support truncated series optimization? This allows, for example, large
# orders of convolutions to be calculated with finite memory given that at least
# one of the series is finite. Right now, the design requires that finite series
# emit 0 indefinitely following the last non-zero term.


def main():
    print(nth(10000, 1 // (1 - 2 * atom())))

    # xs = [
    #     0, 3, 5, 4, 10, 11, 15, 10, 20, 30, 10, 3, 4, 1, 2, 4, 5, 6, 3, 4, 5,
    #     2, 3, 4, 4, 6, 6, 6, 6, 34, 6, 6, 7, 7, 8, 8, 8, 8, 9,8 ,9, 7, 6, 5, 5,
    #     10 ,23,3, 34, 4, 456, 5, 57, 57, 567,567, 4, 324, 34, 45, 45, 457, 74, 5,
    #     3,4,4,4,7,8,3,5,6,7,8,9,0,0,0,1,3,5,6,3456,23,234,234,23,345,5,6,6,53
    # ]
    # xs = list(range(100000))
    # for x in generate_naive(xs):
    #     print(x)
    # print()
    # for x in generate_partition(xs):
    #     print(x)
    # print()
    # for x in generate_dp(xs):
    #     print(x)

    # series = Finite([1]) // Finite([1, 1])
    # for x in take(series, 30):
    #     print(x)

    # series = Finite([1, 2, 3])
    # series = 3 * (-series)
    # series = series * series
    # for y in x:
    #     print(y)


def genlen(xs) -> int:
    length = 0
    for _ in xs:
        length += 1
    return length


# Generate function composition factors by visiting every integer composition of
# n.
def generate_naive(xs: list[int]) -> Iterable[int]:
    for n in range(1, len(xs)):
        s = 0
        for c in compositions(n):
            s += math.prod(map(lambda i: xs[i], c))
        yield s


# Generate function composition factors by visiting every integer partition of n
# and then correcting for the number of "repeats" with a multinomial factor.
def generate_partition(xs: list[int]) -> Iterable[int]:
    for n in range(1, len(xs)):
        s = 0
        for p in partitions(n):
            a = math.prod(map(lambda i: xs[i], p))
            c = multiset_perms(p)
            s += a * c
        yield s


# Generate function composition factors by maintaining a dynamic programming
# table of previous factors. Generate the nth factor by adding the nth input
# coefficient as an additional factor to _some_ previously computed factor (less
# than n).
def generate_dp(xs: list[int]) -> Iterable[int]:
    if len(xs) == 0:
        return
    if xs[0] != 0:
        raise Exception("composition only valid when constant term is 0")
    ys = [0]
    if len(xs) < 2:
        return
    y = xs[1]
    ys.append(y)
    yield y
    for n in range(2, len(xs)):
        y = 0
        for i in range(1, n):
            y += ys[n - i] * xs[i]
        y += xs[n]
        ys.append(y)
        yield y


A = TypeVar("A")


def take(n: int, iterable: Iterable[A]) -> Iterable[A]:
    it = iter(iterable)
    i = 0
    for item in it:
        yield item
        i += 1
        if i >= n:
            return


def nth(n: int, iterable: Iterable[A]) -> A:
    it = iter(iterable)
    i = 0
    for item in it:
        if i == n:
            return item
        i += 1
    raise Exception("not enough items")


def neutral() -> PowerSeries:
    return finite((1, ))


def atom() -> PowerSeries:
    return finite((0, 1))


def finite(coeffs: tuple[int, ...]) -> PowerSeries:
    return Finite(coeffs)


class PowerSeries(ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[int]:
        pass

    def __neg__(self) -> PowerSeries:
        return MappedSeries(lambda x: -x, self)

    def __abs__(self) -> PowerSeries:
        return MappedSeries(lambda x: abs(x), self)

    def __radd__(self, other: int) -> PowerSeries:
        return Addition(finite((other, )), self)

    def __add__(self, other: PowerSeries) -> PowerSeries:
        return Addition(self, other)

    def __rsub__(self, other: int) -> PowerSeries:
        return Subtraction(finite((other, )), self)

    def __sub__(self, other: PowerSeries) -> PowerSeries:
        return Subtraction(self, other)

    # Scalar multiplication
    def __rmul__(self, other: int) -> PowerSeries:
        if isinstance(other, int):
            return MappedSeries(lambda x: other * x, self)
        else:
            raise TypeError("unsupported operation")

    # Series multiplication
    def __mul__(self, other: PowerSeries) -> PowerSeries:
        return Product(self, other)

    # Scalar quotient.
    def __rfloordiv__(self, other: int) -> PowerSeries:
        return Division(finite((other, )), self)

    def __floordiv__(self, other: PowerSeries) -> PowerSeries:
        return Division(self, other)

    # Power series composition
    def __call__(self, other: PowerSeries) -> PowerSeries:
        return Composition(self, other)


class Finite(PowerSeries):
    def __init__(self, items: Iterable[int]):
        self._items = tuple(items)

    def __iter__(self) -> Iterator[int]:
        for item in self._items:
            yield item
        while True:
            yield 0


class MappedSeries(PowerSeries):
    def __init__(self, f, upstream):
        self._f = f
        self._upstream = upstream

    def __iter__(self):
        for item in self._upstream:
            yield self._f(item)


class Addition(PowerSeries):
    def __init__(self, f, g):
        self._f = f
        self._g = g

    def __iter__(self):
        for (f, g) in zip(iter(self._f), iter(self._g)):
            yield f + g


class Subtraction(PowerSeries):
    def __init__(self, f, g):
        self._f = f
        self._g = g

    def __iter__(self):
        for (f, g) in zip(iter(self._f), iter(self._g)):
            yield f - g


class Product(PowerSeries):
    def __init__(self, f, g):
        self._f = f
        self._g = g

    def __iter__(self) -> Iterator[int]:
        # Explicitly memoize previous results to be reused. Note that we will
        # accumulate zeros indefinitely once we reach the end of a sequence.
        f = iter(self._f)
        g = iter(self._g)
        fs = []
        gs = []
        for i in itertools.count(0):
            fs.append(next(f))
            gs.append(next(g))
            s = 0
            for j in range(0, i + 1):
                s += fs[i] * gs[j]
            yield s


class Division(PowerSeries):
    def __init__(self, f, g):
        self._f = f
        self._g = g

    def __iter__(self) -> Iterator[int]:
        f = iter(self._f)
        g = iter(self._g)
        gs = []
        hs = []
        g0 = next(g)
        if g0 == 0:
            raise Exception("F(x) / G(x) where G = 0")
        gs.append(g0)
        hs.append(next(f) // g0)
        yield hs[0]
        for i in itertools.count(1):
            fi = next(f)
            gs.append(next(g))
            s = 0
            # NOTE: This time, the upper bound is intentionally exclusive.
            for j in range(0, i):
                s += hs[j] * gs[i - j]
            hi = (fi - s) // g0
            hs.append(hi)
            yield hi


class Composition(PowerSeries):
    def __init__(self, f, g):
        self._f = f
        self._g = g

    def __iter__(self) -> Iterator[int]:
        f = iter(self._f)
        g = iter(self._g)
        g0 = next(g)
        if g0 != 0:
            raise Exception("f(g(z)) where g_0 = 0")
        h0 = next(f)
        fs = []
        gs = []
        composition_products = []
        raise Exception("not yet implemented")


def compositions(n: int) -> Iterable[tuple[int, ...]]:
    def rec(c: tuple[int, ...], n: int):
        if n == 0:
            yield c
        else:
            for x in range(1, n + 1):
                yield from rec(c + (x, ), n - x)

    yield from rec((), n)


def partitions(n: int) -> Iterable[tuple[int, ...]]:
    if n <= 0:
        yield ()
    else:
        for p in partitions(n - 1):
            yield p + (1, )
            if len(p) == 1 or len(p) > 1 and p[-1] < p[-2]:
                yield p[:-1] + (p[-1] + 1, )


def multiset_perms(multiset: Iterable[int]) -> int:
    ms = sorted(multiset)
    result = math.factorial(len(ms))
    for rl in run_lengths(ms):
        result //= math.factorial(rl)
    return result


def run_lengths(xs: Iterable[int]) -> Iterable[int]:
    prev = None
    run_length = 0
    for x in xs:
        if prev is None:
            prev = x
            run_length = 1
        elif prev == x:
            run_length += 1
        else:
            prev = x
            yield run_length
            run_length = 1
    if prev is not None:
        yield run_length


if __name__ == "__main__":
    main()
