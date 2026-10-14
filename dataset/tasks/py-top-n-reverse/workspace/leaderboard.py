"""Weekly leaderboard."""

from dataclasses import dataclass

from ranking import top_n


@dataclass
class Player:
    name: str
    score: int


def podium(players):
    """The three best players, best first."""
    return top_n(players, 3, key=lambda p: p.score)


def format_podium(players):
    return "\n".join(f"{i}. {p.name} ({p.score})" for i, p in enumerate(podium(players), start=1))
