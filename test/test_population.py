import copy

import numpy as np
import pytest

import cgp
from cgp.genome import ID_INPUT_NODE, ID_NON_CODING_GENE, ID_OUTPUT_NODE


def test_assert_mutation_rate(rng_seed, genome_params, mutation_rate):
    with pytest.raises(ValueError):
        cgp.Population(5, -0.1, rng_seed, genome_params)

    with pytest.raises(ValueError):
        cgp.Population(5, 1.1, rng_seed, genome_params)

    # assert that no error is thrown for a suitable mutation rate
    cgp.Population(5, mutation_rate, rng_seed, genome_params)


def test_init_random_parent_population(population_params, genome_params):
    pop = cgp.Population(**population_params, genome_params=genome_params)
    assert len(pop.parents) == population_params["n_parents"]


def test_champion(population_simple_fitness):
    pop = population_simple_fitness
    assert pop.champion == pop.parents[-1]


def test_mutate(population_params, genome_params):
    population_params["mutation_rate"] = 0.5
    pop = cgp.Population(**population_params, genome_params=genome_params)

    offspring = pop.parents
    offspring_original = copy.deepcopy(offspring)
    offspring = pop.mutate(offspring)
    assert np.any(
        [off_orig != off_mutated for off_orig, off_mutated in zip(offspring_original, offspring)]
    )


def test_fitness_parents(population_params, genome_params):
    pop = cgp.Population(**population_params, genome_params=genome_params)
    fitness_values = np.random.rand(population_params["n_parents"])
    for fitness, parent in zip(fitness_values, pop.parents):
        parent.fitness = fitness

    assert np.all(pop.fitness_parents() == pytest.approx(fitness_values))


def test_pop_uses_own_rng(population_params, genome_params, rng_seed):
    """Test independence of Population on global numpy rng.
    """

    pop = cgp.Population(**population_params, genome_params=genome_params)

    np.random.seed(rng_seed)

    pop._generate_random_parent_population()
    parents_0 = list(pop._parents)

    np.random.seed(rng_seed)

    pop._generate_random_parent_population()
    parents_1 = list(pop._parents)

    # since Population does not depend on global rng seed, we
    # expect different individuals in the two populations
    for p_0, p_1 in zip(parents_0, parents_1):
        assert p_0.genome.dna != p_1.genome.dna


def test_parent_individuals_are_assigned_correct_indices(population_params, genome_params):

    pop = cgp.Population(**population_params, genome_params=genome_params)

    for idx, ind in enumerate(pop.parents):
        assert ind.idx == idx


def test_individual_init(population_params, genome_params):

    dna = [
        ID_INPUT_NODE,
        ID_NON_CODING_GENE,
        ID_NON_CODING_GENE,
        0,
        0,
        0,
        1,
        1,
        1,
        2,
        2,
        2,
        ID_OUTPUT_NODE,
        3,
        ID_NON_CODING_GENE,
    ]

    def individual_init(ind):
        ind.genome.dna = dna
        return ind

    genome_params = {
        "n_inputs": 1,
        "n_outputs": 1,
        "n_columns": 3,
        "n_rows": 1,
        "levels_back": None,
        "primitives": (cgp.Add, cgp.Sub, cgp.ConstantFloat),
    }

    # without passing individual_init comparison fails
    pop = cgp.Population(**population_params, genome_params=genome_params)
    for ind in pop.parents:
        with pytest.raises(AssertionError):
            assert ind.genome.dna == dna

    # with passing individual_init comparison succeeds
    pop = cgp.Population(
        **population_params, genome_params=genome_params, individual_init=individual_init
    )
    for ind in pop.parents:
        assert ind.genome.dna == dna


def test_individual_init_expects_callable(population_params, genome_params):
    # passing a list as individual_init fails
    with pytest.raises(TypeError):
        cgp.Population(**population_params, genome_params=genome_params, individual_init=[])
