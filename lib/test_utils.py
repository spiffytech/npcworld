from npcworld.lib import utils

def test_replace_true():
    new_val_fn = lambda n: n**2
    cmp = lambda n: n % 2 == 0
    seq = (1, 2, 3, 4)

    new_seq = utils.replace_true(new_val_fn, cmp, seq)
    assert new_seq == (1, 4, 3, 16)

def test_frames_to_secs():
    fts = utils.frames_to_secs(1)
    assert 0 < round(fts, 5) < 1
