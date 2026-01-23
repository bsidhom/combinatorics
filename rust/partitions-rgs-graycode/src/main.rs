// This is only slightly slower than lexicographically-ordered restricted growth
// strings despite being significantly more readable and leaving lots of
// performance on the table. Probably the best technique so far on balance.

// TODO: Optimize for memory reuse. For now, this closely follows
// https://gist.github.com/bsidhom/bd286aa1c3d685da606de64be3594305
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let n = args[1].parse().unwrap();
    rgs_graycode(n, |p| {
        println!("{p:?}");
    });
}

fn rgs_graycode<F>(n: usize, f: F)
where
    F: FnMut(&[usize]),
{
    let mut f = f;
    let mut p = Vec::with_capacity(n);
    // Annoyingly, you can't apply an HRTB to the lifetime parameter(s) of an
    // opaque type (impl FnMut here), so we have to wrap it in an identity function.
    // Sadly, this doesn't actually help much because we have to allocate at each
    // level of recursion within the helper itself and use a trait object to
    // avoid infinite recursion in the expansion.
    let mut f = wrap_fn(|_m, p| {
        f(p);
    });
    rgs_graycode_helper(n, &mut p, &mut f);
}

fn rgs_graycode_helper(n: usize, p: &mut Vec<usize>, f: &mut dyn FnMut(usize, &mut Vec<usize>)) {
    // TODO: Figure out how to efficiently modify prefix partitions without
    // generating closures at each level. We're stack-allocating the callback
    // here, but I'm not sure what the representation implications are when
    // this gets converted to a trait object.

    if n == 0 {
        p.clear();
        f(0, p);
    } else if n == 1 {
        p.clear();
        p.push(0);
        f(0, p);
    } else {
        let mut odd = true;
        let mut f = wrap_fn(|m, p| {
            // NOTE: While I would like to use a last-part "iterator" (either
            // as a helper taking a callback or as a proper external iterator),
            // the code is too noisy or bloated to make it worth-while right
            // now. The purpose here is to make the logic as simple as possible
            // to follow.

            // NOTE: Pre-allocating and sharing the `p` vector does make things
            // faster than creating a fresh one here, but not by as much as you
            // you might expect. And because allocations only happen once per
            // level, it matters less as `n` gets larger.
            if odd {
                p.push(m + 1);
                f(m + 1, p);
                p.pop();
                for i in (0..=m).rev() {
                    p.push(i);
                    f(m, p);
                    p.pop();
                }
            } else {
                for i in 0..=m {
                    p.push(i);
                    f(m, p);
                    p.pop();
                }
                p.push(m + 1);
                f(m + 1, p);
                p.pop();
            }
            odd = !odd;
        });
        rgs_graycode_helper(n - 1, p, &mut f);
    }
}

// We use this because in-line opaque closures cannot be explicitly typed or
// given higher-ranked trait bounds (universal lifetime parameters).
fn wrap_fn<F>(f: F) -> F
where
    F: for<'a> FnMut(usize, &'a mut Vec<usize>),
{
    f
}
