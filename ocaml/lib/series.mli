module type S = Series_intf.S

module Ephemeral : S
include Series_intf.S
