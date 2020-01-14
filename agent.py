from torch import nn, from_numpy
import torch
import torch.nn.functional as F
from torch.optim.rmsprop import RMSprop

import numpy as np

from replay_memory import ReplayMemory, Transition

if torch.cuda.is_available():
    torch.backends.cudnn.deterministic = True


class DQN(nn.Module):
    def __init__(self, name, state_shape, n_actions):
        super(DQN, self).__init__()
        self.name = name
        width, height, channel = state_shape
        self.conv1 = nn.Conv2d(channel, 16, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=4, stride=2)

        def conv2d_size_out(size, kernel_size=5, stride=2):
            return (size - kernel_size) // stride + 1

        convw = conv2d_size_out(conv2d_size_out(width, kernel_size=8, stride=4), kernel_size=4, stride=2)
        convh = conv2d_size_out(conv2d_size_out(height, kernel_size=8, stride=4), kernel_size=4, stride=2)
        linear_input_size = convw * convh * 32
        self.fc1 = nn.Linear(linear_input_size, 256)
        self.output = nn.Linear(256, n_actions)

        for m in self.modules():
            if isinstance(m, torch.nn.Conv2d):
                nn.init.kaiming_normal_(m.weight.detach())
                m.bias.detach().zero_()
            elif isinstance(m, torch.nn.Linear):
                nn.init.kaiming_normal_(m.weight.detach())
                m.bias.detach().zero_()

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        return self.output(x)


class Agent:
    def __init__(self, n_actions, gamma, tau, lr, state_shape, capacity, alpha, epsilon_start, epsilon_end,
                 epsilon_decay, batch_size):
        self.n_actions = n_actions
        self.gamma = gamma
        self.tau = tau
        self.lr = lr
        self.state_shape = state_shape
        self.batch_size = batch_size

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.eval_model = DQN("eval_model", self.state_shape, self.n_actions).to(self.device)
        self.target_model = DQN("target_model", self.state_shape, self.n_actions).to(self.device)
        self.loss_fn = nn.MSELoss().to(self.device)

        # self.target_model.load_state_dict(self.eval_model.state_dict())
        self.target_model.eval()
        self.optimizer = RMSprop(self.eval_model.parameters(), lr=self.lr, alpha=alpha)
        self.memory = ReplayMemory(capacity)

        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.epsilon = self.epsilon_start

        self.steps = 0

    def choose_action(self, state):
        eps_threshold = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
                        np.exp(-1. * self.steps / self.epsilon_decay)

        if np.random.random() > eps_threshold:
            with torch.no_grad():
                state = torch.unsqueeze(from_numpy(state).float().to(self.device), dim=0)
                action = self.eval_model(
                    state.permute(dims=[0, 3, 2, 1])).argmax(dim=1)[0]

        else:
            action = torch.randint(low=0, high=self.n_actions, size=(1,), device=self.device)[0]
        self.steps += 1

        return action

    def store(self, state, action, reward, next_state, done):

        state = from_numpy(state).float().to(self.device)
        reward = torch.Tensor([reward], device="cpu")
        next_state = from_numpy(next_state).float().to(self.device)
        done = torch.Tensor([done], device="cpu")

        self.memory.push(state, action.to("cpu"), reward.to("cpu"), next_state, done.to("cpu"))

    @staticmethod
    def soft_update_of_target_network(local_model, target_model, tau):
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)

    def unpack_batch(self, batch):

        batch = Transition(*zip(*batch))

        actions = tuple((map(lambda a: torch.tensor([[a]], device=self.device), batch.action)))
        rewards = tuple((map(lambda r: torch.tensor([r], device=self.device), batch.reward)))

        states = torch.cat(batch.state).to(self.device).view(512, 84, 84, 4)
        actions = torch.cat(actions).to(self.device)
        rewards = torch.cat(rewards).to(self.device)
        next_states = torch.cat(batch.next_state).view(512, 84, 84, 4)
        dones = torch.cat(batch.done)

        states = states.permute(dims=[0, 3, 2, 1])
        actions = actions.to(self.device).view((-1, 1))
        rewards = rewards.to(self.device)
        next_states = next_states.permute(dims=[0, 3, 2, 1])
        dones = dones.to(self.device)
        return states, actions, rewards, next_states, dones

    def train(self):
        if len(self.memory) < self.batch_size:
            return 0  # as no loss
        batch = self.memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones = self.unpack_batch(batch)

        x = states
        q_eval = self.eval_model(x).gather(dim=1, index=actions)
        q_next = self.target_model(next_states).detach()
        q_target = rewards + self.gamma * q_next.max(dim=1)[0]
        loss = self.loss_fn(q_eval, q_target.view((self.batch_size, 1)))

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        var = loss.detach().cpu().numpy()
        return var