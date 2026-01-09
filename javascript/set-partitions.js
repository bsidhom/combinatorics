const main = () => {
  for (const p of genPartitions([1, 2, 3, 4, 5])) {
    console.log(JSON.stringify(p));
  }
};

const genPartitions = function* (set) {
  // This is essentially the same logic as
  // https://gist.github.com/bsidhom/645056f81b43c29e63a737cf91854753 but with
  // less copying.
  const gen = function* (prefix, set, minInsertIndex) {
    if (prefix.length == 0) {
      throw new Error("empty prefix");
    }
    // Precondition: prefix is non-empty.
    if (set.length == 0) {
      yield prefix;
    } else {
      prefix.push([set[0]]);
      yield* gen(prefix, set.slice(1), 0);
      prefix.pop();
      for (let i = minInsertIndex; i < set.length; i++) {
        prefix.at(-1).push(set[i]);
        yield* gen(prefix, set.toSpliced(i, 1), i);
        prefix.at(-1).pop();
      }
    }
  };
  if (set.length == 0) {
    yield [];
  } else {
    yield* gen([[set[0]]], set.slice(1), 0);
  }
};

main();
