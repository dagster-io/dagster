var MersenneTwister = require('../');
var g = new MersenneTwister();

describe('Generator', function() {
	it('Should repeat random sequence on same seed', function() {
		var seed = 123;

		g.init_seed(seed);
		var first_1 = g.random();
		var first_2 = g.random();

		g.init_seed(seed);
		var second_1 = g.random();
		var second_2 = g.random();

		first_1.should.be.exactly(second_1);
		first_2.should.be.exactly(second_2);
	});

	it('Should allow seeding via constructor', function() {
		var seed = 325;
		var g1 = new MersenneTwister(seed);
		var g2 = new MersenneTwister(seed);

		for (var i = 0; i < 5; ++i) {
			g1.random().should.be.exactly(g2.random());
		}
	});

	it('Should roughly match Python when seeded by array', function() {
	        var seed1 = 0;
                var seed2 = 42;

	        var g1 = new MersenneTwister([seed1]);
	        var g2 = new MersenneTwister([seed2]);

                /* We should get a near exact match with Python's rng
                 * when we seed by array.  The code for generating
                 * these comparison values is something like:

                 import random

                 r = random.Random(0)

                 for i in range(10000000):
                     x = r.random()
                     if i % 1000000 == 0: print(x)
                */
                var values1 = [0.84442, 0.34535, 0.25570, 0.32368, 0.89075];
                var values2 = [0.63942, 0.55564, 0.55519, 0.81948, 0.94333];

		for (var i = 0; i < 5000000; i++) {
 		       var rval1 = g1.random_long();
 		       var rval2 = g2.random_long();

                       if (i % 1000000 == 0) {
                            var idx = i / 1000000;
                            rval1.should.be.approximately(values1[idx], 1e-5);
                            rval2.should.be.approximately(values2[idx], 1e-5);
                        }
		}
 	});
});
