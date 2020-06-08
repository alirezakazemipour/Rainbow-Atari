import argparse


def get_params():
    parser = argparse.ArgumentParser(description="Parameters based on the Rainbow paper")
    parser.add_argument("--lr", default=6.25e-5, type=float, help="The learning rate")
    parser.add_argument("--multi_step_n", default=3, type=int,
                        help="The number of step to take account formulti step learning")
    parser.add_argument("--batch_size", default=32, type=int, help="The batch size")
    parser.add_argument("--mem_size", default=12000, type=int, help="The memory size")
    parser.add_argument("--gamma", default=0.99, type=float, help="The discount factor")
    parser.add_argument("--tau", default=0.05, type=float, help="Soft update exponential rate")
    parser.add_argument("--max_episodes", default=10000, type=int, help="Maximum number of episodes to train the agent")
    parser.add_argument("--env_name", default="Pong-v0", type=str, help="Name of the environment")
    parser.add_argument("--log_interval", default=1, type=int,
                        help="The interval specifies how often different metrics should be logged, counted by episodes")
    parser.add_argument("--save_interval", default=200, type=int, help="The interval specifies how often different"
                                                                       "parameters should be saved, counted by episodes")
    parser.add_argument("--print_interval", default=200, type=int, help="The interval specifies how often different"
                                                                        "parameters should be printed, counted by episodes")
    parser.add_argument("--train_period", default=4, type=int,
                        help="The period that specifies the number of steps which the networks are not updated")
    parser.add_argument("--do_train", action="store_false", help="The flag determines whether to train"
                                                                 "the agent or play with it")
    parser.add_argument("--V_min", default=-10, type=int, help="Lower bound of the value estimation of"
                                                               "the distributional algorithm")
    parser.add_argument("--V_max", default=10, type=int, help="Upper bound of the value estimation of"
                                                              "the distributional algorithm")
    parser.add_argument("--N_atoms", default=51, type=int, help="Number of atoms to predict the value distribution in"
                                                                "the distributional algorithm")
    parser.add_argument("--adam_eps", default=1.5e-4, type=float, help="The Adam epsilon")
    params = parser.parse_args()
    return vars(params)
