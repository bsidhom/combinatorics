// This is slightly faster than the lexicographically-ordered restricted growth 
// string technique despite being more readable _and_ using trait objects when
// passing recursive closures! Probably the best technique so far on balance.

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
    // Annoyingly, you can't apply an HRTB to the lifetime parameter(s) of an
    // opaque type (impl FnMut here), so we have to wrap it in an identity function.
    // Sadly, this doesn't actually help much because we have to allocate at each
    // level of recursion within the helper itself and use a trait object to
    // avoid infinite recursion in the expansion.
    let mut f = wrap_fn(|_m, p| {
        f(p);
    });
    rgs_graycode_helper(n, &mut f);
}

fn rgs_graycode_helper(n: usize, f: &mut dyn FnMut(usize, &[usize])) {
    // TODO: Figure out how to efficiently modify prefix partitions without
    // generating closures at each level. We're stack-allocating the callback
    // here, but I'm not sure what the representation implications are when
    // this gets converted to a trait object.
    if n == 0 {
        f(0, &[]);
    } else if n == 1 {
        f(0, &[0]);
    } else {
        let mut odd = true;
        let mut f = wrap_fn(|m, prefix| {
            // NOTE: While I would like to use a last-part "iterator" (either
            // as a helper taking a callback or as a proper external iterator),
            // the code is too noisy or bloated to make it worth-while right
            // now. The purpose here is to make the logic as simple as possible
            // to follow.

            // TODO: The easiest performance win is probably to reuse p between
            // all recursion levels. On the other hand, this isn't as expensive
            // as it might appear because we only allocate logarithmically in
            // depth of recursion and reuse the vector when yielding.
            let mut p = Vec::with_capacity(n);
            p.extend_from_slice(prefix);
            if odd {
                p.push(m + 1);
                f(m + 1, &p);
                p.pop();
                for i in (0..=m).rev() {
                    p.push(i);
                    f(m, &p);
                    p.pop();
                }
            } else {
                for i in 0..=m {
                    p.push(i);
                    f(m, &p);
                    p.pop();
                }
                p.push(m + 1);
                f(m + 1, &p);
                p.pop();
            }
            odd = !odd;
        });
        rgs_graycode_helper(n - 1, &mut f);
    }
}

fn wrap_fn<F>(f: F) -> F
where
    F: for<'a> FnMut(usize, &'a [usize]),
{
    f
}
