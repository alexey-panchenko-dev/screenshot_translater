from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScreenPoint:
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int

    @classmethod
    def from_points(cls, start: ScreenPoint, end: ScreenPoint) -> ScreenRegion:
        left = min(start.x, end.x)
        top = min(start.y, end.y)
        return cls(
            left=left,
            top=top,
            width=abs(end.x - start.x),
            height=abs(end.y - start.y),
        )

    def is_large_enough(self, minimum_size: int) -> bool:
        return self.width >= minimum_size and self.height >= minimum_size

    def scaled(self, factor: float) -> ScreenRegion:
        left = round(self.left * factor)
        top = round(self.top * factor)
        right = round((self.left + self.width) * factor)
        bottom = round((self.top + self.height) * factor)
        return ScreenRegion(left, top, right - left, bottom - top)

    def as_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }
