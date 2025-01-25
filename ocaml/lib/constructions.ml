(* Both of series below _could_ be implemented as quotients, but the direct
formulation is substantially more efficient in practice. *)
let geometric = Seq.repeat Q.one
let geometric_trunc n = geometric |> Seq.take (n + 1)

let exp n =
  let c i =
    let d = Z.fac i in
    Q.make Z.one d
  in
  Seq.init (n + 1) c

(* TODO: The powerset construction appears to be badly broken. Need to figure
out what's happening. Unfortunately, the translation is complicated due to the 
exp-log transformation. I might revisit this using the direct product form. *)
(* Note that this and the multiset construction only converge if f0 is 0. *)
let powerset n fs =
  let rec go k acc =
    if k > n then acc
    else
      let sign = if k mod 2 = 0 then Z.(neg one) else Z.one in
      let coefficient = Q.make sign (Z.of_int k) in
      let arg = Series.zpow k in
      let gs = Series.(coefficient *. (compose fs arg)) in
      go (k + 1) Series.(acc + gs)
  in
  let parts = go 1 (Series.zero |> Seq.take (n + 1)) in
  Series.compose (exp n) parts

let multiset _ = failwith "todo"
let cycle _ = failwith "todo"
