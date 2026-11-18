from app.models.user import User

def test_user_creation_rollback(db_session):

    user = User(
        full_name = "Test User",
        email = "test@test.com",
        password_hash = "password_hash"
    )

    db_session.add(user)
    db_session.commit()
    saved_user = db_session.get(User, user.id)

    assert saved_user is not None