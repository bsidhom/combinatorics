fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n = args[1].parse().unwrap();
    partitions(n, |p| {
        println!("{p:?}");
    })
}

fn partitions<F>(n: usize, f: F)
where
    F: FnMut(&[Vec<usize>]),
{
    let mut f = f;
    let mut p = vec![Vec::new(); n];
    let mut inner_f = |ip: &mut IndexedPartition| {
        for part in p.iter_mut() {
            part.clear();
        }
        for i in 0..n {
            p[ip.index[i]].push(i);
        }
        f(&p[..ip.part_count]);
    };
    let mut ip = IndexedPartition::with_capacity(n);
    for k in 0..=n {
        stirling_partitions(n, k, &mut AugmentationStack::new(), &mut ip, &mut inner_f);
    }
}

fn stirling_partitions<F>(n: usize, k: usize, ops: &mut AugmentationStack, ip: &mut IndexedPartition, f: &mut F)
where
    F: FnMut(&mut IndexedPartition),
{
    if n == k {
        // There's only one way to achieve this: put each item into its own part.
        ip.clear();
        for i in 0..n {
            ip.index.push(i);
        }
        ip.part_count = n;
        ops.apply(ip);
        f(ip);
    } else if k > 0 && k <= n {
        // Put n into a singleton partition.
        ops.push(Augmentation::add_singleton());
        stirling_partitions(n-1, k-1, ops, ip, f);
        ops.pop();

        for i in 0..k {
            ops.push(Augmentation::insert_at(i));
            stirling_partitions(n-1, k, ops, ip, f);
            ops.pop();
        }
    }
    // If we match neither of the above, there are no valid partitions.
}

#[derive(Debug)]
struct AugmentationStack {
    ops: Vec<Augmentation>,
}

impl AugmentationStack {
    fn new() -> AugmentationStack {
        let ops = Vec::new();
        AugmentationStack { ops }
    }

    fn push(&mut self, op: Augmentation) {
        self.ops.push(op);
    }

    fn pop(&mut self) {
        self.ops.pop();
    }

    fn apply(&self, ip: &mut IndexedPartition) {
        for op in self.ops.iter().rev() {
            op.apply(ip);
        }
    }
}

#[derive(Debug)]
enum Augmentation {
    AddSingleton,
    InsertAt(usize),
}

impl Augmentation {
    fn add_singleton() -> Augmentation {
        Augmentation::AddSingleton
    }

    fn insert_at(k: usize) -> Augmentation {
        Augmentation::InsertAt(k)
    }

    fn apply(&self, ip: &mut IndexedPartition) {
        match self {
            Augmentation::AddSingleton => {
                ip.index.push(ip.part_count);
                ip.part_count += 1;
            }
            &Augmentation::InsertAt(k) => {
                ip.index.push(k);
            }
        }
    }
}

#[derive(Debug)]
struct IndexedPartition {
    part_count: usize,
    index: Vec<usize>,
}

impl IndexedPartition {
    fn with_capacity(n: usize) -> IndexedPartition {
        let part_count = 0;
        let index = Vec::with_capacity(n);
        IndexedPartition { part_count, index }
    }

    fn clear(&mut self) {
        self.index.clear();
        self.part_count = 0;
    }
}
