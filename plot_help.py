import math
import time
import errno
from math import pi, sin, cos
import os
from images2gif import writeGif

import pygame
from PIL import Image

from graph import Graph




direct = "C:\\Users\\Ricky\\Desktop\\"
fileextension = '.png'
PYGAME_PIXEL = False
PYGAME_FRAME = False
PYGAME = PYGAME_PIXEL or PYGAME_FRAME
if PYGAME:
    pygame.display.init()


class Color(object):
    def __init__(self, r=0, g=0, b=0):
        self.r = min(255, int(r))
        self.g = min(255, int(g))
        self.b = min(255, int(b))
        self.val = self.r | (self.g << 8) | (self.b << 16)
        if PYGAME:
            self.pg = pygame.Color(self.r, self.g, self.b, 0)

    def __add__(self, other):
        return Color(self.r + other.r, self.g + other.g, self.b + other.b)

    def __rmul__(self, other):
        return Color(other * self.r, other * self.g, other * self.b)

    def avg(self, other, (w1, w2)=(0.5, 0.5)):
        return Color(w1 * self.r + w2 * other.r, w1 * self.g + w2 * other.g, w1 * self.b + w2 * other.b)

    def scale(self, r_range, g_range, b_range):
        def _scale(val, (lower, upper)):
            return lower + val * (upper - lower) / 255
        return Color(_scale(self.r, r_range), _scale(self.g, g_range), _scale(self.b, b_range))

    @staticmethod
    def from_int(val):
        return Color(val & 255, val >> 8 & 255, val >> 16 & 255)

    @staticmethod
    def colors(n):
        return [Color.rbow(2 * pi * k / n, 1) for k in range(n)]

    @staticmethod
    def colors0(n):
        return [Color.rbow0(2 * pi * k / n, 1) for k in range(n)]

    @staticmethod
    def hsl(h, s, l):
        c = (1 - abs(2 * l - 1)) * s
        m = l - c / 2
        h1 = (h / (pi / 3)) % 6
        x = c * (1 - abs(h1 % 2 - 1))
        if h is None:
            (r, g, b) = (m, m, m)
        elif 0 <= h1 < 1:
            (r, g, b) = (c + m, x + m, m)
        elif 1 <= h1 < 2:
            (r, g, b) = (x + m, c + m, m)
        elif 2 <= h1 < 3:
            (r, g, b) = (m, c + m, x + m)
        elif 3 <= h1 < 4:
            (r, g, b) = (m, x + m, c + m)
        elif 4 <= h1 < 5:
            (r, g, b) = (x + m, m, c + m)
        else:
            (r, g, b) = (c + m, m, x + m)
        return Color(255 * r, 255 * g, 255 * b)

    @staticmethod
    def rbow(t, freq=1.5):
        return Color(127 * math.sin(freq * t) + 128,
                     127 * math.sin(freq * t - 2 * pi / 3) + 128,
                     127 * math.sin(freq * t + 2 * pi / 3) + 128)

    @staticmethod
    def rbow0(t, freq=1.5):
        return Color.hsl(t * freq, 1, .5)


