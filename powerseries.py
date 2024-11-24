#!/usr/bin/env python3

from __future__ import annotations

import itertools
import math

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Callable, Generic, Iterable, Iterator, Type, TypeVar


def main():
    # ys = finite([1])
    # xs = finite([1, -2])
    # for x in take(10, ys / xs):
    #     print(x)
    # f = one() / finite([1, -1])
    # g = zpow(4)
    # for c in take(1000, f(g)):
    #     print(c)
    # for c in take(1000, g):
    #     print(c)
    pennies = one() / (one() - zpow(1))
    nickels = one() / (one() - zpow(5))
    dimes = one() / (one() - zpow(10))
    quarters = one() / (one() - zpow(25))
    for c in take(100, pennies * nickels * dimes * quarters):
        print(c)


A = TypeVar("A", int, Fraction)
B = TypeVar("B", int, Fraction)
T = TypeVar("T")


def take(n: int, items: Iterable[T]) -> Iterable[T]:

    def make_iterator():
        it = iter(items)
        i = 0
        while True:
            if i >= n:
                return
            value = next(it)
            i += 1
            yield value

    return IterableWrapper(make_iterator)


def one() -> PowerSeries[int]:
    return finite([1])


def z() -> PowerSeries[int]:
    return finite([0, 1])


def zpow(n: int) -> PowerSeries[int]:
    coeffs = [0] * n + [1]
    return finite(coeffs)


def finite(f: Iterable[int]) -> PowerSeries[int]:
    return Finite(f, int, integer_div)


def finite_frac(f: Iterable[Fraction]) -> PowerSeries[Fraction]:
    return Finite(f, Fraction, fractional_div)


def exp() -> PowerSeries[Fraction]:
    return Exponential()


class PowerSeries(ABC, Generic[A]):

    @abstractmethod
    def zero(self) -> A:
        pass

    @abstractmethod
    def div(self, num: A, denom: A) -> A:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[A]:
        pass

    def to_frac(self) -> PowerSeries[Fraction]:
        return MappedSeries(self, Fraction, Fraction, fractional_div)

    def __neg__(self) -> PowerSeries[A]:
        return MappedSeries(self, lambda x: -x, self.zero, self.div)

    def __add__(self, other: PowerSeries[A]) -> PowerSeries[A]:
        return Addition(self, other)

    def __sub__(self, other: PowerSeries[A]) -> PowerSeries[A]:
        return Addition(self, -other)

    def __mul__(self, other: PowerSeries[A]) -> PowerSeries[A]:
        return Multiplication(self, other)

    def __truediv__(self, other: PowerSeries[A]) -> PowerSeries[A]:
        return Division(self, other)

    def __call__(self, other: PowerSeries[A]) -> PowerSeries[A]:
        return Composition(self, other)


class Finite(PowerSeries[A]):

    def __init__(self, items: Iterable[A], type_: Type[A],
                 div: Callable[[A, A], A]):
        self._items = items
        self._type = type_
        self._div = div

    def zero(self):
        return self._type()

    def div(self, num: A, denom: A) -> A:
        return self._div(num, denom)

    def __iter__(self) -> Iterator[A]:
        for item in self._items:
            yield item
        while True:
            yield self.zero()


class MappedSeries(PowerSeries[B]):

    def __init__(self, series: PowerSeries[A], f: Callable[[A], B],
                 zero: Callable[[], B], div: Callable[[B, B], B]):
        self._series = series
        self._f = f
        self._zero = zero
        self._div = div

    def zero(self) -> B:
        return self._zero()

    def div(self, num: B, denom: B) -> B:
        return self._div(num, denom)

    def __iter__(self) -> Iterator[B]:
        for c in self._series:
            yield self._f(c)


class Addition(PowerSeries[A]):

    def __init__(self, f: PowerSeries[A], g: PowerSeries[A]):
        self._f = f
        self._g = g

    def zero(self) -> A:
        return self._f.zero()

    def div(self, num: A, denom: A) -> A:
        return self._f.div(num, denom)

    def __iter__(self) -> Iterator[A]:
        for (f, g) in zip(iter(self._f), iter(self._g)):
            yield f + g


class Multiplication(PowerSeries[A]):

    def __init__(self, f: PowerSeries[A], g: PowerSeries[A]):
        self._f = f
        self._g = g

    def zero(self) -> A:
        return self._f.zero()

    def div(self, num: A, denom: A) -> A:
        return self._f.div(num, denom)

    def __iter__(self) -> Iterator[A]:
        f = iter(self._f)
        g = iter(self._g)
        fs = []
        gs = []
        for n in itertools.count():
            s = self._f.zero()
            fs.append(next(f))
            gs.append(next(g))
            for i in range(n + 1):
                s += fs[i] * gs[n - i]
            yield s


