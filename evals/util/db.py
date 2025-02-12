from datetime import datetime

from peewee import (
    DateTimeField,
    FloatField,
    Model,
    TextField,
)
from playhouse.db_url import connect

from evals.util.env import ENV

db = connect(ENV.NEON_POSTGRES)


class EvalResult(Model):
    model_name = TextField()
    eval_name = TextField()
    result = FloatField()
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db  # This model uses the "people.db" database.


def init_db():
    db.create_tables([EvalResult])


def test_insert():
    result = EvalResult(model_name="test", eval_name="test", result=0.5)
    result.save()


def read_all():
    import pandas as pd

    results = [r for r in EvalResult.select().dicts()]

    results = pd.DataFrame(results)

    print(results.to_markdown())


if __name__ == "__main__":
    import fire

    fire.Fire({"init_db": init_db, "test_insert": test_insert, "read": read_all})
