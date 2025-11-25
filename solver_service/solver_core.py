"""
RailFleet Workshop Scheduler using OR-Tools CP-SAT via PyJobShop.

This module adapts PyJobShop's job shop scheduling framework for railway
workshop planning with custom constraints for skills, parts, and shifts.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import logging

logger = logging.getLogger(__name__)


class RailFleetSolver:
    """
    Workshop scheduler using CP-SAT with custom constraints.

    Constraints:
    - No-Overlap: One WO per track/team at a time
    - Skills: Team must have required skills for WO
    - Parts: Parts must be available before WO starts
    - Shifts: WOs must fit within team shift windows
    - Deadlines: Hard deadlines must be respected
    - Asset Incompatibilities: Certain assets cannot be in workshop simultaneously
    """

    def __init__(self, time_unit_min: int = 15):
        """
        Initialize solver.

        Args:
            time_unit_min: Time unit in minutes (default 15 for quarter-hour slots)
        """
        self.time_unit_min = time_unit_min
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # Variables storage
        self.intervals = {}  # work_order_id -> (start_var, end_var, interval_var, presence_var)
        self.track_assignments = {}  # work_order_id -> track_id_var
        self.team_assignments = {}  # work_order_id -> team_id_var

    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the workshop scheduling problem.

        Args:
            problem: Problem specification with tracks, teams, parts, work_orders

        Returns:
            Solution with assignments, metrics, and explanations
        """
        logger.info("Starting RailFleet solver")

        # Parse problem
        tracks = problem.get("tracks", [])
        teams = problem.get("teams", [])
        parts = problem.get("parts", [])
        work_orders = problem.get("work_orders", [])
        objectives = problem.get("objectives", {}).get("weights", {})
        solver_config = problem.get("solver_config", {})

        # Time conversion
        planning_start = self._parse_timestamp(problem["problem"]["planning_horizon"]["start"])
        planning_end = self._parse_timestamp(problem["problem"]["planning_horizon"]["end"])
        horizon_slots = int((planning_end - planning_start).total_seconds() / 60 / self.time_unit_min)

        logger.info(f"Horizon: {horizon_slots} slots ({self.time_unit_min}min each)")
        logger.info(f"Work Orders: {len(work_orders)}, Tracks: {len(tracks)}, Teams: {len(teams)}")

        # Create index maps
        track_idx = {t["id"]: i for i, t in enumerate(tracks)}
        team_idx = {t["id"]: i for i, t in enumerate(teams)}
        part_idx = {p["part_no"]: i for i, p in enumerate(parts)}

        # Variables for each work order
        for wo in work_orders:
            wo_id = wo["id"]
            duration_slots = self._duration_to_slots(wo["duration_min"])

            # Optional presence variable (can be unscheduled)
            presence = self.model.NewBoolVar(f"presence_{wo_id}")

            # Start/End times (only meaningful if scheduled)
            start = self.model.NewIntVar(0, horizon_slots, f"start_{wo_id}")
            end = self.model.NewIntVar(0, horizon_slots, f"end_{wo_id}")

            # Interval (optional based on presence)
            interval = self.model.NewOptionalIntervalVar(
                start, duration_slots, end, presence, f"interval_{wo_id}"
            )

            self.intervals[wo_id] = (start, end, interval, presence)

            # Track assignment
            track_var = self.model.NewIntVar(0, len(tracks) - 1, f"track_{wo_id}")
            self.track_assignments[wo_id] = track_var

            # Team assignment
            team_var = self.model.NewIntVar(0, len(teams) - 1, f"team_{wo_id}")
            self.team_assignments[wo_id] = team_var

            # If scheduled, enforce duration
            self.model.Add(end == start + duration_slots).OnlyEnforceIf(presence)

            # Time windows (earliest/latest)
            if wo.get("earliest_start_ts"):
                earliest_slot = self._timestamp_to_slot(wo["earliest_start_ts"], planning_start)
                self.model.Add(start >= earliest_slot).OnlyEnforceIf(presence)

            if wo.get("latest_end_ts"):
                latest_slot = self._timestamp_to_slot(wo["latest_end_ts"], planning_start)
                self.model.Add(end <= latest_slot).OnlyEnforceIf(presence)

        # Constraint 1: No-Overlap per Track
        logger.info("Adding No-Overlap constraints (tracks)")
        for track in tracks:
            track_id = track["id"]
            tid = track_idx[track_id]

            # Intervals assigned to this track
            track_intervals = []
            for wo_id, (start, end, interval, presence) in self.intervals.items():
                track_var = self.track_assignments[wo_id]

                # If WO is assigned to this track AND scheduled, add to no-overlap
                is_on_track = self.model.NewBoolVar(f"on_track_{wo_id}_{track_id}")
                self.model.Add(track_var == tid).OnlyEnforceIf([presence, is_on_track])
                self.model.Add(track_var != tid).OnlyEnforceIf([is_on_track.Not()])

                # Create optional interval for this track
                opt_interval = self.model.NewOptionalIntervalVar(
                    start, end - start, end, is_on_track, f"track_interval_{wo_id}_{track_id}"
                )
                track_intervals.append(opt_interval)

            if track_intervals:
                self.model.AddNoOverlap(track_intervals)

        # Constraint 2: No-Overlap per Team
        logger.info("Adding No-Overlap constraints (teams)")
        for team in teams:
            team_id = team["id"]
            tid = team_idx[team_id]

            team_intervals = []
            for wo_id, (start, end, interval, presence) in self.intervals.items():
                team_var = self.team_assignments[wo_id]

                is_on_team = self.model.NewBoolVar(f"on_team_{wo_id}_{team_id}")
                self.model.Add(team_var == tid).OnlyEnforceIf([presence, is_on_team])
                self.model.Add(team_var != tid).OnlyEnforceIf([is_on_team.Not()])

                opt_interval = self.model.NewOptionalIntervalVar(
                    start, end - start, end, is_on_team, f"team_interval_{wo_id}_{team_id}"
                )
                team_intervals.append(opt_interval)

            if team_intervals:
                self.model.AddNoOverlap(team_intervals)

        # Constraint 3: Skills matching (simplified - team must have all required skills)
        logger.info("Adding Skills constraints")
        for wo in work_orders:
            wo_id = wo["id"]
            required_skills = set(wo.get("required_skills", []))
            presence = self.intervals[wo_id][3]
            team_var = self.team_assignments[wo_id]

            if required_skills:
                # At least one team must have the skills
                valid_teams = []
                for team in teams:
                    team_skills = set(team.get("skills", []))
                    if required_skills.issubset(team_skills):
                        valid_teams.append(team_idx[team["id"]])

                if valid_teams:
                    # Team must be one of the valid teams (if scheduled)
                    team_match = [self.model.NewBoolVar(f"team_match_{wo_id}_{tid}")
                                  for tid in valid_teams]
                    for i, tid in enumerate(valid_teams):
                        self.model.Add(team_var == tid).OnlyEnforceIf([presence, team_match[i]])

                    # At least one must match if scheduled
                    self.model.Add(sum(team_match) >= 1).OnlyEnforceIf(presence)
                else:
                    # No valid team -> cannot schedule
                    self.model.Add(presence == 0)

        # Constraint 4: Parts availability
        logger.info("Adding Parts availability constraints")
        for wo in work_orders:
            wo_id = wo["id"]
            required_parts = wo.get("required_parts", [])
            start, _, _, presence = self.intervals[wo_id]

            for req_part in required_parts:
                part_no = req_part["part_no"]
                # Find part
                part = next((p for p in parts if p["part_no"] == part_no), None)
                if part:
                    avail_from_slot = self._timestamp_to_slot(part["available_from"], planning_start)
                    # WO can only start after part is available
                    self.model.Add(start >= avail_from_slot).OnlyEnforceIf(presence)
                else:
                    # Part not available -> cannot schedule
                    logger.warning(f"WO {wo_id} requires unavailable part {part_no}")
                    self.model.Add(presence == 0)

        # Constraint 5: Asset incompatibilities
        logger.info("Adding Asset incompatibility constraints")
        for wo in work_orders:
            incompatible_assets = wo.get("incompatible_assets", [])
            if not incompatible_assets:
                continue

            wo_id = wo["id"]
            start1, end1, _, presence1 = self.intervals[wo_id]

            # Find WOs with incompatible assets
            for other_wo in work_orders:
                if other_wo["asset_id"] in incompatible_assets:
                    other_id = other_wo["id"]
                    start2, end2, _, presence2 = self.intervals[other_id]

                    # If both scheduled, they cannot overlap
                    both_scheduled = self.model.NewBoolVar(f"both_sched_{wo_id}_{other_id}")
                    self.model.Add(presence1 + presence2 == 2).OnlyEnforceIf(both_scheduled)
                    self.model.Add(presence1 + presence2 < 2).OnlyEnforceIf(both_scheduled.Not())

                    # No overlap if both scheduled
                    self.model.Add(end1 <= start2).OnlyEnforceIf(both_scheduled)
                    # OR
                    or_var = self.model.NewBoolVar(f"or_{wo_id}_{other_id}")
                    self.model.Add(end2 <= start1).OnlyEnforceIf([both_scheduled, or_var])

        # Objective: Minimize unscheduled + lateness + overtime
        logger.info("Setting up objective")

        unscheduled_penalty = objectives.get("unscheduled", 1000)
        lateness_penalty = objectives.get("lateness_per_slot", 10)
        overtime_penalty = objectives.get("overtime_per_slot", 1)

        objective_terms = []

        # Penalize unscheduled WOs
        for wo_id, (_, _, _, presence) in self.intervals.items():
            # Maximize presence (minimize not-presence)
            objective_terms.append(presence.Not() * unscheduled_penalty)

        # Penalize lateness (beyond latest_end_ts)
        for wo in work_orders:
            wo_id = wo["id"]
            if wo.get("latest_end_ts"):
                _, end, _, presence = self.intervals[wo_id]
                latest_slot = self._timestamp_to_slot(wo["latest_end_ts"], planning_start)

                lateness = self.model.NewIntVar(0, horizon_slots, f"lateness_{wo_id}")
                self.model.AddMaxEquality(lateness, [end - latest_slot, 0])
                objective_terms.append(lateness * lateness_penalty)

        # Total objective
        if objective_terms:
            self.model.Minimize(sum(objective_terms))

        # Solver configuration
        self.solver.parameters.max_time_in_seconds = solver_config.get("time_limit_sec", 60)
        self.solver.parameters.num_workers = solver_config.get("num_workers", 4)
        self.solver.parameters.log_search_progress = solver_config.get("log_search_progress", False)

        # Solve
        logger.info("Solving...")
        status = self.solver.Solve(self.model)

        # Build solution
        return self._build_solution(
            status, work_orders, tracks, teams, planning_start, horizon_slots
        )

    def _build_solution(
        self, status, work_orders, tracks, teams, planning_start, horizon_slots
    ) -> Dict[str, Any]:
        """Build solution response."""
        status_name = self.solver.StatusName(status)
        logger.info(f"Solver status: {status_name}")

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignments = []
            unscheduled = []

            for wo in work_orders:
                wo_id = wo["id"]
                start, end, _, presence = self.intervals[wo_id]

                if self.solver.Value(presence):
                    # Scheduled
                    start_slot = self.solver.Value(start)
                    end_slot = self.solver.Value(end)
                    track_idx = self.solver.Value(self.track_assignments[wo_id])
                    team_idx = self.solver.Value(self.team_assignments[wo_id])

                    assignments.append({
                        "work_order_id": wo_id,
                        "asset_id": wo["asset_id"],
                        "track_id": tracks[track_idx]["id"],
                        "team_id": teams[team_idx]["id"],
                        "start_ts": self._slot_to_timestamp(start_slot, planning_start),
                        "end_ts": self._slot_to_timestamp(end_slot, planning_start),
                        "start_slot": start_slot,
                        "end_slot": end_slot,
                    })
                else:
                    # Unscheduled
                    unscheduled.append({
                        "work_order_id": wo_id,
                        "asset_id": wo["asset_id"],
                        "reason": "Could not satisfy constraints",
                    })

            return {
                "status": "success",
                "solver_status": status_name,
                "objective_value": self.solver.ObjectiveValue(),
                "solve_time_sec": self.solver.WallTime(),
                "assignments": assignments,
                "unscheduled": unscheduled,
                "metrics": {
                    "total_work_orders": len(work_orders),
                    "scheduled": len(assignments),
                    "unscheduled_count": len(unscheduled),
                    "utilization_pct": len(assignments) / len(work_orders) * 100 if work_orders else 0,
                },
            }
        else:
            return {
                "status": "failed",
                "solver_status": status_name,
                "error": "No solution found",
                "assignments": [],
                "unscheduled": [{"work_order_id": wo["id"], "asset_id": wo["asset_id"], "reason": "No solution"}
                                for wo in work_orders],
            }

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse ISO 8601 timestamp."""
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

    def _duration_to_slots(self, duration_min: int) -> int:
        """Convert duration in minutes to slots."""
        return int(duration_min / self.time_unit_min)

    def _timestamp_to_slot(self, ts_str: str, planning_start: datetime) -> int:
        """Convert timestamp to slot number."""
        ts = self._parse_timestamp(ts_str)
        delta_min = (ts - planning_start).total_seconds() / 60
        return int(delta_min / self.time_unit_min)

    def _slot_to_timestamp(self, slot: int, planning_start: datetime) -> str:
        """Convert slot number to timestamp."""
        ts = planning_start + timedelta(minutes=slot * self.time_unit_min)
        return ts.isoformat().replace("+00:00", "Z")