class PlotData(object):
    def __init__(self, vw, color=Color(0, 0, 0), avg=False, scales=None):
        self.vw = vw
        self.color = color
        self.scales = scales
        if color == "rainbow":
            self.data = [Color(0, 0, 0)] * (vw.dimx * vw.dimy)
        else:
            self.data = [color] * (vw.dimx * vw.dimy)
        if avg or color == "rainbow":
            self.num = [0] * (vw.dimx * vw.dimy)
        if PYGAME:
            self.screen = pygame.display.set_mode((vw.dimx, vw.dimy))
        if vw.axisx:
            self.xaxis()
        if vw.axisy:
            self.yaxis()

    def getpixel(self, (i, j)):
        return self.data[j * self.vw.dimx + i]

    def __getitem__(self, (i, j)):
        return self.data[j * self.vw.dimx + i]

    def putpixel(self, (i, j), color, add=False, avg=False, flip=True):
        if self.scales is not None:
            color = color.scale(*self.scales)
        if 0 <= i < self.vw.dimx and 0 <= j < self.vw.dimy:
            idx = j * self.vw.dimx + i
            if self.color == "rainbow":
                self.num[idx] += 1
                self.data[idx] = Color.rbow(min(2 * pi, self.num[idx]), 1)
            elif not add:
                self.data[idx] = color
            elif avg:
                self.data[idx] = Color.avg(self.data[idx], color,
                                           (self.num[idx] / (self.num[idx] + 1.0), 1 / (self.num[idx] + 1.0)))
                self.num[idx] += 1
            else:
                self.data[idx] = self.data[idx] + color
            if PYGAME_PIXEL:
                self.screen.set_at((i, j), self.data[idx].pg)
                if flip:
                    pygame.display.flip()

    def putpoint(self, (x, y), color, add=False, avg=False, flip=True):
        self.putpixel(self.vw.cart2px((x, y)), color, add, avg, flip)

    def save(self, filename, save=True):
        plot = Image.new("RGB", (self.vw.dimx, self.vw.dimy))
        data2 = [c.val for c in self.data]
        plot.putdata(data2)
        if save:
            plot.save(direct + filename + fileextension)
            print "saved", filename + fileextension, "to", direct, "at", time.asctime()
        if PYGAME_FRAME:
            img = pygame.image.fromstring(plot.tostring(), plot.size, plot.mode)
            self.screen.blit(img, (0, 0))
            pygame.display.flip()
        return plot

    def yaxis(self, color=Color(85, 85, 85)):
        if (0, self.vw.ymax) in self.vw and self.vw.xmax != 0 and self.vw.xmin != 0:
            for i in range(self.vw.dimy):
                self.putpixel((self.vw.xcartpx(0), i), color)

    def xaxis(self, color=Color(85, 85, 85)):
        if (self.vw.xmax, 0) in self.vw and self.vw.ymin != 0 and self.vw.xmin != 0:
            for i in range(self.vw.dimx):
                self.putpixel((i, self.vw.ycartpx(0)), color)

    def line0(self, (x1, y1), (x2, y2), color, add=False, avg=False):
        x1, y1 = self.vw.cart2px((x1, y1))
        x2, y2 = self.vw.cart2px((x2, y2))
        if abs(x2 - x1) > abs(y2 - y1):
            if x1 > x2:
                (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
            for i in range(x1, x2 + 1):
                for c in range(-self.vw.thick, self.vw.thick + 1):
                    for d in range(-self.vw.thick, self.vw.thick + 1):
                        if c ** 2 + d ** 2 <= self.vw.thick ** 2 and x1 != x2:
                            self.putpixel((i + d, y1 + (i - x1) * (y2 - y1) / (x2 - x1) + c), color, add, avg, False)
        else:
            if y1 > y2:
                (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
            for i in range(y1, y2 + 1):
                for c in range(-self.vw.thick, self.vw.thick + 1):
                    for d in range(-self.vw.thick, self.vw.thick + 1):
                        if c ** 2 + d ** 2 <= self.vw.thick ** 2 and y1 != y2:
                            self.putpixel((x1 + (i - y1) * (x2 - x1) / (y2 - y1) + d, i + c), color, add, avg, False)
        if PYGAME:
            pygame.display.flip()

    def line(self, (x1, y1), (x2, y2), color, add=False, avg=False):
        x1, y1 = self.vw.cart2px((x1, y1))
        x2, y2 = self.vw.cart2px((x2, y2))
        t = self.vw.thick
        for c in range(-t, t + 1):
            for d in range(-t, t + 1):
                if c * c + d * d <= t * t:
                    self.putpixel((x1 + c, y1 + d), color, add, avg)
                    self.putpixel((x2 + c, y2 + d), color, add, avg)
        if abs(x2 - x1) > abs(y2 - y1):
            if x1 > x2:
                (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
            for i in range(x1, x2 + 1):
                for c in range(-t, t + 1):
                    self.putpixel((i, y1 + (i - x1) * (y2 - y1) / (x2 - x1) + c), color, add, avg, False)
        else:
            if y1 > y2:
                (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
            for i in range(y1, y2 + 1):
                for c in range(-t, t + 1):
                    self.putpixel((x1 + (i - y1) * (x2 - x1) / (y2 - y1) + c, i), color, add, avg, False)
        pygame.display.flip()

    def circle(self, (x0, y0), r, color, add=False, avg=False, pts=400):
        t = 0
        while t < 2 * pi:
            u = t + 2 * pi / pts
            self.line((x0 + r * cos(t), y0 + r * sin(t)), (x0 + r * cos(u), y0 + r * sin(u)), color, add, avg)
            t = u

    def circumcircle(self, (ax, ay), (bx, by), (cx, cy), color, add=False, avg=False, pts=400):
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if d == 0:
            self.line((ax, ay), (bx, by), color, add, avg)
            self.line((cx, cy), (bx, by), color, add, avg)
        else:
            x0 = ((ax ** 2 + ay ** 2) * (by - cy) + (bx ** 2 + by ** 2) * (cy - ay) + (cx ** 2 + cy ** 2) * (
                ay - by)) / d
            y0 = ((ax ** 2 + ay ** 2) * (cx - bx) + (bx ** 2 + by ** 2) * (ax - cx) + (cx ** 2 + cy ** 2) * (
                bx - ax)) / d
            r = math.sqrt((ax - x0) ** 2 + (ay - y0) ** 2)
            self.circle((x0, y0), r, color, add, avg, pts)


class ViewWindow(object):
    def __init__(self, xmin=-10.0, xmax=10.0, ymin=-10.0, ymax=10.0, tmin=0.0, tmax=2 * pi, tstep=pi / 2500, dimx=500,
                 dimy=500, thick=1, axisx=False, axisy=False):
        self.xmin = float(xmin)
        self.xmax = float(xmax)
        self.ymin = float(ymin)
        self.ymax = float(ymax)
        self.tmin = float(tmin)
        self.tmax = float(tmax)
        self.tstep = float(tstep)
        self.dimx = dimx
        self.dimy = dimy
        self.thick = thick
        self.axisx = axisx
        self.axisy = axisy

    def autoparam(self, xlist, ylist):
        self.xmin = min(
            [min([x(t) for t in [self.tstep * t for t in range(int(self.tmax / self.tstep))]]) for x in xlist])
        self.ymin = min(
            [min([y(t) for t in [self.tstep * t for t in range(int(self.tmax / self.tstep))]]) for y in ylist])
        self.xmax = max(
            [max([x(t) for t in [self.tstep * t for t in range(int(self.tmax / self.tstep))]]) for x in xlist])
        self.ymax = max(
            [max([y(t) for t in [self.tstep * t for t in range(int(self.tmax / self.tstep))]]) for y in ylist])
        self.xmin, self.xmax = self.xmin - .1 * (self.xmax - self.xmin), self.xmax + .1 * (self.xmax - self.xmin)
        self.ymin, self.ymax = self.ymin - .1 * (self.ymax - self.ymin), self.ymax + .1 * (self.ymax - self.ymin)
        if self.xmax - self.xmin > self.ymax - self.ymin:
            self.dimy = int(self.dimy * (self.ymax - self.ymin) / (self.xmax - self.xmin))
        else:
            self.dimx = int(self.dimx * (self.xmax - self.xmin) / (self.ymax - self.ymin))

    def autograph(self, funclist):
        factor = self.dimy / (self.ymax - self.ymin)
        self.ymin = min(
            [min(map(f, [t * (self.xmin + (self.xmax - self.xmin) / self.dimx) for t in range(self.dimx)])) for f in
             funclist])
        self.ymax = max(
            [max(map(f, [t * (self.xmin + (self.xmax - self.xmin) / self.dimx) for t in range(self.dimx)])) for f in
             funclist])
        self.ymin, self.ymax = self.ymin - .1 * (self.ymax - self.ymin), self.ymax + .1 * (self.ymax - self.ymin)
        self.dimy = int((self.ymax - self.ymin) * factor)

    def autocomplex(self, *pts):
        self.xmin = min([z.real for z in pts])
        self.ymin = min([z.imag for z in pts])
        self.xmax = max([z.real for z in pts])
        self.ymax = max([z.imag for z in pts])
        self.xmin, self.xmax = self.xmin - .5 * (self.xmax - self.xmin), self.xmax + .5 * (self.xmax - self.xmin)
        self.ymin, self.ymax = self.ymin - .5 * (self.ymax - self.ymin), self.ymax + .5 * (self.ymax - self.ymin)
        if self.xmax - self.xmin > self.ymax - self.ymin:
            self.dimy = int(self.dimy * (self.ymax - self.ymin) / (self.xmax - self.xmin))
        else:
            self.dimx = int(self.dimx * (self.xmax - self.xmin) / (self.ymax - self.ymin))

    def __contains__(self, (x, y)):
        return self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax

    def contains_pixel(self, (i, j)):
        return 0 <= i < self.dimx and 0 <= j < self.dimy

    def xpxcart(self, i):
        return i * float(self.xmax - self.xmin) / self.dimx + self.xmin

    def xcartpx(self, x):
        return int(self.dimx * (x - self.xmin) / (self.xmax - self.xmin))

    def ypxcart(self, j):
        return self.ymax - j * float(self.ymax - self.ymin) / self.dimy

    def ycartpx(self, y):
        return int(self.dimy * (self.ymax - y) / (self.ymax - self.ymin))

    def px2cart(self, (i, j)):
        return self.xpxcart(i), self.ypxcart(j)

    def cart2px(self, (x, y)):
        return self.xcartpx(x), self.ycartpx(y)

    def pxiterator(self):
        for j in xrange(self.dimy):
            for i in xrange(self.dimx):
                yield (i, j)

    def cartiterator(self):
        for j in xrange(self.dimy):
            for i in xrange(self.dimx):
                yield self.px2cart((i, j))

    def xiterator(self):
        for i in xrange(self.dimx):
            yield self.xpxcart(i)

    def complexiterator(self):
        for j in xrange(self.dimy):
            for i in xrange(self.dimx):
                yield self.xpxcart(i) + self.ypxcart(j) * 1j


def suffix(vw, verbose=False):
    if verbose:
        return " [{0}, {1}] x [{2}, {3}]".format(vw.xmin, vw.xmax, vw.ymin, vw.ymax)
    return ""


def diffquo(f, h):
    return lambda x: (f(x + h) - f(x - h)) / (2 * h)


def newton(f, z0, df=None, n=10, epsilon=1e-10, h=.0001):
    if df is None:
        df = diffquo(f, h)
    if n == 0 or abs(df(z0)) < epsilon:
        return z0
    else:
        return newton(f, z0 - f(z0) / df(z0), df, n - 1, epsilon, h)


def gradient(f, (x0, y0), h=.0001):
    return diffquo(lambda x: f(x, y0), h)(x0), diffquo(lambda y: f(x0, y), h)(y0)


def closest(rootlist, approx, d=lambda z1, z2: abs(z1 - z2), k=1):
    if k == 1:
        minval = d(rootlist[0], approx)
        mindex = 0
        for i in range(1, len(rootlist)):
            if d(rootlist[i], approx) < minval:
                minval = d(rootlist[i], approx)
                mindex = i
        return mindex
    else:
        return rootlist.index(
            sorted(rootlist, lambda x, y: int(math.copysign(1, d(x, approx) - d(y, approx))))[k - 1])


def rootsofunity(n, phi=0):
    return [cos(2 * k * pi / n + phi) + 1j * sin(2 * k * pi / n + phi) for k in range(n)]


def colorcube(func="dfs"):
    if not func.startswith("hilbert"):
        return list(getattr(Graph.grid3d(64, 64, 64), func)((0, 0, 0)))
    else:
        return list(hilbert_3d(6))


def hilbert(n):
    s = "A"
    for i in range(n):
        s2 = ""
        for c in s:
            if c == 'A':
                s2 += "-BF+AFA+FB-"
            elif c == 'B':
                s2 += "+AF-BFB-FA+"
            else:
                s2 += c
        s = s2
    (x, y) = (0, 0)
    (dx, dy) = (1, 0)
    yield (x, y)
    for c in s:
        if c == '+':
            (dx, dy) = (dy, -dx)
        elif c == '-':
            (dx, dy) = (-dy, dx)
        elif c == 'F':
            (x, y) = (x + dx, y + dy)
            yield (x, y)


def hilbert_3d(n):
    if n == 6:
        with open("h3d.csv") as h3d:
            for line in h3d.readlines():
                yield tuple(int(x) for x in line.split(','))
    else:
        s = 'X'
        for i in range(n):
            s2 = ""
            for c in s:
                if c == 'X':
                    s2 += "^<XF^<XFX-F^>>XFX&F+>>XFX-F>X->"
                else:
                    s2 += c
            s = s2
        (x, y, z) = (0, 0, 0)
        hlu = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        yield (x, y, z)
        for c in s:
            if c == 'F':
                (x, y, z) = (x + hlu[0][0], y + hlu[1][0], z + hlu[2][0])
                yield (x, y, z)
            elif c == '+':
                hlu = multmat(hlu, [[0, -1, 0], [1, 0, 0], [0, 0, 1]])  # yaw(90)
            elif c == '-':
                hlu = multmat(hlu, [[0, 1, 0], [-1, 0, 0], [0, 0, 1]])  # yaw(-90)
            elif c == '>':
                hlu = multmat(hlu, [[1, 0, 0], [0, 0, -1], [0, 1, 0]])  # roll(90)
            elif c == '<':
                hlu = multmat(hlu, [[1, 0, 0], [0, 0, 1], [0, -1, 0]])  # roll(-90)
            elif c == '&':
                hlu = multmat(hlu, [[0, 0, 1], [0, 1, 0], [-1, 0, 0]])  # pitch(-90)
            elif c == '^':
                hlu = multmat(hlu, [[0, 0, -1], [0, 1, 0], [1, 0, 0]])  # pitch(90)


def multmat(m1, m2):
    prod = []
    for i in range(len(m1)):
        prod.append([0] * len(m2[0]))
    for i, row in enumerate(m1):
        for j, col in enumerate(transpose(m2)):
            prod[i][j] = sum([a * b for a, b in zip(row, col)])
    return prod


def transpose(m):
    m2 = []
    for i in range(len(m[0])):
        m2.append([0] * len(m))
    for i in range(len(m)):
        for j in range(len(m[0])):
            m2[j][i] = m[i][j]
    return m2


def lp(p, z1=None, z2=None):
    if z1 is None or z2 is None:
        return lambda x, y: (abs(x.real - y.real) ** p + abs(x.imag - y.imag) ** p) ** (1.0 / p)
    else:
        return (abs(z1.real - z2.real) ** p + abs(z1.imag - z2.imag) ** p) ** (1.0 / p)


def mkdir():
    try:
        os.makedirs(direct)
    except OSError as exc:
        if exc.errno != errno.EEXIST or not os.path.isdir(direct):
            raise


def argcmp(z1, z2):
    arg1 = math.atan2(z1.imag, z1.real)
    arg2 = math.atan2(z2.imag, z2.real)
    return int(math.copysign(1, arg1 + 2 * pi * (arg1 < 0) - arg2 - 2 * pi * (arg2 < 0)))


def writegif(filename, images, duration=0.01):
    writeGif(direct + filename + ".gif", images, duration)
    print "saved {0}.gif to {1} at {2}".format(filename, direct, time.asctime())


def sgn(x):
    if x < 0:
        return -1
    if x > 0:
        return 1
    return 0


def frange(start, stop=None, step=1.0):
    start = float(start)
    d = sgn(step)
    if stop is None:
        stop = start
        start = 0.0
    while d * start < d * stop:
        yield start
        start += step


def makegif(cmdlist, duration=0.001, filename="gif" + str(int(time.time()))):
    images = []
    for cmd in cmdlist:
        images.append(eval(cmd))
    writegif(filename, images, duration)


vw0 = ViewWindow(-1.1, 1.1, -1.1, 1.1, 0, 2 * pi, pi / 500, 700, 700, 2, True, True)
vw1 = ViewWindow(-4, 4, -2, 2, 0, 2 * pi, pi / 500, 2000, 1000, 1, True, True)
vw2 = ViewWindow(-2.3, 0.7, -1.5, 1.5, 0, 2 * pi, pi / 200, 200, 200, 0, False, False)
vw3 = ViewWindow(-pi, pi, -pi, pi, 0, 2 * pi, pi / 200, 500, 500, 6, False, False)
vw4 = ViewWindow(-1.96, 1.96, -1.1, 1.1, 0, 2 * pi, pi / 200, 1366, 768, 1, False, False)
vw5 = ViewWindow(-2.3, 0.7, -1.5, 1.5, 0, 2 * pi, pi / 200, 700, 700, 0, False, False)
vw6 = ViewWindow(-1.5, 1.5, -1.5, 1.5, 0, 2 * pi, pi / 200, 400, 400, 2, False, False)
vw7 = ViewWindow(-1, 1, -2, 2, 0, 2 * pi, pi / 500, 800, 800, 2, False, False)
vw8 = ViewWindow(0, 1, 0, 1, 0, 2 * pi, pi / 500, 400, 400, 2, False, False)
vw9 = ViewWindow(-5, 5, -2, 2, 0, 2 * pi, pi / 500, 1200, 480, 1, True, True)
vwA = ViewWindow(-3, 3, -2, 2, 0, 2 * pi, pi / 500, 600, 400, 1, False, False)
vwB = ViewWindow(-1.2, 1.2, -0.4, 2.0, 0, 2 * pi, pi / 500, 400, 400, 2, False, False)

vws = [vw0, vw1, vw2, vw3, vw4, vw5, vw6, vw7, vw8, vw9, vwA, vwB]
