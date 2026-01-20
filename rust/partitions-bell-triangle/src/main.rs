fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n: usize = args[1].parse().unwrap();
    partitions(n, |p| {
        println!("{p:?}");
    });
}

fn partitions<F>(n: usize, f: F) where F: FnMut(&[Vec<usize>]) {
    let mut ip = IndexedPartition::with_capacity(n);
    let mut p: Vec<Vec<usize>> = vec![vec![]; n];
    let mut f = f;
    if n == 0 {
        f(&[]);
    } else {
        sub_partitions(n-1, n-1, &mut AugmentationStack::new(), &mut ip, &mut |ip| {
            for i in 0..n {
                let part = ip.index[i];
                p[part].push(i);
            }
            f(&p[0..ip.part_count]);
            for part in p.iter_mut() {
                part.clear();
            }
            ip.clear();
        });
    }
}

fn sub_partitions<F>(n: usize, k: usize, ops: &mut AugmentationStack, ip: &mut IndexedPartition, f: &mut F) where F: FnMut(&mut IndexedPartition) {
    if n == 0 {
        assert_eq!(k, 0);
        ip.part_count = 1;
        // ip.index.clear();
        ip.index.push(0);
        ops.apply(ip);
        f(ip);
    } else {
        if k == 0 {
            ops.push(Augmentation::add_singleton());
            sub_partitions(n-1, n-1, ops, ip, f);
            ops.pop();
        } else {
            sub_partitions(n, k-1, ops, ip, f);
            ops.push(Augmentation::swappend(n, k));
            sub_partitions(n-1, k-1, ops, ip, f);
            ops.pop();
        }
    }
}

#[derive(Debug)]
struct AugmentationStack {
    stack: Vec<Augmentation>,
}

impl AugmentationStack {
    fn new() -> AugmentationStack {
        AugmentationStack { stack: Vec::new() }
    }
    
    fn apply(&self, ip: &mut IndexedPartition) {
        for augmentation in self.stack.iter().rev() {
            augmentation.apply(ip);
        }
    }

    fn push(&mut self, op: Augmentation) {
        self.stack.push(op);
    }

    fn pop(&mut self) {
        self.stack.pop().unwrap();
    }
}

#[derive(Debug)]
enum Augmentation {
    AddSingleton,
    Swappend { n: usize, k: usize },
}

impl Augmentation {
    fn add_singleton() -> Augmentation {
        Augmentation::AddSingleton
    }

    fn swappend(n: usize, k: usize) -> Augmentation {
        Augmentation::Swappend { n, k }
    }

    fn apply(&self, ip: &mut IndexedPartition) {
        match self {
            Augmentation::AddSingleton => {
                ip.index.push(ip.part_count);
                ip.part_count += 1;
            }
            &Augmentation::Swappend { n, k } => {
                ip.index.swap(n-1, k-1);
                ip.index.push(ip.index[k-1]);
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
        IndexedPartition { part_count: 0, index: Vec::with_capacity(n) }
    }
    fn clear(&mut self) {
        self.part_count = 0;
        self.index.clear();
    }
}
