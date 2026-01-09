const main = () => {
  const n = 5;
  for (let i = 0; i <= n; i++) {
    for (mset of genMultisets(i)) {
      console.log(i, mset);
    }
  }
};

// Generates all possible multisets of total size n. This assumes that distinct
// set elements are ordered. If this is not the case, then the "shape" should
// be determined by integer partitions rather than compositions.
const genMultisets = function* (n) {
  // A multiset of size n (not-necessarily distinct) can be mapped into a
  // unique dense multiset of the integers in range [1..n], where the order
  // is canonicalized by element order. In this case, there is only one
  // canonical multiset per "shape", where a shape is given by the
  // multiplicities of its elements. There is a bijection between the
  // vector of multiplicities and integer compositions of size n. To actually
  // generate the multisets, we first generate compositions of the target size
  // in reverse lexico order. This ensures that the output _multiset_ is in
  // lexico (canonical) order, since we first maximize prefix lengths of
  // lower-valued elements.
  for (const c of genIntegerCompositions(n)) {
    let m = [];
    let i = 1;
    for (const count of c) {
      for (let k = 0; k < count; k++) {
        m.push(i);
      }
      i++;
    }
    yield m;
  }
};

// Generates integer compositions of n in _reverse_ lexicographical order. If
// the part sizes are interpreted as the _multiplicities_ of items in a
// multiset, then this yields multisets in _ascending_ lexicographical order.
const genIntegerCompositions = function* (n) {
  if (n < 0) {
    throw new Error("no compositions of a negative integer");
  }
  if (n == 0) {
    yield [];
  } else if (n == 1) {
    yield [1];
  } else {
    yield [n];
    for (let k = n - 1; k > 0; k--) {
      // k is the size of the leading part
      for (const c of genIntegerCompositions(n - k)) {
        yield [k, ...c];
      }
    }
  }
};

main();
