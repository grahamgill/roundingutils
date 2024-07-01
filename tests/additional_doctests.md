Additional doctests for `../src/roundingutils/_rounder.py` that are not illustrative as examples or are excessively repetitive.   

    >>> from decimal import Decimal
    >>> from math import isnan, copysign
    >>> from _rounder import \
    ...   _sign, _awayfromzero, _roundhalftozero, _roundhalffromzero, _roundhalfdown, _roundhalfup, _roundhalfodd, \
    ...   _round05fromzero, _ceil_float, _floor_float, _trunc_float, _awayfromzero_float, _roundhalfeven_float, _roundhalfodd_float, \
    ...   _roundhalftozero_float, _roundhalffromzero_float, _roundhalfdown_float, _roundhalfup_float, _round05fromzero_float, \
    ...   _roundhalfodd_decimal, _roundhalfupdown_decimal
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
    >>> _sign(1+1j)
    Traceback (most recent call last):
      ...
    TypeError: must be real number, not complex
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
    >>> _round05fromzero_float(0.0) == 0.0 and copysign(1.0, _round05fromzero_float(0.0)) == 1.0
    True
    >>> _round05fromzero_float(-0.0) == -0.0 and copysign(1.0, _round05fromzero_float(-0.0)) == -1.0
    True
    >>> _round05fromzero_float(float('Inf')) == float('Inf') and copysign(1.0, _round05fromzero_float(float('Inf'))) == 1.0
    True
    >>> _round05fromzero_float(float('-Inf')) == float('-Inf') and copysign(1.0, _round05fromzero_float(float('-Inf'))) == -1.0
    True
    >>> isnan(_round05fromzero_float(float('NaN'))) and copysign(1.0, _round05fromzero_float(float('NaN'))) == 1.0
    True
    >>> isnan(_round05fromzero_float(float('-NaN'))) and copysign(1.0, _round05fromzero_float(float('-NaN'))) == -1.0
    True
    >>> _roundhalfodd_decimal(Decimal('0')) == Decimal('0') and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('0'))) == Decimal('1')
    True
    >>> _roundhalfodd_decimal(Decimal('-0')) == Decimal('-0') and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('-0'))) == Decimal('-1')
    True
    >>> _roundhalfodd_decimal(Decimal('Inf')) == Decimal('Inf') and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('Inf'))) == Decimal('1')
    True
    >>> _roundhalfodd_decimal(Decimal('-Inf')) == Decimal('-Inf') and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('-Inf'))) == Decimal('-1')
    True
    >>> isnan(_roundhalfodd_decimal(Decimal('NaN'))) and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('NaN'))) == Decimal('1')
    True
    >>> isnan(_roundhalfodd_decimal(Decimal('-NaN'))) and copysign(Decimal('1'), _roundhalfodd_decimal(Decimal('-NaN'))) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('0'), 1) == Decimal('0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('0'), 1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0'), 1) == Decimal('-0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-0'), 1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('Inf'), 1) == Decimal('Inf') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('Inf'), 1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-Inf'), 1) == Decimal('-Inf') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-Inf'), 1)) == Decimal('-1')
    True
    >>> isnan(_roundhalfupdown_decimal(Decimal('NaN'), 1)) and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('NaN'), 1)) == Decimal('1')
    True
    >>> isnan(_roundhalfupdown_decimal(Decimal('-NaN'), 1)) and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-NaN'), 1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('0'), -1) == Decimal('0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('0'), -1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-0'), -1) == Decimal('-0') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-0'), -1)) == Decimal('-1')
    True
    >>> _roundhalfupdown_decimal(Decimal('Inf'), -1) == Decimal('Inf') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('Inf'), -1)) == Decimal('1')
    True
    >>> _roundhalfupdown_decimal(Decimal('-Inf'), -1) == Decimal('-Inf') and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-Inf'), -1)) == Decimal('-1')
    True
    >>> isnan(_roundhalfupdown_decimal(Decimal('NaN'), -1)) and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('NaN'), -1)) == Decimal('1')
    True
    >>> isnan(_roundhalfupdown_decimal(Decimal('-NaN'), -1)) and copysign(Decimal('1'), _roundhalfupdown_decimal(Decimal('-NaN'), -1)) == Decimal('-1')
    True
