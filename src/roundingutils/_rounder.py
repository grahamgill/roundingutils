from collections import defaultdict
import decimal
from decimal import Decimal
from enum import Enum
from math import floor, ceil, trunc, copysign, modf, fmod, fabs, isfinite, isnan
from numbers import Integral, Real, Number, Complex, Rational
from typing import Callable, Dict

# all we need for `import *`
__all__ = ['Rounder', 'RoundingMode']


class RoundingMode(Enum):
    """Collection of rounding modes.

    See [Rounding on Wikipedia](https://en.wikipedia.org/wiki/Rounding). The method `ROUND05FROMZERO` is documented on that page
    as [Rounding to Prepare for Shorter Precision (RPSP)](https://en.wikipedia.org/wiki/Rounding#Rounding_to_prepare_for_shorter_precision).

    """
    ROUNDDOWN = 'Round toward -infinity'
    ROUNDUP = 'Round toward +infinity'
    ROUNDTOZERO = 'Round toward zero'
    ROUNDFROMZERO = 'Round away from zero, toward +infinity if positive and toward -infinity if negative'
    ROUNDHALFEVEN = 'Round to nearest decimal with ties going to the even digit'
    ROUNDHALFODD = 'Round to nearest decimal with ties going to the odd digit'
    ROUNDHALFDOWN = 'Round to nearest decimal with ties going toward -infinity'
    ROUNDHALFUP = 'Round to nearest decimal with ties going toward +infinity'
    ROUNDHALFTOZERO = 'Round to nearest decimal with ties going toward zero'
    ROUNDHALFFROMZERO = 'Round to nearest decimal with ties going toward +infinity if positive and toward -infinity if negative'
    ROUND05FROMZERO = 'Round toward zero, unless the rounded number ends in 0 or 5, in which case round toward +infinity if positive and toward -infinity if negative'


def _sign(x: Real | Decimal) -> Integral:
    """Signum function.

    Returns 0 if input is numerically equal to zero, 1 if input is positive, -1 if input is negative.
    >>> _sign(Fraction(5,2))
    1
    >>> _sign(Decimal('-3.2'))
    -1
    >>> _sign(-0.0)
    0

    Takes signed `NaN` and signed `Inf` also and returns the sign.
    >>> _sign(float('Inf'))
    1
    >>> _sign(float('-Inf'))
    -1
    >>> _sign(float('NaN'))
    1
    >>> _sign(float('-NaN'))
    -1
    >>> _sign(Decimal('Inf'))
    1
    >>> _sign(Decimal('-Inf'))
    -1
    >>> _sign(Decimal('NaN'))
    1
    >>> _sign(Decimal('-NaN'))
    -1

    Complex valued inputs raise an error.
    >>> _sign(1+1j)
    Traceback (most recent call last):
      ...
    TypeError: must be real number, not complex

    """
    # in general this is faster than `return 0 if x == 0 else int(copysign(1.0, x))` but 
    # this doesn't work in the default context of `Decimal('NaN')` which traps comparisons `>`, `<`
    # as invalid operations:
    # return 0 if x == 0 else 1 if x > 0 else -1 if x < 0 else int(copysign(1.0, x))

    # this is a compromise between the two
    return int(copysign(1.0, x)) if isnan(x) else 1 if x > 0 else -1 if x < 0 else 0


