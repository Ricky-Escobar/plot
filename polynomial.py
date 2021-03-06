try:
    import numpy as np
except ImportError:
    np = None


class Polynomial(object):
    def __init__(self, *coeffs, **kwargs):
        self.coeffs = coeffs
        try:
            self.var = kwargs["var"]
        except KeyError:
            self.var = "z"
        try:
            self.exp = kwargs["exp"]
        except KeyError:
            self.exp = "^"
        try:
            self.mult = kwargs["mult"]
        except KeyError:
            self.mult = ""

    def __str__(self):
        s = ""
        first = True
        for i, c in enumerate(self.coeffs):
            coeff = ""
            var = self.var
            exp = ""
            mult = self.mult
            if c == 0:
                var = ""
                mult = ""
            else:
                if first:
                    if c == 1:
                        mult = ""
                    elif c == -1:
                        coeff = "-"
                        mult = ""
                    else:
                        coeff = str(c)
                    first = False
                elif c < 0:
                    if c == -1:
                        if i == len(self.coeffs) - 1:
                            coeff = " - 1"
                        else:
                            coeff = " - "
                        mult = ""
                    else:
                        coeff = " - " + str(-c)
                elif c > 0:
                    if c == 1:
                        if i == len(self.coeffs) - 1:
                            coeff = " + 1"
                        else:
                            coeff = " + "
                        mult = ""
                    else:
                        coeff = " + " + str(c)
                if i == len(self.coeffs) - 1:
                    var = ""
                    mult = ""
                elif i != len(self.coeffs) - 2:
                    exp = self.exp + str(len(self.coeffs) - i - 1)
            s += coeff + mult + var + exp
        if s != "":
            return s
        return "0"

    def func(self):
        return lambda z: self(z)

    def roots(self):
        if np is None:
            raise Exception()
        return np.roots(self.coeffs)

    def deriv(self, order=1):
        if order == 0:
            return self
        return Polynomial(
            *[c * (len(self.coeffs) - i - 1) for i, c in enumerate(self.coeffs) if i != len(self.coeffs) - 1],
            var=self.var, exp=self.exp, mult=self.mult).deriv(order - 1)

    def __call__(self, z):
        val = 0
        for c in self.coeffs:
            val = z * val + c
        return val

    def __rmul__(self, other):
        return Polynomial(*[other * coeff for coeff in self.coeffs], var=self.var, exp=self.exp, mult=self.mult)

    def __mul__(self, other):
        try:
            return Polynomial(*[sum(self.coeffs[j] * other.coeffs[i - j] for j in range(i + 1) if
                                    j < len(self.coeffs) and i - j < len(other.coeffs)) for i in
                                range((len(self.coeffs) - 1) + (len(other.coeffs) - 1) + 1)], var=self.var,
                              exp=self.exp, mult=self.mult)
        except AttributeError:
            return other * self

    def __radd__(self, other):
        return Polynomial(*(self.coeffs[:-1] + (self.coeffs[-1] + other,)), var=self.var, exp=self.exp, mult=self.mult)

    def __add__(self, other):
        try:
            l = max(len(self.coeffs), len(other.coeffs))
            coeffs = [0] * l
            for i in range(1, l + 1):
                if i <= len(self.coeffs):
                    coeffs[-i] = self.coeffs[-i]
                if i <= len(other.coeffs):
                    coeffs[-i] += other.coeffs[-i]
            return Polynomial(*coeffs, var=self.var, exp=self.exp, mult=self.mult)
        except AttributeError:
            return other + self

    def __pow__(self, power):
        poly = Polynomial(1, var=self.var, exp=self.exp, mult=self.mult)
        for i in range(power):
            poly *= self
        return poly