class Division(PowerSeries[A]):

    def __init__(self, f: PowerSeries[A], g: PowerSeries[A]):
        self._f = f
        self._g = g

    def zero(self) -> A:
        return self._f.zero()

    def div(self, num: A, denom: A) -> A:
        return self._f.div(num, denom)

    def __iter__(self) -> Iterator[A]:
        f = iter(self._f)
        g = iter(self._g)
        g0 = next(g)
        if g0 == self._f.zero():
            raise Exception("f(z)/g(z) where constant term of g(z) is zero")
        gs = [g0]
        qs = []
        for n in itertools.count():
            s: A = self.zero()
            for i in range(n):
                s += qs[i] * gs[n - i]
            fn = next(f)
            # NOTE: int.__sub__ and Fraction.__sub__ should both return their
            # original types. Pyright does not seem to know this. Note that the
            # intention is _not_ to make A covariant in its subtypes, but
            # invariant. I'm not sure if there's a way to specify this to the
            # type hint system.
            diff: A = fn - s  # type: ignore
            qn = self.div(diff, g0)
            gs.append(next(g))
            qs.append(qn)
            yield qn


class Composition(PowerSeries[A]):

    def __init__(self, f: PowerSeries[A], g: PowerSeries[A]):
        self._f = f
        self._g = g

    def zero(self) -> A:
        return self._f.zero()

    def div(self, num: A, denom: A) -> A:
        return self._f.div(num, denom)

    def __iter__(self) -> Iterator[A]:
        f = iter(self._f)
        g = iter(self._g)
        fs = []
        gs = []
        cs = []
        gs.append(next(g))
        if gs[0] != self._f.zero():
            raise Exception("f(g(z)) where constant term of g is non-zero")
        fs.append(next(f))
        yield fs[0]
        for n in itertools.count(1):
            fs.append(next(f))
            gs.append(next(g))
            c = [0] * n
            c[0] = gs[n]
            for k in range(2, n+1):
                for i in range(1, n - k + 2):
                    c[i-1] += gs[i] * cs[n-i-1][k-2]
            hn = 0
            for m in range(1, n + 1):
                hn += fs[m] * c[m - 1]
            cs.append(c)
            yield hn
            # fs.append(next(f))
            # gs.append(next(g))
            # s = self._f.zero()
            # for k in range(n):
            #     # Add up all the ways to make this composition by adding a new
            #     # element of size k to a previous one.
            #     # s += hs[k] * gs[n - k]
            #     s += fs[k] * xs[k] * gs[n - k]
            # # As usual, we struggle with the fact that pyright doesn't know
            # # this must be of type A.
            # s += fs[n] * gs[n]
            # # hn: A = s # type: ignore
            # # hs.append(hn)
            # # yield hn
            # yield s

# When computing the composition C(z) = B(A(z)), we have the following coefficients:
# \begin{aligned}
# c_n &= \sum_{k=0}^{n} b_k a_{j_{1}}a_{j_2}\cdots a_{j_k} \mid \sum_{i=1}^{k} a_{j_i} = n \\
# c_0 &= b_0 \\
# c_1 &= b_1 a_1 \\
# c_2 &= b_1 a_2 + b_2 a_1 a_1 \\
# c_3 &= b_1 a_3 + b_2 a_1 a_2 + b_2 a_2 a_1 + b_3 a_1 a_1 a_1 \\
# c_4 &= b_1 a_4 + b_2 a_1 a_3 + b_2 a_2 a_2 + b_2 a_3 a_1 + b_3 a_1 a_1 a_2 + b_3 a_1 a_2 a_1 + b_3 a_2 a_1 a_1 + b_4 a_1 a_1 a_1 a_1
# \end{aligned}
#
# Rewritten to factor the $b_i$s, we have:
# c_1 &= b_1 a_1 \\
# c_2 &= b_1 a_2 + b_2 a_1 a_1 \\
# c_3 &= b_1 a_3 + b_2 (a_1 a_2 + a_2 a_1) + b_3 a_1 a_1 a_1 \\
# c_4 &= b_1 a_4 + b_2 (a_1 a_3 + a_2 a_2 + a_3 a_1) + b_3 (a_1 a_1 a_2 + a_1 a_2 a_1 + a_2 a_1 a_1) + b_4 a_1 a_1 a_1 a_1
#
# Note that when computing c_n, you can either make an n-composition of n itself
# by tacking on a_1 to a previous (n-1)-composition of (n-1), or else you can
# add 1 to each index i of a_i in a k-composition of (n-1), where k < (n - 1).

class Exponential(PowerSeries[Fraction]):

    def zero(self):
        return Fraction()

    def div(self, num: Fraction, denom: Fraction) -> Fraction:
        return fractional_div(num, denom)

    def __iter__(self) -> Iterator[Fraction]:
        for n in itertools.count():
            yield Fraction(1, math.factorial(n))


class IterableWrapper(Generic[T]):

    def __init__(self, f: Callable[[], Iterator[T]]):
        self._f = f

    def __iter__(self) -> Iterator[T]:
        return self._f()


def integer_div(a: int, b: int) -> int:
    return a // b


def fractional_div(a: Fraction, b: Fraction) -> Fraction:
    return a / b


if __name__ == "__main__":
    main()
