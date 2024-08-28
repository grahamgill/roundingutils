import abc
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

    #### Examples
    >>> _sign(Fraction(5,2))
    1
    >>> _sign(Decimal('-3.2'))
    -1
    >>> _sign(-0.0)
    0

    Takes signed `NaN` and signed `Inf` also and returns the sign.

    Complex valued inputs raise an error.
    """
    # in general this is faster than `return 0 if x == 0 else int(copysign(1.0, x))` but 
    # this doesn't work in the default context of `Decimal('NaN')` which traps comparisons `>`, `<`
    # as invalid operations:
    # return 0 if x == 0 else 1 if x > 0 else -1 if x < 0 else int(copysign(1.0, x))

    # this is a compromise between the two
    return int(copysign(1.0, x)) if isnan(x) else 1 if x > 0 else -1 if x < 0 else 0


def _awayfromzero(x: Real | Decimal) -> Integral:
    """Rounding to integer away from zero, toward +infinity if input is positive, and toward -infinity if input is negative.
    
    #### Examples
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

    Inf and NaN exceptions are also subject to `decimal` context.
    """
    # `Decimal('NaN')` in default context doesn't allow comparison `>=`, which means that using
    # `ceil(x) if x >= 0 else floor(x)` needs to be protected with
    # e.g. `ceil(x) if isnan(x) or x >= 0 else floor(x)`
    return _sign(x) * ceil(abs(x))


def _roundhalftozero(x: Real | Decimal) -> Integral:
    """Round to nearest integer, with exactly half going toward zero.
    
    #### Examples
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
    """
    return _sign(x) * ceil((2 * abs(x) - 1) / 2)


def _roundhalffromzero(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward +infinity if `x > 0` and going toward -infinity if `x < 0`.
    
    #### Examples
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
    """
    return _sign(x) * floor((2 * abs(x) + 1) / 2)


