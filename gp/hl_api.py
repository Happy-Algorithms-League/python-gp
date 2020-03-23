import numpy as np


def evolve(
    pop,
    objective,
    ea,
    max_generations,
    min_fitness,
    record_history=None,
    print_progress=False,
    *,
    label=None,
    n_processes=1,
):
    """
    Evolves a population and returns the history of fitness of parents.

    Parameters
    ----------
    pop : gp.AbstractPopulation
        A population class that will be evolved.
    objective : Callable
        An objective function used for the evolution. Needs to take an
        invidual (gp.AbstractIndividual) as input parameter and return
        a modified individual (with updated fitness).
    ea : EA algorithm instance
        The evolution algorithm. Needs to be a class instance with an
        `initialize_fitness_parents` and `step` method.
    max_generations : int
        Maximum number of generations.
    min_fitness : float
        Minimum fitness at which the evolution is stopped.
    record_history :  callable
        Function that accepts a population instance and a dictionary
        and records properties of interest in the dictionary. Defaults to None.
    print_progress : boolean, optional
        Switch to print out the progress of the algorithm. Defaults to False.
    label : str, optional
        Optional label to be passed to the objective function.
    n_processes : int, optional
        Number of parallel processes to be used. If greater than 1,
        parallel evaluation of the objective is supported. Currently
        not implemented. Defaults to 1.

    Returns
    -------
    dict
        History of the evolution.
    """

    # data structure for recording evolution history; can be populated via user
    # defined recording function
    history = {}

    ea.initialize_fitness_parents(pop, objective, label=label)
    if record_history is not None:
        record_history(pop, history)

    # perform evolution
    max_fitness = np.finfo(np.float).min
    # Main loop: -1 offset since the last loop iteration will still increase generation by one
    while pop.generation < max_generations - 1:

        pop = ea.step(pop, objective, label=label)

        # progress printing, recording, checking exit condition etc.; needs to
        # be done /after/ new parent population was populated from combined
        # population and /before/ new individuals are created as offsprings
        if pop.champion.fitness > max_fitness:
            max_fitness = pop.champion.fitness

        if print_progress:
            print(
                f"\r[{pop.generation + 1}/{max_generations}"
                f"({pop.champion.idx})] max fitness: {max_fitness}\033[K",
                end="",
                flush=True,
            )

        if record_history is not None:
            record_history(pop, history)

        if pop.champion.fitness + 1e-10 >= min_fitness:
            for key in history:
                history[key] = history[key][: pop.generation + 1]
            break

    if print_progress:
        print()

    return history
