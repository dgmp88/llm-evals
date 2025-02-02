from datetime import datetime

from peewee import (
    DateField,
    FloatField,
    Model,
    TextField,
)
from playhouse.db_url import connect
from playhouse.postgres_ext import JSONField

from llm_maths.env import ENV

db = connect(ENV.NEON_POSTGRES)


class EvalResult(Model):
    model_name = TextField()
    eval_name = TextField()
    result = FloatField()
    timestamp = DateField(default=datetime.now)
    params = JSONField()

    class Meta:
        database = db  # This model uses the "people.db" database.


def init_db():
    db.create_tables([EvalResult])


def test_insert():
    result = EvalResult(model_name="test", eval_name="test", result=0.5)
    result.save()


if __name__ == "__main__":
    import fire

    fire.Fire({"init_db": init_db, "test_insert": test_insert})
