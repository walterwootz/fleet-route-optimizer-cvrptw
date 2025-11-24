"""
FLEET-ONE Agent Module

Central LLM-based fleet management agent with multi-mode routing.

Components:
- agent_core: Main agent logic and mode routing
- rbac_policy: Role-based access control and conflict resolution
- tool_orchestrator: Backend service orchestration
- use_case_handlers: Playbook use case implementations
"""

from src.services.fleet_one.agent_core import (
    FleetOneAgent,
    AgentMode,
    AgentContext,
    AgentResponse,
    ModeRouter,
    get_agent
)

from src.services.fleet_one.rbac_policy import (
    Role,
    Scope,
    ConflictResolver,
    RBACEngine,
    PolicyEngine,
    get_rbac_engine,
    init_policy_engine,
    get_policy_engine
)

from src.services.fleet_one.tool_orchestrator import (
    ToolOrchestrator,
    ToolCallResult,
    ServiceType,
    init_orchestrator,
    get_orchestrator
)

from src.services.fleet_one.use_case_handlers import (
    UseCaseHandlers,
    HandlerResult,
    init_handlers,
    get_handlers
)

__all__ = [
    # Agent Core
    "FleetOneAgent",
    "AgentMode",
    "AgentContext",
    "AgentResponse",
    "ModeRouter",
    "get_agent",

    # RBAC & Policy
    "Role",
    "Scope",
    "ConflictResolver",
    "RBACEngine",
    "PolicyEngine",
    "get_rbac_engine",
    "init_policy_engine",
    "get_policy_engine",

    # Tool Orchestration
    "ToolOrchestrator",
    "ToolCallResult",
    "ServiceType",
    "init_orchestrator",
    "get_orchestrator",

    # Use Case Handlers
    "UseCaseHandlers",
    "HandlerResult",
    "init_handlers",
    "get_handlers"
]
