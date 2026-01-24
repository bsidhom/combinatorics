// This is a proper Gray code over RGS partitions. I ripped it directly from
// TAOCP, which discusses the code as developed by Ehrlich. It is essentially
// the same logic as my code which alternately appends a final part size in
// ascending or descending order within prefix RGSs, but uses a slightly
// modified scheme such that the final block index is _always_ 0 or 1. This
// guarantees that you can always fix the final part while "stepping" the prefix
// code, ensuring an edit distance of 1. Sadly, I didn't discover this on my own,
// but it's easy to see why it works once you make that realization. Unlike
// Knuth in Algorithm H, I use recursion to do iteration (just as in the pseudo
// Gray code solution) rather than following an iterative, non-recursive flow as
// in Algorithm H. This makes it simpler to follow in my opinion. I haven't
// quantified the difference, but for moderate test sizes, this is within about
// 10% of the performance of Algorithm H.

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
        // Start at 1 and count up, wrapping to 0 at max value? Otherwise,
        // start at 0 and count down (immediately wrapping to max value). This
        // is the scheme used by Ehrlich and described by Knuth when discussing
        // Gray codes for partition RGS. He doesn't mention it in the text, but
        // this works because _every_ partition prefix supports a final block of
        // either 0 or 1. My previous attempt (pseudo-Gray code) did not account
        // for this and is not actually a valid Gray code within RGS itself,
        // even if it corresponds to partition edit distances of 1. Moreover,
        // _neither_ code is cyclic, unfortunately.
        let mut up = false;
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
            if up {
                for i in 1..=m {
                    p.push(i);
                    f(m, p);
                    p.pop();
                }
                p.push(m + 1);
                f(m + 1, p);
                p.pop();
                // Wrap
                p.push(0);
                f(m, p);
                p.pop();
            } else {
                p.push(0);
                f(m, p);
                p.pop();
                // Wrap
                p.push(m + 1);
                f(m + 1, p);
                p.pop();
                for i in (1..=m).rev() {
                    p.push(i);
                    f(m, p);
                    p.pop();
                }
            }
            up = !up;
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
