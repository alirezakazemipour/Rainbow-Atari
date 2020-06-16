import gym
from logger import Logger
from play import Play
from agent import Agent
from utils import *
from config import get_params
import time


def intro_env():
    test_env.reset()
    for _ in range(max_steps):
        a = test_env.env.action_space.sample()
        _, reward, done, info = test_env.step(a)
        test_env.env.render()
        time.sleep(0.005)
        print(f"reward: {reward}")
        print(info)
        if done:
            break
    test_env.close()
    exit(0)


if __name__ == '__main__':
    params = get_params()
    test_env = gym.make(params["env_name"])
    n_actions = test_env.action_space.n
    max_steps = test_env._max_episode_steps
    print(f"Environment: {params['env_name']}\n"
          f"Number of actions:{n_actions}")

    if 'FIRE' in test_env.unwrapped.get_action_meanings():
        test_env = FireResetEnv(test_env)
    else:
        test_env = EpisodicLifeEnv(test_env)
    assert 'NoFrameskip' in test_env.env.spec.id

    if params["do_intro_env"]:
        intro_env()

    env = gym.make(params["env_name"])
    env.seed(123)
    if 'FIRE' in env.unwrapped.get_action_meanings():
        env = FireResetEnv(env)
    else:
        env = EpisodicLifeEnv(env)
    logger = Logger(**params)
    stacked_frames = np.zeros(shape=[84, 84, 4], dtype='float32')
    agent = Agent(n_actions=n_actions,
                  state_shape=[84, 84, 4],
                  **params)

    if not params["train_from_scratch"]:
        chekpoint = logger.load_weights()
        agent.online_model.load_state_dict(chekpoint["online_model_state_dict"])
        agent.target_model.load_state_dict(chekpoint["target_model_state_dict"])
        agent.epsilon = chekpoint["epsilon"]
        agent.memory = chekpoint["memory"]
        agent.n_step_buffer = chekpoint["n_step_buffer"]
        min_episode = chekpoint["episode"]

        print("Keep training from previous run.")
    else:
        min_episode = 0
        print("Train from scratch.")

    if params["do_train"]:

        for episode in range(min_episode + 1, params["max_episodes"] + 1):
            s = env.reset()
            stacked_frames = stack_frames(stacked_frames, s, True)
            episode_reward = 0
            episode_loss = 0
            logger.on()
            for step in range(1, max_steps + 1):

                stacked_frames_copy = stacked_frames.copy()
                action = agent.choose_action(stacked_frames_copy)
                s_, r, d, _ = env.step(action)
                stacked_frames = stack_frames(stacked_frames, s_, False)
                r = np.clip(r, -1.0, 1.0)
                agent.store(stacked_frames_copy, action, r, stacked_frames, d)
                env.env.render()
                time.sleep(0.005)
                if step % params["train_period"]:
                    loss = agent.train()
                    episode_loss += loss

                episode_reward += r
                if d:
                    break

            logger.off()
            # agent.update_epsilon()
            logger.log(episode, episode_reward, episode_loss, step, len(agent.memory), agent.beta)
            if episode % params["interval"] == 0:
                logger.save_weights(episode, agent)

    else:
        episode = params["max_episodes"]
        step = max_steps
        # region play
        play_path = "./models/" + logger.dir + "/" "episode" + str(episode) + "-" + "step" + str(step)
        player = Play(agent, env, play_path)
        player.evaluate()
        # endregion