def _roundhalfdown(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward -infinity.
    
    #### Examples
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
    """
    return ceil((2 * x - 1) / 2)


def _roundhalfup(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward +infinity.
    
    #### Examples
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
    """
    return floor((2 * x + 1) / 2)


def _roundhalfodd(x: Real | Decimal) -> Integral:
    """Round `x` to nearest integer, with exactly half going toward the nearest odd integer.
    
    #### Examples
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
    """
    sgn_x = _sign(x)
    return round(x + sgn_x) - sgn_x


def _round05fromzero(x: Real | Decimal) -> Integral:
    """Round `x` toward zero, unless the integer produced ends in zero or five (i.e. is a multiple of 5), in which case round away from zero instead.
    
    #### Examples
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
    """
    tozero_x = trunc(x)
    return tozero_x if tozero_x % 5 else _awayfromzero(x)


def _ceil_float(x: float) -> float:
    """As `ceil` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    fpart, ipart = modf(x)
    return ipart if copysign(1.0, fpart) == -1.0 or fpart == 0.0 else ipart + 1.0


def _floor_float(x: float) -> float:
    """As `floor` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    fpart, ipart = modf(x)
    return ipart if copysign(1.0, fpart) == 1.0 or fpart == 0.0 else ipart - 1.0


def _trunc_float(x: float) -> float:
    """As `trunc` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    _, ipart = modf(x)
    return ipart


def _awayfromzero_float(x: float) -> float:
    """As `_awayfromzero` but takes and returns `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
    >>> _awayfromzero_float(-3.2)
    -4.0
    >>> _awayfromzero_float(5.6)
    6.0
    >>> _awayfromzero_float(-1.0)
    -1.0
    >>> _awayfromzero_float(1.0)
    1.0
    """
    fpart, ipart = modf(x)
    return ipart if fpart == 0.0 else ipart + copysign(1.0, fpart)


def _roundhalfeven_float(x: float) -> float:
    """A synonym for `round(x, 0)`, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    return round(x, 0)


def _roundhalfodd_float(x: float) -> float:
    """Like `round(x, 0)`, but rounds half to the nearest odd integer instead of even integer, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    sgn_x = copysign(1.0, x)
    return copysign(round(x + sgn_x, 0) - sgn_x, x)


def _roundhalftozero_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half to the nearest integer nearest zero, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    return copysign(_ceil_float((2.0 * fabs(x) - 1.0) / 2.0), x)


def _roundhalffromzero_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half to the nearest integer farthest from zero, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    return copysign(_floor_float((2.0 * fabs(x) + 1.0) / 2.0), x)


def _roundhalfdown_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half toward -infinity, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    return copysign(_ceil_float((2.0 * x - 1.0) / 2.0), x)


def _roundhalfup_float(x: float) -> float:
    """Rounds to nearest integer, and rounds half toward +infinity, taking and returning `float`.
    Float signs, Inf and NaN are all preserved.
    
    #### Examples
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
    """
    return copysign(_floor_float((2.0 * x + 1.0) / 2.0), x)


def _round05fromzero_float(x: float) -> float:
    """Round `x` toward zero, unless the integer produced ends in zero or five (i.e. is a multiple of 5), in which case round away from zero instead,
    taking and returning float. Float signs, Inf and NaN are all preserved.
    
    #### Examples
    >>> _round05fromzero_float(5.0000000000001)
    6.0
    >>> _round05fromzero_float(4.9999999999999)
    4.0
    >>> _round05fromzero_float(5.0)
    5.0
    >>> _round05fromzero_float(-9.9999999999999)
    -9.0
    >>> _round05fromzero_float(-10.0000000000001)
    -11.0
    >>> _round05fromzero_float(-10.0)
    -10.0
    >>> _round05fromzero_float(3.0000000000001)
    3.0
    >>> _round05fromzero_float(3.9999999999999)
    3.0
    >>> _round05fromzero_float(3.0)
    3.0
    >>> _round05fromzero_float(-7.9999999999999)
    -7.0
    >>> _round05fromzero_float(-7.0000000000001)
    -7.0
    >>> _round05fromzero_float(-7.0)
    -7.0
    """
    fpart, ipart = modf(x)
    return ipart if fpart == 0.0 or fmod(ipart, 5.0) else ipart + copysign(1.0, fpart)


def _roundhalfodd_decimal(x: Decimal) -> Decimal:
    """Like `round(x, 0)`, but rounds half to the nearest odd integer instead of even integer, taking and returning `Decimal`.
    Decimal signs, Inf and NaN are all preserved.
    
    #### Examples
    >>> _roundhalfodd_decimal(Decimal('-3.2'))
    Decimal('-3')
    >>> _roundhalfodd_decimal(Decimal('5.6'))
    Decimal('6')
    >>> _roundhalfodd_decimal(Decimal('-3.5'))
    Decimal('-3')
    >>> _roundhalfodd_decimal(Decimal('5.5'))
    Decimal('5')
    >>> _roundhalfodd_decimal(Decimal('-4.5'))
    Decimal('-5')
    >>> _roundhalfodd_decimal(Decimal('6.5'))
    Decimal('7')
    >>> _roundhalfodd_decimal(Decimal('-1.0'))
    Decimal('-1')
    >>> _roundhalfodd_decimal(Decimal('1.0'))
    Decimal('1')
    """
    sgn_x = Decimal(1).copy_sign(x)
    return ((x + sgn_x).to_integral_value(decimal.ROUND_HALF_EVEN) - sgn_x).copy_sign(x)


def _roundhalfupdown_decimal(x: Decimal, direction: Decimal | int) -> Decimal:
    """Rounds to the nearest integer, with half going toward +infinity if the sign of `direction` is positive, and half
    going toward -infinity if the sign of `direction` is negative. Takes and returns `Decimal`.
    Decimal signs, Inf and NaN are all preserved.
    
    #### Examples
    >>> _roundhalfupdown_decimal(Decimal('-3.2'), 1)
    Decimal('-3')
    >>> _roundhalfupdown_decimal(Decimal('5.6'), 1)
    Decimal('6')
    >>> _roundhalfupdown_decimal(Decimal('-3.5'), 1)
    Decimal('-3')
    >>> _roundhalfupdown_decimal(Decimal('5.5'), 1)
    Decimal('6')
    >>> _roundhalfupdown_decimal(Decimal('-1'), 1)
    Decimal('-1')
    >>> _roundhalfupdown_decimal(Decimal('1'), 1)
    Decimal('1')
    >>> _roundhalfupdown_decimal(Decimal('0.5'), 1)
    Decimal('1')
    >>> _roundhalfupdown_decimal(Decimal('0.25'), 1) == Decimal('0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('0.25'), 1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0.25'), 1) == Decimal('-0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-0.25'), 1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0.5'), 1) == Decimal('-0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-0.5'), 1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-3.2'), -1)
    Decimal('-3')
    >>> _roundhalfupdown_decimal(Decimal('5.6'), -1)
    Decimal('6')
    >>> _roundhalfupdown_decimal(Decimal('-3.5'), -1)
    Decimal('-4')
    >>> _roundhalfupdown_decimal(Decimal('5.5'), -1)
    Decimal('5')
    >>> _roundhalfupdown_decimal(Decimal('-1'), -1)
    Decimal('-1')
    >>> _roundhalfupdown_decimal(Decimal('1'), -1)
    Decimal('1')
    >>> _roundhalfupdown_decimal(Decimal('0.5'), -1) == Decimal('0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('0.5'), -1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('0.25'), -1) == Decimal('0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('0.25'), -1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0.25'), -1) == Decimal('-0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-0.25'), -1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0.5'), -1)
    Decimal('-1')
    """
    sgn_x = Decimal(1).copy_sign(x) * Decimal(1).copy_sign(direction)
    return x.to_integral_value(decimal.ROUND_HALF_DOWN if sgn_x < 0 else decimal.ROUND_HALF_UP)


def _apply_to_real_part(f: Callable[[Real], Number]) -> Callable[[Complex], Number]:
    """Convert `Callable` `f` from a function on `Real` numbers to a function on `Complex` numbers by applying it to the real part of its
    input.
    
    #### Examples
    >>> _sign(3.2 + 1j)
    Traceback (most recent call last):
      ...
    TypeError: must be real number, not complex

    >>> _apply_to_real_part(_sign)(3.2 + 1j)
    1

    >>> _roundhalfodd_float(complex(-1.5, float('NaN')))
    Traceback (most recent call last):
      ...
    TypeError: must be real number, not complex

    >>> _apply_to_real_part(_roundhalfodd_float)(complex(-1.5, float('NaN')))
    -1.0
    >>> _apply_to_real_part(_roundhalfodd_float)(2.5)
    3.0
    >>> _apply_to_real_part(_roundhalfodd_decimal)(5)
    Decimal('5')
    """
    return lambda x: f(x.real)


def _map_over_dict_vals(f: Callable, d: Dict) -> Dict:
    """Map `Callable` `f` over the values of dictionary `d`, returning the new dictionary. Keys are unchanged.

    #### Examples
    >>> _map_over_dict_vals(lambda x: x * x, {'a':1, 'b':2, 'c':3})
    {'a': 1, 'b': 4, 'c': 9}
    >>> _map_over_dict_vals(_apply_to_real_part(_sign), {'a':3+2j, 'b':0+5j, 'c':-8-3j, 'd':complex(float('Inf'), 2)})
    {'a': 1, 'b': 0, 'c': -1, 'd': 1}
    """
    return {k: f(v) for k, v in d.items()}


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
    "Map of `RoundingMode`s to functions from `Real` or `Decimal` to `Integral`." 

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
    "Map of `RoundingMode`s to functions from `float` to `float`." 

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
    "Map of `RoundingMode`s to functions from `Decimal` to `Decimal`." 

    def __init__(self, number_type: Number | type[Number], default_mode: RoundingMode = RoundingMode.ROUNDHALFEVEN):
        # allow passing in a Number of the type you want as a convenience
        if not isinstance(number_type, type):
            number_type = type(number_type)

        # set raise_notimplemented, for unimplemented combinations of types and rounding methods
        # non-Number types raise a TypeError, but unsupported Number types just assign to raise_notimplemented
        if issubclass(number_type, Number) and not issubclass(number_type, Complex | Decimal):
            self.raise_notimplemented = lambda x: Rounder._raise_notimplemented(x, msg = f'Number subclass {number_type.__name__} is not implemented in {type(self).__name__}')
        elif not issubclass(number_type, Number):
            raise TypeError(f'{number_type.__name__} is not a subclass of Number')
        else:
            self.raise_notimplemented = Rounder._raise_notimplemented

        # number_type is intended to be read-only
        self._number_type = number_type

        # isinteger can be reassigned but starts with the _isinteger_selector provided function
        self.isinteger = Rounder._isinteger_selector(number_type)

        ## define roundingfuncs as a pair of default dictionaries with raise_notimplemented as default, and then add to them according to number_type
        self._roundingfuncs = [defaultdict(
            lambda: self.raise_notimplemented), defaultdict(lambda: self.raise_notimplemented)]

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
            # if number_type is an instance of ABCMeta then it has no concrete implementation, so we need to skip
            # assigning a rounding method returning the same type and instead leave it as the default value of
            # raise_notimplemented
            if not isinstance(number_type, abc.ABCMeta):
              self._roundingfuncs[0] |= _map_over_dict_vals(
                  self._to_number_type, Rounder._real_to_integral)

        elif issubclass(number_type, complex):
            self._roundingfuncs[0] |= _map_over_dict_vals(
                lambda f: self._to_number_type(_apply_to_real_part(f)), Rounder._float_to_float)

        elif issubclass(number_type, Complex):
            # see the comments for the Real case above, which apply here as well
            if not isinstance(number_type, abc.ABCMeta):
              self._roundingfuncs[0] |= _map_over_dict_vals(lambda f: self._to_number_type(
                  _apply_to_real_part(f)), Rounder._real_to_integral)

        # records the default mode and finishes the definition of roundingfuncs
        self.default_mode = default_mode

    ## settings and properties

    @property
    def number_type(self):
        return self._number_type
    
    @property
    def isinteger(self):
        return self._isinteger
    
    @isinteger.setter
    def isinteger(self, fn: Callable[[Number], bool] | None):
        if fn is None:
            self._isinteger = lambda x: self.raise_notimplemented(x, msg = f'Number subclass {self.number_type.__name__} has no defined method to decide when a number is an integer')
        else:
            self._isinteger = fn

    @property
    def roundingfuncs(self):
        return self._roundingfuncs

    def setroundingfuncs(self, d: Dict[RoundingMode, Callable[[Number], Number]], to_int: bool, default=NotImplemented):
        if default is NotImplemented:
            default = self.raise_notimplemented
        self._roundingfuncs[to_int] = defaultdict(default, d)
        self._roundingfuncs[to_int][None] = self._roundingfuncs[to_int][self.default_mode]
        return self._roundingfuncs

    @property
    def default_mode(self):
        return self._default_mode

    @default_mode.setter
    def default_mode(self, mode: RoundingMode):
        self._default_mode = mode
        self._roundingfuncs[0][None] = self._roundingfuncs[0][mode]
        self._roundingfuncs[1][None] = self._roundingfuncs[1][mode]

    ## operations

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

        return self.isinteger(x / unitsize)
    
    ## internal helpers

    def _to_number_type(self, f: Callable[[Number], Number]) -> Callable[[Number], Number]:
        return lambda x: self._number_type(f(x))

    @staticmethod
    def _isinteger_selector(t: type[Number]) -> Callable[[Number], bool] | None:
        """Returns an "isinteger" type function for the `Number` subclass `t`. `t` is checked to be a subclass of
        the following classes, in order: `Integral`, `float`, `Decimal`, `Rational`, `Real`, `complex`, `Complex`; and
        a function is returned for the first class listed of which `t` is a subclass. Thus if `t` is a subclass of 
        e.g. `Real` like `$\mathbb Q(\sqrt 5)$` (where the rational coefficients are given by `Rational`s) and defines
        its own "isinteger" type method, `Rounder._isinteger_selector(t)` will return the
        isinteger function for `Real` as it does not know about the isinteger method for the class of `t`.
        
        Returns `None` for a `Number` subclass which is not a subclass of `Decimal` or of `Complex`.
        """
        if issubclass(t, Integral):
            return lambda _: True

        if issubclass(t, float):
            return lambda x: x.is_integer()

        if issubclass(t, Decimal):
            return lambda x: x.is_finite() and x.as_integer_ratio()[1] == 1

        # nothing special for `Fraction` that's more specific than general `Rational`
        if issubclass(t, Rational):
            # right clause of the `or` shouldn't be needed but just in case a `Rational` subclass doesn't keep
            # numerator and denominator in lowest terms with positive denominator
            return lambda x: x.denominator == 1 or x.numerator % x.denominator == 0

        if issubclass(t, Real):
            return lambda x: isfinite(x) and round(x, 0) == x

        if issubclass(t, complex):
            return lambda x: x.imag == 0 and x.real.is_integer()

        if issubclass(t, Complex):
            return lambda x: x.imag == 0 and isfinite(x.real) and round(x.real, 0) == x.real

        if issubclass(t, Number):
            return None

        return lambda _: False

    @staticmethod
    def _raise_notimplemented(_ = None, msg = None):
        """Raises the `NotImplementedError` exception. The first argument is ignored. It is a placeholder for a value to be rounded,
        ignored because the rounding method requested is not implemented.

        #### Examples
        >>> Rounder(float)._raise_notimplemented(3.2)
        Traceback (most recent call last):
          ...
        NotImplementedError
        >>> Rounder._raise_notimplemented(5.7, 'not implemented')
        Traceback (most recent call last):
          ...
        NotImplementedError: not implemented
        >>> Rounder._raise_notimplemented(msg = 'not gonna work')
        Traceback (most recent call last):
          ...
        NotImplementedError: not gonna work
        """
        raise NotImplementedError if msg is None else NotImplementedError(msg)


if __name__ == "__main__":
    import doctest
    from fractions import Fraction
    doctest.testmod()
    doctest.testfile('../../tests/additional_doctests.md')
