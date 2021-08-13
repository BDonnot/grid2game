import sys
import os
from grid2op.Agent import BaseAgent


def load_assistant(assistant_path, assistant_seed, env):
    """utility to load the agent"""
    # lazy loading
    res = None
    print("Loading an assistant with \"load_assistant\"")
    if assistant_path is not None:
        abs_assistant_path = os.path.abspath(assistant_path)
        if not os.path.exists(assistant_path):
            raise RuntimeError(f"Nothing found at \"{assistant_path}\"")
        if not os.path.isdir(assistant_path):
            raise RuntimeError(f"\"{assistant_path}\" should be a folder")

        if not os.path.exists(os.path.join(assistant_path, "submission")):
            raise RuntimeError(f"\"{assistant_path}\" should contain a folder named \"submission\"")
        sys.path.append(abs_assistant_path)
        try:
            from submission import make_agent
            res = make_agent(env, os.path.join(abs_assistant_path, "submission"))
            assert isinstance(res, BaseAgent), "your assistant you be a grid2op.Agent.BaseAgent"
        except Exception as exc_:
            print("Impossible to load your agent. Make sure to include properly the \"make_agent\" function.")
            raise
        print("assistant loaded in \"load_assistant\"")
        res.seed(int(assistant_seed))
    return res

