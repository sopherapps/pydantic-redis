import pprint
from typing import Tuple
from pydantic_redis import RedisConfig, Model, Store


class Score(Model):
    _primary_key_field: str = "id"
    id: str
    total: int


class ScoreBoard(Model):
    _primary_key_field: str = "id"
    id: str
    scores: Tuple[str, Score]


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(name="test", redis_config=RedisConfig())

    store.register_model(Score)
    store.register_model(ScoreBoard)

    ScoreBoard.insert(
        data=ScoreBoard(
            id="test",
            scores=(
                "mark",
                Score(id="some id", total=50),
            ),
        )
    )
    score_board_response = ScoreBoard.select(ids=["test"])
    scores_response = Score.select(ids=["some id"])

    Score.update(_id="some id", data={"total": 78})
    updated_score_board_response = ScoreBoard.select(ids=["test"])

    ScoreBoard.update(
        _id="test",
        data={
            "scores": (
                "tom",
                Score(id="some id", total=60),
            )
        },
    )
    updated_score_response = Score.select(ids=["some id"])

    print("score board:")
    pp.pprint(score_board_response)
    print("\nscores:")
    pp.pprint(scores_response)

    print("\nindirectly updated score board:")
    pp.pprint(updated_score_board_response)
    print("\nindirectly updated score:")
    pp.pprint(updated_score_response)
