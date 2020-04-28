import functools
import matplotlib.pyplot as plt
import numpy as np
import scipy.constants
import warnings

import gp


"""Example demonstrating the use of Cartesian Genetic Programming for
two regression tasks."""


def f_target_easy(x):
    return x[:, 0] ** 2 + 2 * x[:, 0] * x[:, 1] + x[:, 1] ** 2


def f_target_hard(x):
    return 1.0 + 1.0 / (x[:, 0] + x[:, 1])


def objective(individual, target_function, seed):
    """Objective function of the regression task.

    Parameters
    ----------
    individual : gp.Individual
        Individual of the Cartesian Genetic Programming Framework.
    target_function : Callable
        Target function.

    Returns
    -------
    gp.Individual
        Modified individual with updated fitness value.
    """
    if individual.fitness is not None:
        return individual

    n_function_evaluations = 1000

    np.random.seed(seed)

    f_graph = individual.to_func()
    y = np.empty(n_function_evaluations)
    x = np.random.uniform(-4, 4, size=(n_function_evaluations, 2))
    for i, x_i in enumerate(x):
        with warnings.catch_warnings():  # ignore warnings due to zero division
            warnings.filterwarnings(
                "ignore", message="divide by zero encountered in double_scalars"
            )
            warnings.filterwarnings(
                "ignore", message="invalid value encountered in double_scalars"
            )
            try:
                y[i] = f_graph(x_i)[0]
            except ZeroDivisionError:
                individual.fitness = -np.inf
                return individual

    loss = np.mean((target_function(x) - y) ** 2)
    individual.fitness = -loss

    return individual


def evolution(f_target):
    """Execute CGP on a regression task for a given target function.

    Parameters
    ----------
    f_target : Callable
        Target function

    Returns
    -------
    dict
        Dictionary containing the history of the evolution
    Individual
        Individual with the highest fitness in the last generation
    """
    population_params = {"n_parents": 10, "mutation_rate": 0.5, "seed": 8188211}

    genome_params = {
        "n_inputs": 2,
        "n_outputs": 1,
        "n_columns": 10,
        "n_rows": 2,
        "levels_back": 5,
        "primitives": [gp.Add, gp.Sub, gp.Mul, gp.Div, gp.ConstantFloat],
    }

    ea_params = {"n_offsprings": 10, "n_breeding": 10, "tournament_size": 2, "n_processes": 2}

    evolve_params = {"max_generations": 1000, "min_fitness": 0.0}

    # create population that will be evolved
    pop = gp.Population(**population_params, genome_params=genome_params)

    # create instance of evolutionary algorithm
    ea = gp.ea.MuPlusLambda(**ea_params)

    # define callback for recording of fitness over generations
    history = {}
    history["fitness_parents"] = []

    def recording_callback(pop):
        history["fitness_parents"].append(pop.fitness_parents())

    # the objective passed to evolve should only accept one argument,
    # the individual
    obj = functools.partial(objective, target_function=f_target, seed=population_params["seed"])

    # Perform the evolution
    gp.evolve(
        pop, obj, ea, **evolve_params, print_progress=True, callback=recording_callback,
    )
    return history, pop.champion


if __name__ == "__main__":
    width = 9.0
    fig, axes = plt.subplots(2, 2, figsize=(width, width / scipy.constants.golden))

    for i, (label, target_function) in enumerate(
        zip(["easy", "hard"], [f_target_easy, f_target_hard])
    ):
        history, champion = evolution(target_function)

        ax_fitness, ax_function = axes[i]
        ax_fitness.set_xlabel("Generation")
        ax_fitness.set_ylabel("Fitness")

        history_fitness = np.array(history["fitness_parents"])
        ax_fitness.plot(np.max(history_fitness, axis=1), label="Champion")
        ax_fitness.plot(np.mean(history_fitness, axis=1), label="Population mean")

        ax_fitness.set_yscale("symlog")
        ax_fitness.set_ylim(-1.0e4, 0.0)
        ax_fitness.legend()

        f_graph = champion.to_func()
        x_0_range = np.linspace(-5.0, 5.0, 20)
        x_1_range = np.ones_like(x_0_range) * 2.0  # fix x_1 such than 1d plot makes sense
        y = [f_graph([x_0, x_1_range[0]]) for x_0 in x_0_range]
        y_target = target_function(np.hstack([x_0_range.reshape(-1, 1), x_1_range.reshape(-1, 1)]))

        ax_function.plot(x_0_range, y_target, lw=2, alpha=0.5, label="Target")
        ax_function.plot(x_0_range, y, "x", label="Champion")
        ax_function.legend()
        ax_function.set_ylabel(r"$f(x)$")
        ax_function.set_xlabel(r"$x$")

    fig.savefig("example_evo_regression.pdf")
