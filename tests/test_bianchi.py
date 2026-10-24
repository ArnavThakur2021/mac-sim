from sim.bianchi import solve

def test_fixed_point_range():
    for n in (2,5,10,20,50,100):
        x=solve(n)
        assert 0 < x['throughput'] < 1
        assert 0 < x['collision_probability'] < 1
