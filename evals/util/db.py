from datetime import datetime

from peewee import DateTimeField, FloatField, IntegerField, Model, TextField
from playhouse.db_url import connect

from evals.util.env import ENV

db = connect(ENV.NEON_POSTGRES)


class EvalResult(Model):
    provider = TextField()
    model = TextField()
    eval_name = TextField()
    result = FloatField()
    runs = IntegerField()
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db  # This model uses the "people.db" database.


def init_db():
    db.create_tables([EvalResult])


def test_insert():
    result = EvalResult(
        provider="anthropic",
        model="claude-sonnet-4",
        eval_name="test",
        result=0.5,
        runs=1,
    )
    result.save()


def read_all():
    import pandas as pd

    results = [r for r in EvalResult.select().dicts()]

    results = pd.DataFrame(results)

    results = (
        results.groupby(["provider", "model", "eval_name"])
        .result.mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    return results


if __name__ == "__main__":
    import fire

    fire.Fire({"init_db": init_db, "test_insert": test_insert, "read": read_all})
