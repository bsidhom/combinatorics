open Combinatorics

let part_size n = Series.(one / (one - zpow n))

let partitions_up_to_part_size n =
  let rec prod k acc =
    if k > n then acc else prod (k + 1) Series.(acc * part_size k)
  in
  prod 1 Series.one

let _ = partitions_up_to_part_size

let () =
  (*
  let nickels = Series.((one - zpow 30) / (one - zpow 5)) in
  let dimes = Series.((one - zpow 40) / (one - zpow 10)) in
  let quarters = Series.((one - zpow 75) / (one - zpow 25)) in
  let fs = Series.(nickels * dimes * quarters) in
  *)
  (*
  let pennies = Series.(one / (one - z)) in
  let nickels = Series.(one / (one - zpow 5)) in
  let dimes = Series.(one / (one - zpow 10)) in
  let quarters = Series.(one / (one - zpow 25)) in
  let fs = Series.(pennies * nickels * dimes * quarters) in
  *)
  let fs = partitions_up_to_part_size 100 in
  let _ = fs in
  let fs = Series.(one / (one - z)) in
  let fs = Series.(fs * fs * fs * fs * fs) in
  let print (i, c) =
    let s = Q.to_string c in
    Printf.printf "%03d: %s\n%!" i s
  in
  let fs = Seq.zip (Seq.ints 0) fs in
  Seq.take 101 fs |> Seq.iter print
