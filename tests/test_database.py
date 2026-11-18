from sqlalchemy import inspect


def test_ledger_table_exist(db_engine):
    assert inspect(db_engine).has_table("ledger_entries")