from typing import Callable, Optional

from .models import User

# Holds the name, and link of an action
RemoteAction = Optional[tuple[str, str]]
# Generates a UserAction when called with current_user and target_user
RemoteActionGenerator = Callable[[User, Str], RemoteAction]

remote_action_generators: list[RemoteActionGenerator] = []


def register(remote_action_generator: RemoteActionGenerator):
    remote_action_generators.append(remote_action_generator)
