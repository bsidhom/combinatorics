open Combinatorics

let () =
  let fs = Constructions.powerset 10 Series.z in
  let print (i, c) =
    let s = Q.to_string c in
    Printf.printf "%d: %s\n%!" i s
  in
  let fs = Seq.zip (Seq.ints 0) fs in
  Seq.iter print fs
