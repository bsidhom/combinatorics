fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n: usize = args[1].parse().unwrap();
    gen_partitions(n, |p| {
        println!("{p:?}");
    });
}

// NOTE: The primary reason to use an internal-style iterator entrypoint is for
// uniformity with other implementations. I might eventually refactor these to
// a single main entrypoint and make the implementation pluggable. This would
// make it easier to compare different generators.
fn gen_partitions<F>(n: usize, f: F)
where
    F: FnMut(&[Vec<usize>]),
{
    let mut f = f;
    let mut iter = LexicoPartitionIter::new(n);
    while let Some(p) = iter.next() {
        f(p);
    }
}

#[derive(Debug)]
struct LexicoPartitionIter {
    p: Option<Vec<Vec<usize>>>,
    ready: bool,
    unslotted: UnslottedItems,
}

impl LexicoPartitionIter {
    fn new(n: usize) -> LexicoPartitionIter {
        let mut p = Vec::with_capacity(n);
        for i in 1..=n {
            p.push(vec![i]);
        }
        let p = Some(p);
        let ready = true;
        let unslotted = UnslottedItems::new(n);
        LexicoPartitionIter {
            p,
            ready,
            unslotted,
        }
    }
}

trait LendingIterator {
    type Item<'a>
    where
        Self: 'a;
    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
}

impl LendingIterator for LexicoPartitionIter {
    type Item<'a> = &'a [Vec<usize>];

    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>> {
        if let Some(mut p) = self.p.take() {
            if !self.ready {
                if increment(&mut p, &mut self.unslotted) {
                    self.p = Some(p);
                } else {
                    self.p = None;
                }
            } else {
                self.p = Some(p);
            }
            // NOTE: We only start ready the first iteration. Afterward, we
            // compute the next partition on demand. This allows full laziness
            // and also allows us to share the partition memory--if we eagerly
            // mutated it in place, we couldn't share by reference.
            self.ready = false;
            self.p.as_ref().map(|p| p.as_slice())
        } else {
            None
        }
    }
}

#[derive(Debug)]
struct UnslottedItems {
    // Invariant: items are _always_ stored in ascending order.
    items: Vec<usize>,
}

impl UnslottedItems {
    fn new(n: usize) -> UnslottedItems {
        let items = Vec::with_capacity(n);
        UnslottedItems { items }
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    fn max(&self) -> Option<usize> {
        self.items.last().map(|x| *x)
    }

    fn insert(&mut self, item: usize) {
        let sorted_size = self.items.len();
        self.items.push(item);
        sort_tail(&mut self.items, sorted_size);
    }

    fn insert_all(&mut self, items: &[usize]) {
        for item in items {
            self.insert(*item);
        }
    }

    fn pop_least_above(&mut self, n: usize) -> Option<usize> {
        if let Some(max) = self.max() {
            if max <= n {
                // Due to the sort invariant, we have no candidates.
                return None;
            }
        } else {
            return None;
        }
        let index = self
            .items
            .iter()
            .position(|x| *x >= n)
            .expect("assertion failure: should have found a candidate");
        Some(self.items.remove(index))
    }

    fn clear(&mut self) {
        self.items.clear();
    }
}

fn increment(p: &mut Vec<Vec<usize>>, unslotted: &mut UnslottedItems) -> bool {
    if p.is_empty() {
        return false;
    }
    loop {
        // Precondition: p is non-empty, each part is non-empty
        if unslotted.is_empty() {
            if p.last().unwrap().len() < 3 {
                // We can't increment the last part.
                if p.len() <= 1 {
                    // No earlier parts to increment.
                    p.clear();
                    return false;
                }
                // Continue up the prefix afer inserting this into the bag.
                unslotted.insert_all(p.last().unwrap());
                p.pop();
            } else {
                // We have at least 3 items in the last part and an empty bag.
                // We can increment the partition by promoting the current last
                // item to the penultimate position and moving the previous item
                // into the bag.
                let x = p.last_mut().unwrap().pop().unwrap();
                unslotted.insert(p.last_mut().unwrap().pop().unwrap());
                p.last_mut().unwrap().push(x);
                append_minimum(p, unslotted);
                return true;
            }
        } else {
            // We have at least one unslotted item.
            if let Some(x) = unslotted.pop_least_above(*p.last().unwrap().last().unwrap()) {
                p.last_mut().unwrap().push(x);
                append_minimum(p, unslotted);
                return true;
            } else {
                // Put this part's last element into the bag of unslotted items.
                unslotted.insert(p.last_mut().unwrap().pop().unwrap());

                // We cannot append to the current part. Instead, attempt to
                // increment an earlier item if possible. Note that we must
                // retain the invariant that the first item in any given
                // partition is the _least_ of all remaining unslotted items, as
                // this is required for canonicalization.  Consequently, we
                // cannot increment or otherwise modify the first element of the
                // current part and have to work up the prefix in that case.
                while p.last().unwrap().len() > 1 {
                    let old_last = p.last_mut().unwrap().pop().unwrap();
                    let new_last = unslotted.pop_least_above(old_last);
                    unslotted.insert(old_last);
                    if let Some(new_last) = new_last {
                        p.last_mut().unwrap().push(new_last);
                        append_minimum(p, unslotted);
                        return true;
                    }
                }
                if p.last().unwrap().len() > 0 {
                    // Add the last item to the bag; this can't be incremented
                    // as described above. Note that we include this case to
                    // handle the edge case where the last part _started_ with a
                    // single element.
                    unslotted.insert(p.last_mut().unwrap().pop().unwrap());
                }

                // The current part is empty and cannot be directly incremented.
                if p.len() == 1 {
                    // This was the first part; there's nothing else to increment.
                    return false;
                }
                // We know there is an earlier part which we might be able to increment.
                // Move up the prefix to an earlier part.
                // NOTE: The last part has been fully drained into `unslotted`
                // by this point.
                p.pop();
            }
        }
    }
}

// Append the minimum possible suffix to the given partition prefix composed of
// the given unslotted items.
fn append_minimum(p: &mut Vec<Vec<usize>>, unslotted: &mut UnslottedItems) {
    // TODO: Make a partition a wrapper that holds a constant-sized outer vector
    // and a "used part size". This would allow us to reuse the preallocated
    // blocks within. For now, we just allocate new blocks every time this is
    // called.
    for &item in unslotted.items.iter() {
        p.push(vec![item]);
    }
    unslotted.clear();
}

fn sort_tail<T: Ord>(items: &mut [T], sorted_prefix: usize) {
    for j in sorted_prefix..items.len() {
        for i in (1..=j).rev() {
            if items[i - 1] <= items[i] {
                break;
            }
            items.swap(i - 1, i);
        }
    }
}
