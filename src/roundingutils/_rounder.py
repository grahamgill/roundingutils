import decimal
from decimal import Decimal
from enum import Enum
from math import floor, ceil, trunc, copysign, modf, fmod, fabs
from numbers import Integral, Real, Number, Complex, Rational
from typing import Callable, Dict

# all we need for `import *`
__all__ = ['Rounder', 'RoundingMode']

class RoundingMode(Enum):
  """Collection of rounding modes including some which have no known use cases.
  
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

def _sign(x : Real | Decimal) -> Integral:
  return 0 if x == 0 else 1 if x > 0 else -1 if x < 0 else int(copysign(1, x))

def _awayfromzero(x : Real | Decimal) -> Integral:
  return ceil(x) if x >= 0 else floor(x)

def _roundhalftozero(x : Real | Decimal) -> Integral:
  return _sign(x) * ceil((2 * abs(x) - 1) / 2)

def _roundhalffromzero(x : Real | Decimal) -> Integral:
  return _sign(x) * floor((2 * abs(x) + 1) / 2)

def _roundhalfdown(x : Real | Decimal) -> Integral:
  return ceil((2 * x - 1) / 2)

def _roundhalfup(x : Real | Decimal) -> Integral:
  return floor((2 * x + 1) / 2)

def _roundhalfodd(x : Real | Decimal) -> Integral:
  sgn_x = _sign(x)
  return round(x + sgn_x) - sgn_x

def _round05fromzero(x : Real | Decimal) -> Integral:
  tozero_x = trunc(x)
  return tozero_x if tozero_x % 5 else _awayfromzero(x)

def _sign_float(x : float) -> float:
  return 0.0 if x == 0.0 else copysign(1.0, x)

def _ceil_float(x : float) -> float:
  fpart, ipart = modf(x)
  return ipart if fpart <= 0.0 else ipart + 1.0

def _floor_float(x : float) -> float:
  fpart, ipart = modf(x)
  return ipart if fpart >= 0.0 else ipart - 1.0

def _trunc_float(x : float) -> float:
  _, ipart = modf(x)
  return ipart

def _awayfromzero_float(x : float) -> float:
  fpart, ipart = modf(x)
  return ipart if fpart == 0.0 else ipart + copysign(1.0, fpart)

def _roundhalfeven_float(x : float) -> float:
  return round(x, 0)

def _roundhalfodd_float(x : float) -> float:
  sgn_x = copysign(1.0, x)
  return copysign(round(x + sgn_x, 0) - sgn_x, x)

def _roundhalftozero_float(x : float) -> float:
  return copysign(1.0, x) * _ceil_float((2.0 * fabs(x) - 1.0) / 2.0)

def _roundhalffromzero_float(x : float) -> float:
  return copysign(1.0, x) * _floor_float((2.0 * fabs(x) + 1.0) / 2.0)

def _roundhalfdown_float(x : float) -> float:
  return _ceil_float((2.0 * x - 1.0) / 2.0)

def _roundhalfup_float(x : float) -> float:
  return _floor_float((2.0 * x + 1.0) / 2.0)

def _round05fromzero_float(x : float) -> float:
  fpart, ipart = modf(x)
  return ipart if fpart == 0.0 or fmod(ipart, 5.0) else ipart + copysign(1.0, fpart)

def _roundhalfodd_decimal(x : Decimal) -> Decimal:
  sgn_x = Decimal(1).copy_sign(x)
  return ((x + sgn_x).to_integral_value(decimal.ROUND_HALF_EVEN) - sgn_x).copy_sign(x)

def _roundhalfupdown_decimal(x : Decimal, direction : Decimal | int) -> Decimal:
  sgn_x = Decimal(1).copy_sign(x) * Decimal(1).copy_sign(direction)
  return x.to_integral_value(decimal.ROUND_HALF_DOWN if sgn_x < 0 else decimal.ROUND_HALF_UP)

def _to_input_type(f : Callable[[Number], Number]) -> Callable[[Number], Number]:
  return lambda x: type(x)(f(x))

def _apply_to_real_part(f : Callable[[Number], Number]) -> Callable[[Number], Number]:
  return lambda x: f(x.real)

def _map_over_dict_vals(f : Callable, d : Dict) -> Dict:
  return {k : f(v) for k, v in d.items()}

class Rounder():
  _real_to_integral = {
    RoundingMode.ROUNDDOWN : floor,
    RoundingMode.ROUNDUP : ceil,
    RoundingMode.ROUNDTOZERO : trunc,
    RoundingMode.ROUNDFROMZERO : _awayfromzero,
    RoundingMode.ROUNDHALFEVEN : round,
    RoundingMode.ROUNDHALFODD : _roundhalfodd,
    RoundingMode.ROUNDHALFDOWN : _roundhalfdown,
    RoundingMode.ROUNDHALFUP : _roundhalfup,
    RoundingMode.ROUNDHALFTOZERO : _roundhalftozero,
    RoundingMode.ROUNDHALFFROMZERO : _roundhalffromzero,
    RoundingMode.ROUND05FROMZERO : _round05fromzero
  }

  _float_to_float = {
    RoundingMode.ROUNDDOWN : _floor_float,
    RoundingMode.ROUNDUP : _ceil_float,
    RoundingMode.ROUNDTOZERO : _trunc_float,
    RoundingMode.ROUNDFROMZERO : _awayfromzero_float,
    RoundingMode.ROUNDHALFEVEN : _roundhalfeven_float,
    RoundingMode.ROUNDHALFODD : _roundhalfodd_float,
    RoundingMode.ROUNDHALFDOWN : _roundhalfdown_float,
    RoundingMode.ROUNDHALFUP : _roundhalfup_float,
    RoundingMode.ROUNDHALFTOZERO : _roundhalftozero_float,
    RoundingMode.ROUNDHALFFROMZERO : _roundhalffromzero_float,
    RoundingMode.ROUND05FROMZERO : _round05fromzero_float
  }

  _decimal_to_decimal = {
    RoundingMode.ROUNDDOWN : lambda x: x.to_integral_value(decimal.ROUND_FLOOR),
    RoundingMode.ROUNDUP : lambda x: x.to_integral_value(decimal.ROUND_CEILING),
    RoundingMode.ROUNDTOZERO : lambda x: x.to_integral_value(decimal.ROUND_DOWN),
    RoundingMode.ROUNDFROMZERO : lambda x: x.to_integral_value(decimal.ROUND_UP),
    RoundingMode.ROUNDHALFEVEN : lambda x: x.to_integral_value(decimal.ROUND_HALF_EVEN),
    RoundingMode.ROUNDHALFODD : _roundhalfodd_decimal,
    RoundingMode.ROUNDHALFDOWN : lambda x: _roundhalfupdown_decimal(x, Decimal(-1)),
    RoundingMode.ROUNDHALFUP : lambda x: _roundhalfupdown_decimal(x, Decimal(1)),
    RoundingMode.ROUNDHALFTOZERO : lambda x: x.to_integral_value(decimal.ROUND_HALF_DOWN),
    RoundingMode.ROUNDHALFFROMZERO : lambda x: x.to_integral_value(decimal.ROUND_HALF_UP),
    RoundingMode.ROUND05FROMZERO : lambda x: x.to_integral_value(decimal.ROUND_05UP)
  }

  def __init__(self, number_type : Number | type[Number], to_integral : bool = True, default_mode : RoundingMode = RoundingMode.ROUNDHALFEVEN):
    if isinstance(number_type, Number):
      number_type = type(number_type)

    self._number_type = number_type
    self._to_integral = to_integral
    self._default_mode = default_mode
    self.isinteger = Rounder._isinteger_selector(number_type)

    if to_integral:
      if issubclass(number_type, Real | Decimal):
        self.roundingfuncs = Rounder._real_to_integral

      elif issubclass(number_type, Complex):
        self.roundingfuncs = _map_over_dict_vals(_apply_to_real_part, Rounder._real_to_integral)

      else:
        raise NotImplementedError
      
      self.numunits = lambda x, u, m = self.default_mode: Rounder.numunits(self, x, u, m)
      self.roundunits = lambda x, u, m = self.default_mode: type(u)(Rounder.roundunits(self, x, u, m))

    else:
      if issubclass(number_type, float):
        self.roundingfuncs = _map_over_dict_vals(_to_input_type, Rounder._float_to_float)

      elif issubclass(number_type, Decimal):
        self.roundingfuncs = _map_over_dict_vals(_to_input_type, Rounder._decimal_to_decimal)

      elif issubclass(number_type, Real):
        self.roundingfuncs = _map_over_dict_vals(_to_input_type, Rounder._real_to_integral)

      elif issubclass(number_type, complex):
        self.roundingfuncs = _map_over_dict_vals(_to_input_type, _map_over_dict_vals(_apply_to_real_part, Rounder._float_to_float))

      elif issubclass(number_type, Complex):
        self.roundingfuncs = _map_over_dict_vals(_to_input_type, _map_over_dict_vals(_apply_to_real_part, Rounder._real_to_integral))
      
      else:
        raise NotImplementedError
      
      self.numunits = lambda x, u, m = self.default_mode: self.number_type(Rounder.numunits(self, x, u, m))
      self.roundunits = lambda x, u, m = self.default_mode: self.number_type(Rounder.roundunits(self, x, u, m))
      
  def __call__(self, x : Number, mode : RoundingMode = None) -> Number:
    if mode is None:
      mode = self.default_mode
    
    return self.roundingfuncs[mode](x)
  
  @property
  def roundint(self):
    return self.__call__
  
  @property
  def default_mode(self):
    return self._default_mode
  
  @property
  def number_type(self):
    return self._number_type
  
  @property
  def to_integral(self):
    return self._to_integral
  
  @property
  def roundingfuncs(self):
    return self._roundingfuncs
  
  @roundingfuncs.setter
  def roundingfuncs(self, dict):
    self._roundingfuncs = dict

  @property
  def isinteger(self):
    return self._isinteger
  
  @isinteger.setter
  def isinteger(self, fn):
    self._isinteger = lambda x: True if isinstance(x, Integral) else fn(x)

  def numunits(self, x : Number, unitsize : Number, mode : RoundingMode) -> Integral:
    return self.roundingfuncs[mode](x / unitsize)

  def roundunits(self, x : Number, unitsize : Number, mode : RoundingMode) -> Number:
    if unitsize == 0:
      return x

    return self.roundingfuncs[mode](x / unitsize) * unitsize
  
  def isunitsized(self, x : Number, unitsize : Number) -> bool:
    if unitsize == 0:
      return True

    return self.isinteger(x / unitsize)

  @staticmethod
  def _isinteger_selector(t : type[Number]) -> Callable[[Number], bool]:
    if issubclass(t, Integral):
      return lambda _: True
    
    if issubclass(t, float):
      return lambda x: x.is_integer()

    if issubclass(t, Decimal):
      return lambda x: x.as_integer_ratio()[1] == 1
    
    if issubclass(t, Rational):
      return lambda x: x.denominator == 1 or x.numerator % x.denominator == 0
    
    if issubclass(t, Real):
      return lambda x: round(x, 0) == x
    
    if issubclass(t, complex):
      return lambda x: x.real.is_integer() and x.imag == 0

    if issubclass(t, Complex):
      return lambda x: round(x.real, 0) == x.real and x.imag == 0
    
    if issubclass(t, Number):
      raise NotImplementedError
    
    return False

if __name__ == "__main__":
    import doctest
    doctest.testmod()
