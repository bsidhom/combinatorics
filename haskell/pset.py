#!/usr/bin/env python3

def main():
    for xs in gen(tuple(range(1, 25))):
        print(xs)

def gen(xs):
    def rec(result, xs):
        if len(xs) == 0:
            yield result
        else:
            yield from rec(result, xs[1:])
            yield from rec(result + (xs[0],), xs[1:])
    yield from rec((), xs)

if __name__ == "__main__":
    main()
