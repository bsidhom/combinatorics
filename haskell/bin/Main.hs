module Main where

import Data.Function ((&))

import qualified PowerSeries as P
import PowerSeries ((.*))
import qualified PowerSeries as P

main :: IO ()
main = do
    mapM_ print xs
  where
    xs = take 1001 $ zip [0..] coefficients
    coefficients = P.toList $ coin 1 * coin 5 * coin 10 * coin 25
    coin n = P.compose P.geometric (P.zpow n)
