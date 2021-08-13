from .my_agent import MyAgent


def make_agent(env, path):
    res = MyAgent(env.action_space)
    return res
