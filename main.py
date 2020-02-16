# import gym_moving_dot
# import gym
from moving_dot_env import MovingDotDiscreteEnv
import numpy as np
from skimage.transform import resize
from logger import LOG
from play import Play

from agent import Agent

ENV_NAME = "MovingDotDiscrete-v0"
# ENV_NAME = "MontezumaRevenge-v0"
# ENV_NAME = "Breakout-v0"
# test_env = gym.make(ENV_NAME)
test_env = MovingDotDiscreteEnv()

MAX_EPISODES = 450
MAX_STEPS = 1000  # test_env._max_episode_steps
save_interval = 200
log_interval = 5  # TODO has conflicts with save interval when loading for playing is needed

episode_log = LOG()

TRAIN = False


def rgb2gray(img):
    return 0.2125 * img[..., 0] + 0.7154 * img[..., 1] + 0.0721 * img[..., 2]


def preprocessing(img):
    img = rgb2gray(img) / 255.0
    img = resize(img, output_shape=[84, 84])
    return img


def stack_frames(stacked_frames, state, is_new_episode):
    frame = preprocessing(state)

    if is_new_episode:
        stacked_frames = np.stack([frame for _ in range(4)], axis=2)
    else:
        stacked_frames = stacked_frames[..., :3]
        stacked_frames = np.concatenate([stacked_frames, np.expand_dims(frame, axis=2)], axis=2)
    return stacked_frames


if __name__ == '__main__':

    # env = gym.make(ENV_NAME)
    # n_actions = env.action_space.n
    env = MovingDotDiscreteEnv()
    n_actions = 4
    stacked_frames = np.zeros(shape=[84, 84, 4], dtype='float32')
    agent = Agent(n_actions=n_actions, gamma=0.99, lr=6.25e-5,
                  tau=0.001, state_shape=[84, 84, 4], capacity=39000,
                  alpha=0.99, epsilon_start=0.9, epsilon_end=0.05,
                  epsilon_decay=500, batch_size=32)
    if TRAIN:

        for episode in range(1, MAX_EPISODES + 1):
            s = env.reset()
            stacked_frames = stack_frames(stacked_frames, s, True)
            episode_reward = 0
            episode_loss = 0

            episode_log.on()

            for step in range(1, MAX_STEPS + 1):

                stacked_frames_copy = stacked_frames.copy()
                action = agent.choose_action(stacked_frames_copy)
                s_, r, d, _ = env.step(action)
                # r = np.clip(r, -1, 1)
                stacked_frames = stack_frames(stacked_frames, s_, False)
                agent.store(stacked_frames_copy, action, r, stacked_frames, d)
                # env.render()
                if step % 4 == 0:
                    loss = agent.train()
                    episode_loss += loss
                episode_reward += r
                # if step % save_interval == 0:
                #     episode_log.save_weights(agent.eval_model, agent.optimizer, episode, step)

                if d:
                    break

            episode_log.off()
            if episode % log_interval == 0:
                episode_log.printer(episode, episode_reward, episode_loss, agent.eps_threshold, step)
        episode_log.printer(episode, episode_reward, episode_loss, agent.eps_threshold, step)
        episode_log.save_weights(agent.eval_model, agent.optimizer, episode, step)
    # else:
    episode = MAX_EPISODES
    step = MAX_STEPS
    # region play
    # play_path = "./models/" + episode_log.dir + "/" "episode" + str(episode) + "-" + "step" + str(step)
    play_path = "/content/drive/My Drive/Colab Notebooks/Rainbow/models/2020-02-16-10-48-38/episode450-step1000"
    player = Play(agent, env, play_path)
    player.evaluate()
    # endregion

# for _ in range(100):
#     test_env.reset()
#     done = False
#     while not done:
#         a =test_env.action_space.sample()
#         _, r, done, _ = test_env.step(a)
#         print(r)
#         test_env.render()
#         x = input()
