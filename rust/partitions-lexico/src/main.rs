// Rust is not very amenable to combinatorics due to lack of a friendly
// generator/coroutine syntax or implementation technique. I'm not sure if this
// will stick around, but I've added this as a test to see how performance might
// improve for generating set partitions with fewer allocations. As expected, it
// runs faster and uses substantially less memory. However, the speedup is
// dramatically mitigated by the fact that you have to repeatedly scan over the
// exclusion array when determining which elements to add/modify in the output
// partition. I expected cache locality to help here, but performance barely
// beats JavaScript and doesn't appear to improve with scale. The saving grace
// is that because this uses nearly-constant memory (the size of input sets is
// necessarily limited due to combinatorial explosion), the stack/heap do not
// blow up and you can run with sets as large as you can tolerate the runtime
// for. This is in contrast to the JavaScript implementation which blows up
// around n = 13 on my test computer due to memory limits.
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n: usize = args[1].parse().unwrap();
    let items: Vec<usize> = (1..=n).into_iter().collect();
    gen_partitions(&items[..], |p| {
        println!("{p:?}");
    });
}

fn gen_partitions<T, F>(items: &[T], f: F)
where
    F: FnMut(&[Vec<&T>]),
    T: std::fmt::Debug,
{
    let mut f = f;
    fn rec<'a, T, F>(
        prefix: &mut Vec<Vec<&'a T>>,
        items: &'a [T],
        remaining_count: usize,
        exclude: &mut [bool],
        start_index: usize,
        min_insert_index: usize,
        f: &mut F,
    ) where
        F: FnMut(&[Vec<&T>]),
        T: std::fmt::Debug,
    {
        // println!("prefix: {prefix:?}, i: {start_index}, remaining: {remaining_count}, exclude: {exclude:?}");
        if remaining_count == 0 {
            f(prefix);
        } else {
            let mut i = start_index;
            let start_index = loop {
                if !exclude[i] {
                    break i;
                }
                // NOTE: We depend on the precondition that remaining_count is
                // correct (and the start offset is correct). This ensures we
                // never go beyond the end of the items slice.
                i += 1;
            };
            prefix.push(vec![&items[start_index]]);
            exclude[start_index] = true;
            rec(
                prefix,
                items,
                remaining_count - 1,
                exclude,
                start_index + 1,
                start_index + 1,
                f,
            );
            exclude[start_index] = false;
            prefix.pop();
            if !prefix.is_empty() {
                for i in min_insert_index..(items.len()) {
                    if exclude[i] {
                        continue;
                    }
                    exclude[i] = true;
                    prefix.last_mut().unwrap().push(&items[i]);
                    let start_index = if i == start_index {
                        // Recurse at the next index.
                        start_index + 1
                    } else {
                        // Otherwise, we have effectively spliced out a single
                        // element and need to go back to the original start point,
                        // skipping over elements we've already added (via the
                        // exclude list).
                        start_index
                    };
                    rec(
                        prefix,
                        items,
                        remaining_count - 1,
                        exclude,
                        start_index,
                        i + 1,
                        f,
                    );
                    prefix.last_mut().unwrap().pop();
                    exclude[i] = false;
                }
            }
        }
    }
    let mut prefix = vec![];
    let mut exclude = vec![false; items.len()];
    rec(&mut prefix, items, items.len(), &mut exclude, 0, 0, &mut f);
}
