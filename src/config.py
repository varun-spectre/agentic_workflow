from dataclasses import dataclass, field
from typing import List, Callable, Dict

@dataclass
class AgentConfig:
    max_retries: int = 3
    max_steps: int = 10
    temperature: float = 0.0
    tools_allowed: List[str] = field(default_factory=lambda: ["code_executor"])
    tool_registry: Dict[str, Callable] = field(default_factory=dict)

    def register_tool(self, name: str, fn: Callable):
        """Register a tool and allow it if not already listed"""
        self.tool_registry[name] = fn
        if name not in self.tools_allowed:
            self.tools_allowed.append(name)

    def use_tool(self, name: str, *args, **kwargs):
        """Safely use a registered tool"""
        if name in self.tools_allowed and name in self.tool_registry:
            return self.tool_registry[name](*args, **kwargs)
        else:
            raise Exception(f"Tool '{name}' is not allowed or not registered.")
