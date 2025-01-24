module type S = sig
  (* TODO: Consider making this polymorphic in the coefficient type. *)
  type t = Q.t Seq.t

  val coeffs : t -> Q.t Seq.t
  val nth : int -> t -> Q.t
  val zero : t
  val one : t
  val z : t
  val zpow : int -> t
  val neg : t -> t
  val ( + ) : t -> t -> t
  val ( - ) : t -> t -> t
  val ( *. ) : Q.t -> t -> t
  val ( * ) : t -> t -> t
  val ( / ) : t -> t -> t
  val compose : t -> t -> t
end
