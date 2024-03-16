from database.db import db, Set


# Non-tests
pass

# Tests

class TestSets:
    def test_nonblank_set(self) -> None:
        for bp_set in db.query(Set).all():
            assert len(bp_set.blueprints) > 0, 'Sets cannot be empty'
            assert len(bp_set.blueprints) > 1, 'Sets must have at least two Blueprints'
