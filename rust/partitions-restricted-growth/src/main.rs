// This follows Algorithm H from TAOCP volume 4A, section 7.2.1.5. I've been
// calling the element-to-part-number dense index an "indexed partition", but
// Knuth calls it a "restricted growth string" (with some additional
// canonicalization criteria).

// NOTE: I expected this to be the fastest since it does not require any
// recursion or other nested function calls. Additionally, the tracking data
// structures are small, simple, and cache-friendly. It is indeed faster than
// other techinques, but is still in the same realm.

fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n: usize = args[1].parse().unwrap();
    partitions(n, |ip| {
        // NOTE: Debug-printing custom structs is surprisingly expensive (and
        // also requires more bytes of I/O). For speed, just print the raw
        // index vector (without translating into parts).
        let p = &ip.index;
        println!("{p:?}");
    });
}

fn partitions<F>(n: usize, f: F)
where
    F: FnMut(&IndexedPartition),
{
    let mut ip = IndexedPartition::new(n);
    let mut f = f;
    if n == 0 {
        f(&ip);
        return;
    }
    if n == 1 {
        // We handle this case specially to make the nested loop below simpler:
        // since we know that n >= 2, we can always start searching from the
        // penultimate element without doing a range check. Depending on branch
        // prediction, this _might_ even make the loop faster (though I haven't
        // tested this).
        f(&ip);
        return;
    }

    // NOTE: The `a` vector in Algorithm H is actually the partition index
    // itself. Similarly, we directly compute the part count from m and the
    // index.
    let mut b = vec![1; n - 1];
    let mut m = 1;
    // TODO: Consider rewriting this loop to make it more idiomatic. It
    // currently follows Algorithm H very closely to the point of making it
    // hard to read. For example, the if statement at the end of the core loop
    // could be made uniform and flattened, at the expense of a few extra
    // instructions (assuming they don't get optimized away).
    loop {
        // The last element has realized its maximum part index. This means we
        // add one to the effective partition size and also cannot increment by
        // simply bumping the last index.
        let an_maxed = ip.index[n - 1] == m;
        ip.part_count = if an_maxed { m + 1 } else { m };
        f(&ip);
        if an_maxed {
            // Try to increment the part of a smaller element if possible. Let
            // j be the index of the rightmost item which has _not_ yet been
            // maxed out. If j = 0, then we're done: we can't increment the
            // part of the smallest item because this violates the restricted
            // growth string condition. If we do find a valid j to increment,
            // do so and then zero out everything to its right.
            // NOTE: Here and elsewhere I'm using 0-indexing in contrast to
            // Knuth.
            let mut j = n - 2;
            while ip.index[j] == b[j] {
                j -= 1;
            }
            if j == 0 {
                // We cannot increment the part of the first element. See above.
                return;
            }
            ip.index[j] += 1;
            // Zero out the tail.
            let aj_maxed = ip.index[j] == b[j];
            // b[j] sets the high water mark (incrementing by one if it has
            // reached its potential, otherwise tying).
            m = if aj_maxed { b[j] + 1 } else { b[j] };
            j += 1;
            while j < n - 1 {
                ip.index[j] = 0;
                b[j] = m;
                j += 1;
            }
            ip.index[n - 1] = 0;
        } else {
            // Increment and continue.
            ip.index[n - 1] += 1;
        }
    }
}

#[derive(Debug)]
struct IndexedPartition {
    part_count: usize,
    index: Vec<usize>,
}

impl IndexedPartition {
    fn new(n: usize) -> IndexedPartition {
        IndexedPartition {
            part_count: 0,
            index: vec![0; n],
        }
    }
}
