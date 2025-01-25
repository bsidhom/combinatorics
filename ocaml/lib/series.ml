type t = Q.t Seq.t

exception Composition_of_nonzero_constant

let coeffs fs = fs

let rec nth n fs =
  match Seq.uncons fs with
  | None -> Q.zero
  | Some (f, fs) -> if n <= 0 then f else nth (n - 1) fs

let zero = Seq.empty
let one = Seq.return Q.one

let zpow n =
  let zeros = Seq.repeat Q.zero |> Seq.take n in
  Seq.append zeros (Seq.return Q.one)

let z = zpow 1

let rec ( + ) fs gs =
  let value =
    lazy
      Seq.(
        match (fs (), gs ()) with
        | Cons (f, fs'), Cons (g, gs') -> Cons (Q.(f + g), fs' + gs')
        | (Cons _ as fs), Nil -> fs
        | Nil, (Cons _ as gs) -> gs
        | Nil, Nil -> Nil)
  in
  fun () -> Lazy.force value

let neg = Seq.map Q.neg
let ( - ) fs gs = fs + neg gs

let ( *. ) c =
  let mul f = Q.(c * f) in
  Seq.map mul

let rec ( * ) fs gs =
  let value =
    lazy
      Seq.(
        match (fs (), gs ()) with
        | Cons (f, fs'), Cons (g, gs') ->
            Cons (Q.(f * g), (f *. gs') + (fs' * gs))
        | Nil, _ | _, Nil -> Nil)
  in
  fun () -> Lazy.force value

let rec ( / ) fs gs =
  let value =
    lazy
      Seq.(
        match (fs (), gs ()) with
        | Cons (f, fs'), Cons (g, gs') ->
            if Q.(g = zero) then
              if Q.(f = zero) then
                (* WARNING: This eagerly materializes both lists until the next non-zero
  entry, which is the only way to pull out the next term. *)
                (fs' / gs) ()
              else raise Division_by_zero
            else
              let q = Q.(f / g) in
              Cons (q, (fs' - (q *. gs')) / gs)
        | Cons (f, fs'), Nil ->
            if Q.(f = zero) then
              (* As above, this eagerly materializes. *)
              (fs' / gs) ()
            else raise Division_by_zero
        | Nil, Cons _ | Nil, Nil -> Nil)
  in
  fun () -> Lazy.force value

let rec compose fs gs =
  let value =
    lazy
      Seq.(
        match (fs (), gs ()) with
        | Cons (f, fs'), Cons (g, gs') ->
            if Q.(g = zero) then Cons (f, gs' * compose fs' gs)
            else raise Composition_of_nonzero_constant
        | Cons (f, _), Nil -> Cons (f, Seq.empty)
        | Nil, _ -> Nil)
  in
  fun () -> Lazy.force value
