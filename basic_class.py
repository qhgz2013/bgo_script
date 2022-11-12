from dataclasses import dataclass

__all__ = ['PointF', 'Resolution', 'Rect', 'Point']


@dataclass(order=True, unsafe_hash=True)
class PointF:
    """Normalized point."""
    x: float
    y: float


@dataclass(order=True, unsafe_hash=True)
class Resolution:
    """Device resolution."""
    height: int
    width: int


@dataclass(unsafe_hash=True, order=True)
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1


@dataclass(unsafe_hash=True, order=True)
class Point:
    x: int
    y: int

    def to_point_f(self) -> 'PointF':
        return PointF(float(self.x), float(self.y))
