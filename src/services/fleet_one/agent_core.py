"""
FLEET-ONE Agent Core

Central LLM-based fleet management agent with multi-mode routing.
Handles conversations in German, routes to appropriate handlers,
and orchestrates tool calls across multiple backend services.

Modes:
- FLOTTE: Fleet operations, vehicle availability
- MAINTENANCE: Maintenance planning, deadlines, ECM
- WORKSHOP: Workshop orders, repairs, transfers
- PROCUREMENT: Parts, purchasing, material
- FINANCE: Invoicing, budget, costs
- HR: Staff planning, shifts, assignments
- DOCS: Documents, certifications, reports
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
import re
from dataclasses import dataclass


class AgentMode(Enum):
    """Agent operation modes"""
    FLOTTE = "FLOTTE"
    MAINTENANCE = "MAINTENANCE"
    WORKSHOP = "WORKSHOP"
    PROCUREMENT = "PROCUREMENT"
    FINANCE = "FINANCE"
    HR = "HR"
    DOCS = "DOCS"


@dataclass
class AgentContext:
    """Conversation context"""
    user_id: str
    role: str
    session_id: str
    mode: AgentMode
    history: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class AgentResponse:
    """Agent response structure"""
    text: str  # German response to user
    mode: AgentMode
    tool_calls: List[Dict[str, Any]]
    suggestions: List[str]
    warnings: List[str]
    data: Optional[Dict[str, Any]] = None


class ModeRouter:
    """
    Routes user queries to appropriate agent mode based on keywords.

    Uses keyword matching from FLEET-ONE policy to determine intent.
    """

    # Mode keyword patterns from policy
    MODE_PATTERNS = {
        AgentMode.FLOTTE: [
            r'\b(flotte|lok|loks|lokomotiven?)\b',
            r'\b(einsatz|umlauf|verfügbarkeit)\b',
            r'\b(fahrzeug|rolling stock)\b'
        ],
        AgentMode.MAINTENANCE: [
            r'\b(wartung|instandhaltung)\b',
            r'\b(frist|fristen|deadline)\b',
            r'\b(ecm|untersuchung|hu|ep|fp)\b',
            r'\b(maßnahme|inspektion)\b'
        ],
        AgentMode.WORKSHOP: [
            r'\b(werkstatt|werkstätten?)\b',
            r'\b(auftrag|aufträge|reparatur)\b',
            r'\b(überführung|transfer)\b',
            r'\b(arbeitsauftrag|wo)\b'
        ],
        AgentMode.PROCUREMENT: [
            r'\b(teil|teile|ersatzteil)\b',
            r'\b(beschaffung|einkauf)\b',
            r'\b(bestellung|bestellen)\b',
            r'\b(material|lager|stock)\b'
        ],
        AgentMode.FINANCE: [
            r'\b(rechnung|invoice)\b',
            r'\b(budget|kosten|cost)\b',
            r'\b(controlling|finanz)\b',
            r'\b(bezahlung|payment)\b'
        ],
        AgentMode.HR: [
            r'\b(personal|personaleinsatz)\b',
            r'\b(schicht|schichten)\b',
            r'\b(fahrer|mitarbeiter|staff)\b',
            r'\b(zuführung|crew)\b'
        ],
        AgentMode.DOCS: [
            r'\b(dokument|dokumentation)\b',
            r'\b(zulassung|certification)\b',
            r'\b(bericht|report|protokoll)\b',
            r'\b(ablauf|expir|gültig)\b'
        ]
    }

    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = {
            mode: [re.compile(pattern, re.IGNORECASE)
                   for pattern in patterns]
            for mode, patterns in self.MODE_PATTERNS.items()
        }

    def detect_mode(self, query: str) -> Tuple[AgentMode, float]:
        """
        Detect most appropriate mode for query.

        Returns:
            Tuple of (mode, confidence score)
        """
        scores = {mode: 0 for mode in AgentMode}

        # Score each mode based on keyword matches
        for mode, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(query)
                scores[mode] += len(matches)

        # Get mode with highest score
        if max(scores.values()) == 0:
            # No matches - default to FLOTTE
            return AgentMode.FLOTTE, 0.0

        best_mode = max(scores.items(), key=lambda x: x[1])
        total_matches = sum(scores.values())
        confidence = best_mode[1] / total_matches if total_matches > 0 else 0.0

        return best_mode[0], confidence

    def detect_multi_mode(self, query: str, threshold: float = 0.3) -> List[AgentMode]:
        """
        Detect multiple relevant modes (for complex queries).

        Args:
            threshold: Minimum score ratio to include mode

        Returns:
            List of relevant modes, sorted by relevance
        """
        scores = {mode: 0 for mode in AgentMode}

        for mode, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(query)
                scores[mode] += len(matches)

        max_score = max(scores.values())
        if max_score == 0:
            return [AgentMode.FLOTTE]

        # Include modes above threshold
        relevant_modes = [
            mode for mode, score in scores.items()
            if score >= max_score * threshold
        ]

        # Sort by score descending
        relevant_modes.sort(key=lambda m: scores[m], reverse=True)

        return relevant_modes if relevant_modes else [AgentMode.FLOTTE]


class FleetOneAgent:
    """
    FLEET-ONE - Central fleet management agent.

    Single agent with multiple internal modes for different
    fleet management domains (maintenance, workshop, procurement, etc.)

    Features:
    - German conversational interface
    - Multi-mode routing
    - Tool orchestration across 9 backend services
    - RBAC integration
    - Policy-aware conflict resolution
    - Event sourcing integration
    """

    SYSTEM_PROMPT = """Du bist FLEET-ONE, ein zentraler Assistent für das Flottenmanagement von Streckenlokomotiven.

