module PowerSeries (
    PowerSeries,
    toList,
    geometric,
    atom,
    neutral,
    powerset,
    zpow,
    compose,
    (.*)
) where

newtype PowerSeries = PowerSeries [Integer] deriving (Eq, Show)

toList :: PowerSeries -> [Integer]
toList (PowerSeries as) = as

powerset :: [a] -> [[a]]
powerset = pset []
  where
    pset :: [a] -> [a] -> [[a]]
    pset result [] = [reverse result]
    pset result (x : xs) = pset result xs ++ pset (x : result) xs

neutral :: PowerSeries
neutral = PowerSeries $ 1 : repeat 0

atom :: PowerSeries
atom = PowerSeries $ 0 : 1 : repeat 0

zpow :: Int -> PowerSeries
zpow n = PowerSeries $ replicate n 0 ++ 1 : repeat 0

(.*) :: Integer -> PowerSeries -> PowerSeries
infixl 7 .*
c .* (PowerSeries bs) = PowerSeries $ c `mul'` bs

mul' c [] = []
mul' c (a : as) = c * a : c `mul'` as

mul :: [Integer] -> [Integer] -> [Integer]
mul (a : as') bs@(b : bs') = a*b : ((a `mul'` bs') `add'` (as' `mul` bs))

add' :: [Integer] -> [Integer] -> [Integer]
add' = zipWith (+)

geometric :: PowerSeries
geometric = PowerSeries $ repeat 1

compose :: PowerSeries -> PowerSeries -> PowerSeries
compose (PowerSeries as) (PowerSeries bs) = PowerSeries $ compose' as bs where
    compose' :: [Integer] -> [Integer] -> [Integer]
    compose' (a : as) (0 : bs) = a : bs `mul` compose' as (0 : bs)

instance Num PowerSeries where
    (PowerSeries as) + (PowerSeries bs) = PowerSeries $ add' as bs
    (PowerSeries as) * (PowerSeries bs) = PowerSeries $ as `mul` bs
    abs (PowerSeries as) = PowerSeries $ abs' as
      where
        abs' = fmap abs
    signum (PowerSeries as) = PowerSeries $ signum' as
      where
        signum' = fmap signum
    fromInteger a = PowerSeries [a]
    negate (PowerSeries as) = PowerSeries $ negate' as
      where
        negate' = fmap negate
