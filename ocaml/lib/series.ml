module type S = sig
  include Series_intf.S
end

module Ephemeral = struct
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

  let ( + ) fs gs =
    let rec go fs gs () =
      match (Seq.uncons fs, Seq.uncons gs) with
      | Some (f, fs'), Some (g, gs') ->
          Seq.Cons (Q.(f + g), go fs' gs')
          (* Is it better to return the original fs or gs sequence below rather than
    reconstructing it? *)
      | Some (f, fs'), None -> Seq.Cons (f, fs')
      | None, Some (g, gs') -> Seq.Cons (g, gs')
      | None, None -> Seq.Nil
    in
    go fs gs

  let neg = Seq.map Q.neg
  let ( - ) fs gs = fs + neg gs

  let ( *. ) c =
    let mul f = Q.(c * f) in
    Seq.map mul

  let ( * ) fs gs =
    let rec go fs gs () =
      match (Seq.uncons fs, Seq.uncons gs) with
      | Some (f, fs'), Some (g, gs') ->
          let head = Q.(f * g) in
          let tail_left = f *. gs' in
          let tail_right = go fs' gs in
          let tail = tail_left + tail_right in
          Seq.Cons (head, tail)
      | None, _ | _, None -> Seq.Nil
    in
    go fs gs

  let ( / ) fs gs =
    let rec go fs gs () =
      match (Seq.uncons fs, Seq.uncons gs) with
      | Some (f, fs'), Some (g, gs') ->
          if Q.(f = zero) && Q.(g = zero) then
            (* WARNING: This eagerly materializes both lists until the next non-zero
      entry, which is the only way to pull out the next term. *)
            go fs' gs' ()
          else if Q.(g = zero) then raise Division_by_zero
          else
            let q = Q.(f / g) in
            let tail_numerator = fs' - (q *. gs') in
            let tail = go tail_numerator gs in
            Seq.Cons (q, tail)
      | Some (f, fs'), None ->
          if Q.(f = zero) then
            (* As above, this eagerly materializes. *)
            go fs' gs ()
          else raise Division_by_zero
      | None, Some _ | None, None -> Seq.Nil
    in
    go fs gs

  let compose fs gs =
    let rec go fs gs () =
      match (Seq.uncons fs, Seq.uncons gs) with
      | Some (f, fs'), Some (g, gs') ->
          if Q.(g = zero) then
            let tail = gs' * go fs' gs in
            Seq.Cons (f, tail)
          else raise Composition_of_nonzero_constant
      | Some (f, _), None -> Seq.Cons (f, Seq.empty)
      | None, _ -> Seq.Nil
    in
    go fs gs
end

module S = Ephemeral

type t = Q.t Seq.t

let coeffs fs = fs

(* NOTE: We explicitly do NOT memoize anything we know to have O(1) terms. *)
let nth = S.nth
let zero = S.zero
let one = S.one
let z = S.z

(* TODO: Consider memoizing iff n exceeds some threshold. *)
let zpow n = S.zpow n |> Seq.memoize
let neg t = S.neg t |> Seq.memoize
let ( + ) fs gs = S.(fs + gs) |> Seq.memoize
let ( - ) fs gs = S.(fs - gs) |> Seq.memoize
let ( *. ) c fs = S.(c *. fs) |> Seq.memoize
let ( * ) fs gs = S.(fs * gs) |> Seq.memoize
let ( / ) fs gs = S.(fs / gs) |> Seq.memoize
let compose fs gs = S.compose fs gs |> Seq.memoize
