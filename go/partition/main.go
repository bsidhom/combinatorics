// SPDX-License-Identifier: MPL-2.0

package main

import (
	"fmt"
	"iter"
	"os"
	"strconv"
)

func main() {
	n, err := strconv.Atoi(os.Args[1])
	if err != nil {
		panic(err)
	}
	for p := range Partitions(n) {
		fmt.Printf("%v\n", p)
	}
}

// Partitions generates all partitions of the set [1,..n]. The yielded
// partitions are reused and mutated in-place, so if consumers require long-term
// access to results, they must be copied first.
func Partitions(n int) iter.Seq[[][]int] {
	return func(yield func([][]int) bool) {
		if n == 0 {
			yield([][]int{})
		} else {
			partition := make([][]int, n)
			for p := range subPartitions(n-1, n-1, nopAugmentation) {
				resetSliceSlice(partition)
				for i := range n {
					part := p.index[i]
					// NOTE: The computed indices are zero-based, but we want
					// to partition the set [1,..n], so we add one.
					partition[part] = append(partition[part], i+1)
				}
				yield(partition[:p.partCount])
			}
		}
	}
}

// subPartitions generates all partitions of the set [1,..,n+1] where the
// partition containing (n+1) contains only (n+1) and a subset of [1,..,k].
// This follows the logic of the Bell triangle. As a runtime optimization, we
// allow the caller to pass an augmentation function (augmentPartition) which
// modifies the generated partition before downstream consumption. This allows
// efficient sub-iterators: recursive calls just pass an augmentation function
// and then consume iterator results directly rather than recursively spawning
// iterators and then "mapping" them after the fact.
func subPartitions(n int, k int, augmentPartition func(*IndexedPartition)) iter.Seq[IndexedPartition] {
	// TODO: Consider reusing a single IndexedPartition everywhere and mutating
	// it in-place. I haven't yet considered whether this is actually feasible,
	// but it seems likely to be so since we're effectively storing the full
	// computation graph in the nested augmentPartition wrappers at each level
	// and can "undo" this. On the other hand, the heavy use of temporary
	// closures means we're already allocating a lot.
	if k > n {
		panic(fmt.Sprintf("n > k: n=%d, k=%d", n, k))
	}
	return func(yield func(IndexedPartition) bool) {
		// fmt.Printf("subPartitions(%d, %d)\n", n, k)
		switch n {
		case 0:
			p := IndexedPartition{partCount: 1, index: []int{0}}
			augmentPartition(&p)
			yield(p)
		default:
			switch k {
			case 0:
				// Item (n+1) resides in a singleton part. Generate _all_
				// (unrestricted) partitions of [1,..,n] and then form a new
				// one by appending (n+1) into its own part.
				subPartitions(n-1, n-1, func(p *IndexedPartition) {
					p.index = append(p.index, p.partCount)
					p.partCount += 1
					// Always apply the outer augmentation last.
					augmentPartition(p)
				})(yield)
			default:
				// Item (n+1) resides in a part with some subset of
				// [1,..,k]. We split this into 2 cases: the part _does not_
				// contain k, and the part _does_ contain k.

				// When the part does _not_ contain k, this is identical to
				// partitions where (n+1) lives with a subset of [1,..,k-1]. In
				// other words, we don't need to augment the returned
				// partitions.
				subPartitions(n, k-1, augmentPartition)(yield)

				// Now we want to generate partitions where the part with (n+1)
				// _does_ contain k. Remove (n+1) from consideration for a
				// moment. Since (n+1) was _not_ the only element in its part
				// (it at least contains k as well), this will be drawn from
				// _some_ valid partition of [1,..,n]. Note that k must have
				// been the largest item in this part, since we have removed
				// (n+1) and the remaining items were from [1,..,k]. In other
				// words, we're essentially generating partitions where k lies
				// in a part with [1,..,k-1]. This is precisely
				// subPartitions(n-1,k-1), but where n and k have been swapped!
				// Note that they are exchangeable because we're partitioning
				// [1,..,n] and putting one of either n or k in a part with any
				// subset of [1,..,k-1] (i.e., that subset necessarily contains
				// neither of these two items, and they are considered
				// "equivalent").
				subPartitions(n-1, k-1, func(p *IndexedPartition) {
					// Swap n and k. This is just the relabeling described above.
					// Note that we use zero-indexing, so we have to adjust n
					// and k by 1 here.
					p.index[n-1], p.index[k-1] = p.index[k-1], p.index[n-1]
					// Now ensure that we place (n+1) into the same (final) part
					// as k.
					// NOTE: We do _not_ increment the number of parts.
					p.index = append(p.index, p.index[k-1])
					// Run any outer augmentations.
					augmentPartition(p)
				})(yield)
			}
		}
	}
}

func nopAugmentation(p *IndexedPartition) {}

func resetSliceSlice[T any](xss [][]T) {
	for i := range xss {
		xss[i] = xss[i][:0]
	}
}

type IndexedPartition struct {
	partCount int
	index     []int
}