def _awayfromzero(x: Real | Decimal) -> Integral:
    """Rounding to integer away from zero, toward +infinity if input is positive, and toward -infinity if input is negative.
    
    >>> _awayfromzero(1.0000000001)
    2
    >>> _awayfromzero(Fraction(3,1))
    3
    >>> _awayfromzero(0.0)
    0
    >>> _awayfromzero(Decimal('3.2'))
    4
    >>> _awayfromzero(Decimal('-4.000001'))
    -5

    Beware `decimal` contexts:
    >>> with decimal.localcontext() as ctx:
    ...     ctx.prec = 100
    ...     _awayfromzero(Decimal('-1.0000000000000000000000000000000000000000000000000000000000001'))
    -2
    >>> _awayfromzero(Decimal('-1.0000000000000000000000000000000000000000000000000000000000001'))
    -1

    Inf and NaN exceptions. These are also subject to `decimal` context.
    >>> _awayfromzero(float('Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _awayfromzero(float('NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _awayfromzero(Decimal('Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _awayfromzero(Decimal('NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    # `Decimal('NaN')` in default context doesn't allow comparison `>=`, which means that using
    # `ceil(x) if x >= 0 else floor(x)` needs to be protected with
    # e.g. `ceil(x) if isnan(x) or x >= 0 else floor(x)`
    return _sign(x) * ceil(abs(x))


def _roundhalftozero(x: Real | Decimal) -> Integral:
    """Round to nearest integer, with exactly half going toward zero.
    
    >>> _roundhalftozero(Fraction(3,2))
    1
    >>> _roundhalftozero(Decimal('-1.5'))
    -1
    >>> _roundhalftozero(0.6)
    1
    >>> _roundhalftozero(-0.4)
    0
    >>> _roundhalftozero(0.5)
    0
    >>> _roundhalftozero(0.25)
    0
    >>> _roundhalftozero(-0.25)
    0
    >>> _roundhalftozero(-0.5)
    0

    >>> _roundhalftozero(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _roundhalftozero(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _roundhalftozero(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _roundhalftozero(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    return _sign(x) * ceil((2 * abs(x) - 1) / 2)


def _roundhalffromzero(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward +infinity if `x > 0` and going toward -infinity if `x < 0`.
    
    >>> _roundhalffromzero(Fraction(3,2))
    2
    >>> _roundhalffromzero(Decimal('-1.5'))
    -2
    >>> _roundhalffromzero(0.6)
    1
    >>> _roundhalffromzero(-0.4)
    0
    >>> _roundhalffromzero(0.5)
    1
    >>> _roundhalffromzero(0.25)
    0
    >>> _roundhalffromzero(-0.25)
    0
    >>> _roundhalffromzero(-0.5)
    -1

    >>> _roundhalffromzero(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _roundhalffromzero(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _roundhalffromzero(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _roundhalffromzero(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    return _sign(x) * floor((2 * abs(x) + 1) / 2)


def _roundhalfdown(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward -infinity.
    
    >>> _roundhalfdown(Fraction(3,2))
    1
    >>> _roundhalfdown(Decimal('-1.5'))
    -2
    >>> _roundhalfdown(0.6)
    1
    >>> _roundhalfdown(-0.4)
    0
    >>> _roundhalfdown(0.5)
    0
    >>> _roundhalfdown(0.25)
    0
    >>> _roundhalfdown(-0.25)
    0
    >>> _roundhalfdown(-0.5)
    -1

    >>> _roundhalfdown(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _roundhalfdown(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _roundhalfdown(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _roundhalfdown(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    return ceil((2 * x - 1) / 2)


def _roundhalfup(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward +infinity.
    
    >>> _roundhalfup(Fraction(3,2))
    2
    >>> _roundhalfup(Decimal('-1.5'))
    -1
    >>> _roundhalfup(0.6)
    1
    >>> _roundhalfup(-0.4)
    0
    >>> _roundhalfup(0.5)
    1
    >>> _roundhalfup(0.25)
    0
    >>> _roundhalfup(-0.25)
    0
    >>> _roundhalfup(-0.5)
    0

    >>> _roundhalfup(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _roundhalfup(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _roundhalfup(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _roundhalfup(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    return floor((2 * x + 1) / 2)


def _roundhalfodd(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward the nearest odd integer.
    
    >>> _roundhalfodd(Fraction(3,2))
    1
    >>> _roundhalfodd(Decimal('-1.5'))
    -1
    >>> _roundhalfodd(0.6)
    1
    >>> _roundhalfodd(-0.4)
    0
    >>> _roundhalfodd(0.0)
    0
    >>> _roundhalfodd(-0.0)
    0

    >>> _roundhalfodd(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _roundhalfodd(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _roundhalfodd(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _roundhalfodd(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    sgn_x = _sign(x)
    return round(x + sgn_x) - sgn_x


def _round05fromzero(x: Real | Decimal) -> Integral:
    """Round `x` toward zero, unless the integer produced ends in zero or five (i.e. is a multiple of 5), in which case round away from zero instead.
    
    >>> _round05fromzero(5.0000000000001)
    6
    >>> _round05fromzero(4.9999999999999)
    4
    >>> _round05fromzero(5.0)
    5
    >>> _round05fromzero(Decimal(-9.9999999999999))
    -9
    >>> _round05fromzero(Decimal(-10.0000000000001))
    -11
    >>> _round05fromzero(Fraction(-10,1))
    -10

    >>> _round05fromzero(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
    >>> _round05fromzero(float('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer
    >>> _round05fromzero(Decimal('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert Infinity to integer
    >>> _round05fromzero(Decimal('-NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert NaN to integer
    """
    tozero_x = trunc(x)
    return tozero_x if tozero_x % 5 else _awayfromzero(x)


def _ceil_float(x: float) -> float:
    """As `ceil` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _ceil_float(-3.2)
    -3.0
    >>> _ceil_float(5.6)
    6.0
    >>> _ceil_float(-1.0)
    -1.0
    >>> _ceil_float(1.0)
    1.0
    >>> _ceil_float(-0.5) == -0.0 and copysign(1.0, _ceil_float(-0.5)) == -1.0
    True
    >>> _ceil_float(0.0) == 0.0 and copysign(1.0, _ceil_float(0.0)) == 1.0
    True
    >>> _ceil_float(-0.0) == -0.0 and copysign(1.0, _ceil_float(-0.0)) == -1.0
    True
    >>> _ceil_float(float('Inf')) == float('Inf') and copysign(1.0, _ceil_float(float('Inf'))) == 1.0
    True
    >>> _ceil_float(float('-Inf')) == float('-Inf') and copysign(1.0, _ceil_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_ceil_float(float('NaN'))) and copysign(1.0, _ceil_float(float('NaN'))) == 1.0
    True
    >>> isnan(_ceil_float(float('-NaN'))) and copysign(1.0, _ceil_float(float('-NaN'))) == -1.0
    True
    """
    fpart, ipart = modf(x)
    return ipart if copysign(1.0, fpart) == -1.0 or fpart == 0.0 else ipart + 1.0


def _floor_float(x: float) -> float:
    """As `floor` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _floor_float(-3.2)
    -4.0
    >>> _floor_float(5.6)
    5.0
    >>> _floor_float(-1.0)
    -1.0
    >>> _floor_float(1.0)
    1.0
    >>> _floor_float(0.5) == 0.0 and copysign(1.0, _floor_float(0.5)) == 1.0
    True
    >>> _floor_float(0.0) == 0.0 and copysign(1.0, _floor_float(0.0)) == 1.0
    True
    >>> _floor_float(-0.0) == -0.0 and copysign(1.0, _floor_float(-0.0)) == -1.0
    True
    >>> _floor_float(float('Inf')) == float('Inf') and copysign(1.0, _floor_float(float('Inf'))) == 1.0
    True
    >>> _floor_float(float('-Inf')) == float('-Inf') and copysign(1.0, _floor_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_floor_float(float('NaN'))) and copysign(1.0, _floor_float(float('NaN'))) == 1.0
    True
    >>> isnan(_floor_float(float('-NaN'))) and copysign(1.0, _floor_float(float('-NaN'))) == -1.0
    True
    """
    fpart, ipart = modf(x)
    return ipart if copysign(1.0, fpart) == 1.0 or fpart == 0.0 else ipart - 1.0


def _trunc_float(x: float) -> float:
    """As `trunc` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _trunc_float(-3.2)
    -3.0
    >>> _trunc_float(5.6)
    5.0
    >>> _trunc_float(-1.0)
    -1.0
    >>> _trunc_float(1.0)
    1.0
    >>> _trunc_float(-0.5) == -0.0 and copysign(1.0, _trunc_float(-0.5)) == -1.0
    True
    >>> _trunc_float(0.5) == 0.0 and copysign(1.0, _trunc_float(0.5)) == 1.0
    True
    >>> _trunc_float(0.0) == 0.0 and copysign(1.0, _trunc_float(0.0)) == 1.0
    True
    >>> _trunc_float(-0.0) == -0.0 and copysign(1.0, _trunc_float(-0.0)) == -1.0
    True
    >>> _trunc_float(float('Inf')) == float('Inf') and copysign(1.0, _trunc_float(float('Inf'))) == 1.0
    True
    >>> _trunc_float(float('-Inf')) == float('-Inf') and copysign(1.0, _trunc_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_trunc_float(float('NaN'))) and copysign(1.0, _trunc_float(float('NaN'))) == 1.0
    True
    >>> isnan(_trunc_float(float('-NaN'))) and copysign(1.0, _trunc_float(float('-NaN'))) == -1.0
    True
    """
    _, ipart = modf(x)
    return ipart


def _awayfromzero_float(x: float) -> float:
    """As `_awayfromzero` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _awayfromzero_float(-3.2)
    -4.0
    >>> _awayfromzero_float(5.6)
    6.0
    >>> _awayfromzero_float(-1.0)
    -1.0
    >>> _awayfromzero_float(1.0)
    1.0
    >>> _awayfromzero_float(0.0) == 0.0 and copysign(1.0, _awayfromzero_float(0.0)) == 1.0
    True
    >>> _awayfromzero_float(-0.0) == -0.0 and copysign(1.0, _awayfromzero_float(-0.0)) == -1.0
    True
    >>> _awayfromzero_float(float('Inf')) == float('Inf') and copysign(1.0, _awayfromzero_float(float('Inf'))) == 1.0
    True
    >>> _awayfromzero_float(float('-Inf')) == float('-Inf') and copysign(1.0, _awayfromzero_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_awayfromzero_float(float('NaN'))) and copysign(1.0, _awayfromzero_float(float('NaN'))) == 1.0
    True
    >>> isnan(_awayfromzero_float(float('-NaN'))) and copysign(1.0, _awayfromzero_float(float('-NaN'))) == -1.0
    True
    """
    fpart, ipart = modf(x)
    return ipart if fpart == 0.0 else ipart + copysign(1.0, fpart)


def _roundhalfeven_float(x: float) -> float:
    """A synonym for `round(x, 0)`, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalfeven_float(-3.2)
    -3.0
    >>> _roundhalfeven_float(5.6)
    6.0
    >>> _roundhalfeven_float(-3.5)
    -4.0
    >>> _roundhalfeven_float(5.5)
    6.0
    >>> _roundhalfeven_float(-4.5)
    -4.0
    >>> _roundhalfeven_float(6.5)
    6.0
    >>> _roundhalfeven_float(-1.0)
    -1.0
    >>> _roundhalfeven_float(1.0)
    1.0
    >>> _roundhalfeven_float(0.0) == 0.0 and copysign(1.0, _roundhalfeven_float(0.0)) == 1.0
    True
    >>> _roundhalfeven_float(-0.0) == -0.0 and copysign(1.0, _roundhalfeven_float(-0.0)) == -1.0
    True
    >>> _roundhalfeven_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalfeven_float(float('Inf'))) == 1.0
    True
    >>> _roundhalfeven_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalfeven_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalfeven_float(float('NaN'))) and copysign(1.0, _roundhalfeven_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalfeven_float(float('-NaN'))) and copysign(1.0, _roundhalfeven_float(float('-NaN'))) == -1.0
    True
    """
    return round(x, 0)


def _roundhalfodd_float(x: float) -> float:
    """Like `round(x, 0)`, but rounds half to the nearest odd integer instead of even integer, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalfodd_float(-3.2)
    -3.0
    >>> _roundhalfodd_float(5.6)
    6.0
    >>> _roundhalfodd_float(-3.5)
    -3.0
    >>> _roundhalfodd_float(5.5)
    5.0
    >>> _roundhalfodd_float(-4.5)
    -5.0
    >>> _roundhalfodd_float(6.5)
    7.0
    >>> _roundhalfodd_float(-1.0)
    -1.0
    >>> _roundhalfodd_float(1.0)
    1.0
    >>> _roundhalfodd_float(0.0) == 0.0 and copysign(1.0, _roundhalfodd_float(0.0)) == 1.0
    True
    >>> _roundhalfodd_float(-0.0) == -0.0 and copysign(1.0, _roundhalfodd_float(-0.0)) == -1.0
    True
    >>> _roundhalfodd_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalfodd_float(float('Inf'))) == 1.0
    True
    >>> _roundhalfodd_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalfodd_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalfodd_float(float('NaN'))) and copysign(1.0, _roundhalfodd_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalfodd_float(float('-NaN'))) and copysign(1.0, _roundhalfodd_float(float('-NaN'))) == -1.0
    True
    """
    sgn_x = copysign(1.0, x)
    return copysign(round(x + sgn_x, 0) - sgn_x, x)


def _roundhalftozero_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half to the nearest integer nearest zero, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalftozero_float(-3.2)
    -3.0
    >>> _roundhalftozero_float(5.6)
    6.0
    >>> _roundhalftozero_float(-3.5)
    -3.0
    >>> _roundhalftozero_float(5.5)
    5.0
    >>> _roundhalftozero_float(-1.0)
    -1.0
    >>> _roundhalftozero_float(1.0)
    1.0
    >>> _roundhalftozero_float(0.5) == 0.0 and copysign(1.0, _roundhalftozero_float(0.5)) == 1.0
    True
    >>> _roundhalftozero_float(0.25) == 0.0 and copysign(1.0, _roundhalftozero_float(0.25)) == 1.0
    True
    >>> _roundhalftozero_float(-0.25) == -0.0 and copysign(1.0, _roundhalftozero_float(-0.25)) == -1.0
    True
    >>> _roundhalftozero_float(-0.5) == -0.0 and copysign(1.0, _roundhalftozero_float(-0.5)) == -1.0
    True
    >>> _roundhalftozero_float(0.0) == 0.0 and copysign(1.0, _roundhalftozero_float(0.0)) == 1.0
    True
    >>> _roundhalftozero_float(-0.0) == -0.0 and copysign(1.0, _roundhalftozero_float(-0.0)) == -1.0
    True
    >>> _roundhalftozero_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalftozero_float(float('Inf'))) == 1.0
    True
    >>> _roundhalftozero_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalftozero_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalftozero_float(float('NaN'))) and copysign(1.0, _roundhalftozero_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalftozero_float(float('-NaN'))) and copysign(1.0, _roundhalftozero_float(float('-NaN'))) == -1.0
    True
    """
    return copysign(_ceil_float((2.0 * fabs(x) - 1.0) / 2.0), x)


def _roundhalffromzero_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half to the nearest integer farthest from zero, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalffromzero_float(-3.2)
    -3.0
    >>> _roundhalffromzero_float(5.6)
    6.0
    >>> _roundhalffromzero_float(-3.5)
    -4.0
    >>> _roundhalffromzero_float(5.5)
    6.0
    >>> _roundhalffromzero_float(-1.0)
    -1.0
    >>> _roundhalffromzero_float(1.0)
    1.0
    >>> _roundhalffromzero_float(0.5)
    1.0
    >>> _roundhalffromzero_float(0.25) == 0.0 and copysign(1.0, _roundhalffromzero_float(0.25)) == 1.0
    True
    >>> _roundhalffromzero_float(-0.25) == -0.0 and copysign(1.0, _roundhalffromzero_float(-0.25)) == -1.0
    True
    >>> _roundhalffromzero_float(-0.5)
    -1.0
    >>> _roundhalffromzero_float(0.0) == 0.0 and copysign(1.0, _roundhalffromzero_float(0.0)) == 1.0
    True
    >>> _roundhalffromzero_float(-0.0) == -0.0 and copysign(1.0, _roundhalffromzero_float(-0.0)) == -1.0
    True
    >>> _roundhalffromzero_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalffromzero_float(float('Inf'))) == 1.0
    True
    >>> _roundhalffromzero_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalffromzero_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalffromzero_float(float('NaN'))) and copysign(1.0, _roundhalffromzero_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalffromzero_float(float('-NaN'))) and copysign(1.0, _roundhalffromzero_float(float('-NaN'))) == -1.0
    True
    """
    return copysign(_floor_float((2.0 * fabs(x) + 1.0) / 2.0), x)


def _roundhalfdown_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half toward -infinity, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalfdown_float(-3.2)
    -3.0
    >>> _roundhalfdown_float(5.6)
    6.0
    >>> _roundhalfdown_float(-3.5)
    -4.0
    >>> _roundhalfdown_float(5.5)
    5.0
    >>> _roundhalfdown_float(-1.0)
    -1.0
    >>> _roundhalfdown_float(1.0)
    1.0
    >>> _roundhalfdown_float(0.5) == 0.0 and copysign(1.0, _roundhalfdown_float(0.5)) == 1.0
    True
    >>> _roundhalfdown_float(0.25) == 0.0 and copysign(1.0, _roundhalfdown_float(0.25)) == 1.0
    True
    >>> _roundhalfdown_float(-0.25) == -0.0 and copysign(1.0, _roundhalfdown_float(-0.25)) == -1.0
    True
    >>> _roundhalfdown_float(-0.5)
    -1.0
    >>> _roundhalfdown_float(0.0) == 0.0 and copysign(1.0, _roundhalfdown_float(0.0)) == 1.0
    True
    >>> _roundhalfdown_float(-0.0) == -0.0 and copysign(1.0, _roundhalfdown_float(-0.0)) == -1.0
    True
    >>> _roundhalfdown_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalfdown_float(float('Inf'))) == 1.0
    True
    >>> _roundhalfdown_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalfdown_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalfdown_float(float('NaN'))) and copysign(1.0, _roundhalfdown_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalfdown_float(float('-NaN'))) and copysign(1.0, _roundhalfdown_float(float('-NaN'))) == -1.0
    True
    """
    return copysign(_ceil_float((2.0 * x - 1.0) / 2.0), x)


def _roundhalfup_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half toward +infinity, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    >>> _roundhalfup_float(-3.2)
    -3.0
    >>> _roundhalfup_float(5.6)
    6.0
    >>> _roundhalfup_float(-3.5)
    -3.0
    >>> _roundhalfup_float(5.5)
    6.0
    >>> _roundhalfup_float(-1.0)
    -1.0
    >>> _roundhalfup_float(1.0)
    1.0
    >>> _roundhalfup_float(0.5)
    1.0
    >>> _roundhalfup_float(0.25) == 0.0 and copysign(1.0, _roundhalfup_float(0.25)) == 1.0
    True
    >>> _roundhalfup_float(-0.25) == -0.0 and copysign(1.0, _roundhalfup_float(-0.25)) == -1.0
    True
    >>> _roundhalfup_float(-0.5) == -0.0 and copysign(1.0, _roundhalfup_float(-0.5)) == -1.0
    True
    >>> _roundhalfup_float(0.0) == 0.0 and copysign(1.0, _roundhalfup_float(0.0)) == 1.0
    True
    >>> _roundhalfup_float(-0.0) == -0.0 and copysign(1.0, _roundhalfup_float(-0.0)) == -1.0
    True
    >>> _roundhalfup_float(float('Inf')) == float('Inf') and copysign(1.0, _roundhalfup_float(float('Inf'))) == 1.0
    True
    >>> _roundhalfup_float(float('-Inf')) == float('-Inf') and copysign(1.0, _roundhalfup_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_roundhalfup_float(float('NaN'))) and copysign(1.0, _roundhalfup_float(float('NaN'))) == 1.0
    True
    >>> isnan(_roundhalfup_float(float('-NaN'))) and copysign(1.0, _roundhalfup_float(float('-NaN'))) == -1.0
    True
    """
    return copysign(_floor_float((2.0 * x + 1.0) / 2.0), x)


def _round05fromzero_float(x: float) -> float:
    fpart, ipart = modf(x)
    return ipart if fpart == 0.0 or fmod(ipart, 5.0) else ipart + copysign(1.0, fpart)


def _roundhalfodd_decimal(x: Decimal) -> Decimal:
    sgn_x = Decimal(1).copy_sign(x)
    return ((x + sgn_x).to_integral_value(decimal.ROUND_HALF_EVEN) - sgn_x).copy_sign(x)


def _roundhalfupdown_decimal(x: Decimal, direction: Decimal | int) -> Decimal:
    sgn_x = Decimal(1).copy_sign(x) * Decimal(1).copy_sign(direction)
    return x.to_integral_value(decimal.ROUND_HALF_DOWN if sgn_x < 0 else decimal.ROUND_HALF_UP)


def _apply_to_real_part(f: Callable[[Number], Number]) -> Callable[[Number], Number]:
    return lambda x: f(x.real)


def _map_over_dict_vals(f: Callable, d: Dict) -> Dict:
    return {k: f(v) for k, v in d.items()}


def _raise_notimplemented():
    raise NotImplementedError


class Rounder():
    _real_to_integral = {
        RoundingMode.ROUNDDOWN: floor,
        RoundingMode.ROUNDUP: ceil,
        RoundingMode.ROUNDTOZERO: trunc,
        RoundingMode.ROUNDFROMZERO: _awayfromzero,
        RoundingMode.ROUNDHALFEVEN: round,
        RoundingMode.ROUNDHALFODD: _roundhalfodd,
        RoundingMode.ROUNDHALFDOWN: _roundhalfdown,
        RoundingMode.ROUNDHALFUP: _roundhalfup,
        RoundingMode.ROUNDHALFTOZERO: _roundhalftozero,
        RoundingMode.ROUNDHALFFROMZERO: _roundhalffromzero,
        RoundingMode.ROUND05FROMZERO: _round05fromzero
    }

    _float_to_float = {
        RoundingMode.ROUNDDOWN: _floor_float,
        RoundingMode.ROUNDUP: _ceil_float,
        RoundingMode.ROUNDTOZERO: _trunc_float,
        RoundingMode.ROUNDFROMZERO: _awayfromzero_float,
        RoundingMode.ROUNDHALFEVEN: _roundhalfeven_float,
        RoundingMode.ROUNDHALFODD: _roundhalfodd_float,
        RoundingMode.ROUNDHALFDOWN: _roundhalfdown_float,
        RoundingMode.ROUNDHALFUP: _roundhalfup_float,
        RoundingMode.ROUNDHALFTOZERO: _roundhalftozero_float,
        RoundingMode.ROUNDHALFFROMZERO: _roundhalffromzero_float,
        RoundingMode.ROUND05FROMZERO: _round05fromzero_float
    }

    _decimal_to_decimal = {
        RoundingMode.ROUNDDOWN: lambda x: x.to_integral_value(decimal.ROUND_FLOOR),
        RoundingMode.ROUNDUP: lambda x: x.to_integral_value(decimal.ROUND_CEILING),
        RoundingMode.ROUNDTOZERO: lambda x: x.to_integral_value(decimal.ROUND_DOWN),
        RoundingMode.ROUNDFROMZERO: lambda x: x.to_integral_value(decimal.ROUND_UP),
        RoundingMode.ROUNDHALFEVEN: lambda x: x.to_integral_value(decimal.ROUND_HALF_EVEN),
        RoundingMode.ROUNDHALFODD: _roundhalfodd_decimal,
        RoundingMode.ROUNDHALFDOWN: lambda x: _roundhalfupdown_decimal(x, Decimal(-1)),
        RoundingMode.ROUNDHALFUP: lambda x: _roundhalfupdown_decimal(x, Decimal(1)),
        RoundingMode.ROUNDHALFTOZERO: lambda x: x.to_integral_value(decimal.ROUND_HALF_DOWN),
        RoundingMode.ROUNDHALFFROMZERO: lambda x: x.to_integral_value(decimal.ROUND_HALF_UP),
        RoundingMode.ROUND05FROMZERO: lambda x: x.to_integral_value(
            decimal.ROUND_05UP)
    }

    def __init__(self, number_type: Number | type[Number], default_mode: RoundingMode = RoundingMode.ROUNDHALFEVEN):
        if isinstance(number_type, Number):
            number_type = type(number_type)

        self._number_type = number_type
        self._isinteger = Rounder._isinteger_selector(number_type)
        self._roundingfuncs = [defaultdict(
            _raise_notimplemented), defaultdict(_raise_notimplemented)]

        if issubclass(number_type, Real | Decimal):
            self._roundingfuncs[1] |= Rounder._real_to_integral

        elif issubclass(number_type, Complex):
            self._roundingfuncs[1] |= _map_over_dict_vals(
                _apply_to_real_part, Rounder._real_to_integral)

        if issubclass(number_type, float):
            self._roundingfuncs[0] |= Rounder._float_to_float if number_type == float else _map_over_dict_vals(
                self._to_number_type, Rounder._float_to_float)

        elif issubclass(number_type, Decimal):
            self._roundingfuncs[0] |= Rounder._decimal_to_decimal if number_type == Decimal else _map_over_dict_vals(
                self._to_number_type, Rounder._decimal_to_decimal)

        elif issubclass(number_type, Real):
            self._roundingfuncs[0] |= _map_over_dict_vals(
                self._to_number_type, Rounder._real_to_integral)

        elif issubclass(number_type, complex):
            self._roundingfuncs[0] |= _map_over_dict_vals(
                lambda f: self._to_number_type(_apply_to_real_part(f)), Rounder._float_to_float)

        elif issubclass(number_type, Complex):
            self._roundingfuncs[0] |= _map_over_dict_vals(lambda f: self._to_number_type(
                _apply_to_real_part(f)), Rounder._real_to_integral)

        self.default_mode = default_mode

    def __call__(self, x: Number, mode: RoundingMode = None, to_int: bool = False) -> Number:
        return self._roundingfuncs[to_int][mode](x)

    def roundunits(self, x: Number, unitsize: Number, mode: RoundingMode = None, to_int: bool = False, free_type: bool = True) -> Number:
        r = x if unitsize == 0 else self._roundingfuncs[to_int][mode](
            x / unitsize) * unitsize

        return r if free_type else (type(unitsize) if to_int else self._number_type)(r)

    def round(self, x: Number, ndigits: int = None, mode: RoundingMode = None) -> Number:
        return self(x, mode, True) if ndigits is None else self.roundunits(x, self._number_type(10)**(-ndigits), mode, False, False)

    def countunits(self, x: Number, unitsize: Number, mode: RoundingMode, to_int: bool = True) -> Number:
        return self._roundingfuncs[to_int][mode](x / unitsize)

    def isunitsized(self, x: Number, unitsize: Number) -> bool:
        if unitsize == 0:
            return True

        return self._isinteger(x / unitsize)

    def _to_number_type(self, f: Callable[[Number], Number]) -> Callable[[Number], Number]:
        return lambda x: self._number_type(f(x))

    @property
    def default_mode(self):
        return self._default_mode

    @default_mode.setter
    def default_mode(self, mode: RoundingMode):
        self._default_mode = mode
        self._roundingfuncs[0][None] = self._roundingfuncs[0][mode]
        self._roundingfuncs[1][None] = self._roundingfuncs[1][mode]

    @property
    def number_type(self):
        return self._number_type

    @property
    def roundingfuncs(self):
        return self._roundingfuncs

    def setroundingfuncs(self, d: Dict[RoundingMode, Callable[[Number], Number]], to_int: bool, default=_raise_notimplemented):
        self._roundingfuncs[to_int] = defaultdict(default, d)
        self._roundingfuncs[to_int][None] = self._roundingfuncs[to_int][self.default_mode]

    @property
    def isinteger(self):
        return self._isinteger

    @isinteger.setter
    def isinteger(self, fn: Callable[[Number], bool]):
        self._isinteger = lambda x: True if isinstance(x, Integral) else fn(x)

    @staticmethod
    def _isinteger_selector(t: type[Number]) -> Callable[[Number], bool]:
        if issubclass(t, Integral):
            return lambda _: True

        if issubclass(t, float):
            return lambda x: x.is_integer()

        if issubclass(t, Decimal):
            return lambda x: x.is_finite() and x.as_integer_ratio()[1] == 1

        if issubclass(t, Rational):
            return lambda x: x.denominator == 1 or x.numerator % x.denominator == 0

        if issubclass(t, Real):
            return lambda x: isfinite(x) and round(x, 0) == x

        if issubclass(t, complex):
            return lambda x: x.imag == 0 and x.real.is_integer()

        if issubclass(t, Complex):
            return lambda x: x.imag == 0 and isfinite(x.real) and round(x.real, 0) == x.real

        if issubclass(t, Number):
            raise NotImplementedError

        return lambda _: False


if __name__ == "__main__":
    import doctest
    from fractions import Fraction
    doctest.testmod()
