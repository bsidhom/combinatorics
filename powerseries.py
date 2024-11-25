#!/usr/bin/env python3

from __future__ import annotations

import itertools
import math

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import Callable, Generic, Iterable, Iterator, Type, TypeVar


def main():
    # Solve the famous "change-making" problem using generating functions.
    pennies = one() / (one() - zpow(1))
    nickels = one() / (one() - zpow(5))
    dimes = one() / (one() - zpow(10))
    quarters = one() / (one() - zpow(25))
    change = pennies * nickels * dimes * quarters
    print("Ways to make change of 99 cents:", nth(99, change))
    print()
    # Verify that identity-composition works as expected.
    for c in take(10, z()(zpow(1))):
        print(c)
    print()
    # Powerset construction with one unique item of size 1 and another of size
    # 2.
    for c in take(10, powerset_n(z() + zpow(2), 10)):
        print(c)
    print()
    # Powerset construction with exactly 6 unique elements, each of size 1.
    # Note that we expect to find C(6, n) subsets of size n within the powerset,
    # where C(n, k) is the binomial coefficient "n choose k".
    for c in take(10, powerset_n(6 * z(), 100)):
        print(c)
    print()
    # Multiset construction with exactly 6 unique elements, each of size 1.
    for c in take(10, multiset_n(6 * z(), 10)):
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


def nth(n: int, items: Iterable[T]) -> T:
    i = 0
    for item in items:
        if i == n:
            return item
        i += 1
    raise Exception("not enough elements for nth")


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


def alternating() -> PowerSeries[int]:
    def gen():
        positive = True
        while True:
            if positive:
                yield 1
            else:
                yield -1

    return IterableSeries(IterableWrapper(gen), int, integer_div)


def exp() -> PowerSeries[Fraction]:
    def gen():
        for n in itertools.count():
            yield Fraction(1, math.factorial(n))

    return IterableSeries(IterableWrapper(gen), Fraction, fractional_div)


def iterated_series(f: PowerSeries[A],
                    map_func: Callable[[int], A]) -> PowerSeries[A]:
    # The idea here is for the caller to provide a map_func which takes in a
    # power of z called k) and returns a function which is used to map the
    # resulting coefficients of the input series of z^k. This can be used to
    # replace the truncated powerset/multiset constructions; those are only
    # truncated because we do not currently have a way to represent an infinite
    # sum of series (which are themselves infinite).
    raise Exception("unimplemented")


def powerset_n(f: PowerSeries[A], n: int) -> PowerSeries[Fraction]:
    f_frac = f.to_frac()

    def inner_func(k: int) -> PowerSeries[Fraction]:
        arg = zpow(k).to_frac()
        series = Fraction(1, k) * f_frac(arg)
        return series if k % 2 != 0 else -series

    inner_series = map(inner_func, range(1, n + 1))
    g = series_sum(inner_series)
    return exp()(g)


def multiset_n(f: PowerSeries[A], n: int) -> PowerSeries[Fraction]:
    f_frac = f.to_frac()

    def inner_func(k: int) -> PowerSeries[Fraction]:
        arg = zpow(k).to_frac()
        return Fraction(1, k) * f_frac(arg)

    inner_series = map(inner_func, range(1, n + 1))
    g = series_sum(inner_series)
    return exp()(g)


def series_sum(series: Iterable[PowerSeries[A]]) -> PowerSeries[A]:
    # Annoyingly, we have to write our own series sum wrapper because the
    # built-in `sum` function requires arbitrary types to be `__radd__`-able to
    # the integer value 0, which it uses as the seed. Note that our PowerSeries
    # type is designed as a proper monoid, so we get the zero value from the
    # series itself rather than providing some arbitrary seed. However, since we
    # can't do type-level programming in Python, we require the input to be
    # non-empty and can effectively only treat it as a semigroup anyway.
    it = iter(series)
    try:
        s = next(it)
    except StopIteration:
        raise Exception(
            "series_sum can only be used with a non-empty sequence of series")
    for f in it:
        s += f
    return s


# The top-level "interface" type for power series, with some convenience methods
# that allow us to perform high-level operations directly on series objects.
# Note that the `zero()` and `div()` methods are only used to make this work
# generically across different numeric types. In our use cases, we are typically
# interested in exact solutions to combinatorial problems, which means we're
# working in a discrete space. Consequently, this only supports int and Fraction
# at the moment.
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

    def __rmul__(self, other: A) -> PowerSeries[A]:
        return MappedSeries(self, lambda x: other * x, self.zero, self.div)

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
        # Compute the product of 2 power series using a Cauchy convolution.
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
        # Compute a quotient of two power series h = f/g by considering the
        # Cauchy convolution gh and solving for the implied coefficients of f.
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
        # Take the composition f(g(z)), where both are power series. See the
        # following post for an explanation of the algorithm:
        # https://counting.club/posts/formal-power-series-composition/
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
            c = [self._g.zero() for _ in range(n)]
            c[0] = gs[n]
            for k in range(2, n + 1):
                for i in range(1, n - k + 2):
                    c[k - 1] += gs[i] * cs[n - i - 1][k - 2]
            hn = self._f.zero()
            for m in range(1, n + 1):
                hn += fs[m] * c[m - 1]
            cs.append(c)
            yield hn


class IterableSeries(PowerSeries[A]):
    def __init__(self, it: Iterable[A], zero: Callable[[], A],
                 div: Callable[[A, A], A]):
        self._it = it
        self._zero = zero
        self._div = div

    def zero(self):
        return self._zero()

    def div(self, num: A, denom: A):
        return self._div(num, denom)

    def __iter__(self) -> Iterator[A]:
        return iter(self._it)


# We want to treat _all_ power series as infinite iterables which can
# themselves be reiterated arbitrarily. The IterableWrapper allows us to do
# exactly this given the factory function for some iterable. Typically, this
# factory will be powered by a Python generator under the hood.
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