Ziele: Planen, Steuern, Überwachen, Nachweisen – mit Priorität auf Sicherheit, Fristen, ECM-Konformität und Kostenkontrolle.

Grundsätze:
- Nutze die bereitgestellten Tools für alle Datenabfragen/-änderungen (keine Annahmen ohne Quelle).
- Beachte Deadlines/Fristen, No-Overlap (Track/Team/Asset), Skills, Teileverfügbarkeit, Schichtfenster.
- Kennzeichne Empfehlungen vs. Fakten. Warne bei Risiken/Policy-Verstößen.
- Backend führt UTC; antworte in lokaler Zeit (Europe/Berlin) mit klaren Datums-/Zeitangaben.
- Frage nur nach, wenn Minimalinfos fehlen (keine unnötigen Rückfragen).

Stil: sachlich, präzise, lösungsorientiert; kurze Entscheidungen mit konkreten Vorschlägen
"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FLEET-ONE agent.

        Args:
            config: Agent configuration (from policy JSON)
        """
        self.config = config
        self.router = ModeRouter()
        self.version = config.get("version", "1.0.0")
        self.language = config.get("language", "de")
        self.timezone = config.get("timezone", "Europe/Berlin")

        # Session storage (in-memory for now, should be persistent)
        self.sessions: Dict[str, AgentContext] = {}

    def create_session(
        self,
        user_id: str,
        role: str,
        session_id: Optional[str] = None
    ) -> str:
        """Create new conversation session"""
        if not session_id:
            session_id = f"session-{user_id}-{int(datetime.now().timestamp())}"

        context = AgentContext(
            user_id=user_id,
            role=role,
            session_id=session_id,
            mode=AgentMode.FLOTTE,  # Default
            history=[],
            metadata={}
        )

        self.sessions[session_id] = context
        return session_id

    def process_query(
        self,
        session_id: str,
        query: str,
        force_mode: Optional[AgentMode] = None
    ) -> AgentResponse:
        """
        Process user query and generate response.

        Args:
            session_id: Conversation session ID
            query: User query (in German)
            force_mode: Override automatic mode detection

        Returns:
            AgentResponse with text, tool calls, and metadata
        """
        # Get or create session
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self.sessions[session_id]

        # Detect mode if not forced
        if force_mode:
            mode = force_mode
            confidence = 1.0
        else:
            mode, confidence = self.router.detect_mode(query)

        # Update context
        context.mode = mode
        context.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "mode": mode.value,
            "confidence": confidence
        })

        # Generate response based on mode
        # (Actual implementation will delegate to mode-specific handlers)
        response = self._generate_response(context, query)

        return response

    def _generate_response(
        self,
        context: AgentContext,
        query: str
    ) -> AgentResponse:
        """
        Generate response for query in current mode.

        This is a placeholder that will be replaced by mode-specific handlers.
        """
        mode = context.mode

        # Placeholder response
        return AgentResponse(
            text=f"FLEET-ONE ({mode.value} Modus): Anfrage verstanden. "
                 f"Die Implementierung der spezifischen Handler folgt.",
            mode=mode,
            tool_calls=[],
            suggestions=[
                "Implementierung der Mode-Handler steht noch aus",
                "Tool Orchestration wird in nächstem Schritt hinzugefügt"
            ],
            warnings=[]
        )

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session"""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id].history

    def clear_session(self, session_id: str) -> bool:
        """Clear session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class AgentMetrics:
    """Track agent performance metrics"""

    def __init__(self):
        self.queries_total = 0
        self.queries_by_mode: Dict[AgentMode, int] = {
            mode: 0 for mode in AgentMode
        }
        self.avg_response_time_ms = 0.0
        self.tool_calls_total = 0
        self.errors_total = 0

    def record_query(
        self,
        mode: AgentMode,
        response_time_ms: float,
        tool_call_count: int,
        success: bool
    ):
        """Record query metrics"""
        self.queries_total += 1
        self.queries_by_mode[mode] += 1
        self.tool_calls_total += tool_call_count

        # Update running average
        n = self.queries_total
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (n - 1) + response_time_ms) / n
        )

        if not success:
            self.errors_total += 1

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "queries_total": self.queries_total,
            "queries_by_mode": {
                mode.value: count
                for mode, count in self.queries_by_mode.items()
            },
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "tool_calls_total": self.tool_calls_total,
            "errors_total": self.errors_total,
            "success_rate": (
                (self.queries_total - self.errors_total) / self.queries_total
                if self.queries_total > 0 else 0.0
            )
        }


# Global agent instance (should be managed by dependency injection)
_agent_instance: Optional[FleetOneAgent] = None


def get_agent(config: Optional[Dict[str, Any]] = None) -> FleetOneAgent:
    """Get or create global agent instance"""
    global _agent_instance

    if _agent_instance is None:
        if config is None:
            raise ValueError("Agent not initialized. Provide config on first call.")
        _agent_instance = FleetOneAgent(config)

    return _agent_instance
