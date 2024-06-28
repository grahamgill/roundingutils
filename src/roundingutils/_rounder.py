from collections import defaultdict
import decimal
from decimal import Decimal
from enum import Enum
from math import floor, ceil, trunc, copysign, modf, fmod, fabs, isfinite
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
    >>> _sign(float('-NaN'))
    -1

    Complex valued inputs raise an error.
    >>> _sign(1+1j)
    Traceback (most recent call last):
      ...
    TypeError: '>' not supported between instances of 'complex' and 'int'

    """
    return 0 if x == 0 else 1 if x > 0 else -1 if x < 0 else int(copysign(1, x))


def _awayfromzero(x: Real | Decimal) -> Integral:
    """Rounding to integer away from zero, toward +infinity if input is positive, and toward -infinity if input is negative.
    
    >>> _awayfromzero(1.0000000001)
    2
    >>> _awayfromzero(Decimal('-1.0000000000000000000000000000000000000000000000000000000000001'))
    -2
    >>> _awayfromzero(Fraction(3,1))
    3
    >>> _awayfromzero(0.0)
    0
    >>> _awayfromzero(float('NaN'))
    Traceback (most recent call last):
      ...
    ValueError: cannot convert float NaN to integer

    """
    return ceil(x) if x >= 0 else floor(x)


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

    >>> _roundhalftozero(float('-Inf'))
    Traceback (most recent call last):
      ...
    OverflowError: cannot convert float infinity to integer
  
    """
    return _sign(x) * ceil((2 * abs(x) - 1) / 2)


def _roundhalffromzero(x: Real | Decimal) -> Integral:
    return _sign(x) * floor((2 * abs(x) + 1) / 2)


def _roundhalfdown(x: Real | Decimal) -> Integral:
    return ceil((2 * x - 1) / 2)


def _roundhalfup(x: Real | Decimal) -> Integral:
    return floor((2 * x + 1) / 2)


def _roundhalfodd(x: Real | Decimal) -> Integral:
    sgn_x = _sign(x)
    return round(x + sgn_x) - sgn_x


def _round05fromzero(x: Real | Decimal) -> Integral:
    tozero_x = trunc(x)
    return tozero_x if tozero_x % 5 else _awayfromzero(x)


def _ceil_float(x: float) -> float:
    fpart, ipart = modf(x)
    return ipart if fpart <= 0.0 else ipart + 1.0


def _floor_float(x: float) -> float:
    fpart, ipart = modf(x)
    return ipart if fpart >= 0.0 else ipart - 1.0


def _trunc_float(x: float) -> float:
    _, ipart = modf(x)
    return ipart


def _awayfromzero_float(x: float) -> float:
    fpart, ipart = modf(x)
    return ipart if fpart == 0.0 else ipart + copysign(1.0, fpart)


def _roundhalfeven_float(x: float) -> float:
    return round(x, 0)


def _roundhalfodd_float(x: float) -> float:
    sgn_x = copysign(1.0, x)
    return copysign(round(x + sgn_x, 0) - sgn_x, x)


def _roundhalftozero_float(x: float) -> float:
    return copysign(1.0, x) * _ceil_float((2.0 * fabs(x) - 1.0) / 2.0)


def _roundhalffromzero_float(x: float) -> float:
    return copysign(1.0, x) * _floor_float((2.0 * fabs(x) + 1.0) / 2.0)


def _roundhalfdown_float(x: float) -> float:
    return _ceil_float((2.0 * x - 1.0) / 2.0)


def _roundhalfup_float(x: float) -> float:
    return _floor_float((2.0 * x + 1.0) / 2.0)


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
