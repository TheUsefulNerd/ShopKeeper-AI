def test_database_connection(db):
    from sqlalchemy import text

    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1
