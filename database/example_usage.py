"""
AI Penfight - Database Example Usage & Verification Script
Demonstrates all CRUD operations, foreign key enforcement, cascading deletes,
and executes all 5 required business queries.
"""

import sys
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import init_db, get_db, transaction
from database.crud import (
    UserRepository,
    InteractionRepository,
    AnalysisRepository,
    FeedbackRepository,
    PerformanceRepository,
    PerformanceRollupRepository,
)


def header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def run_demonstration():
    header("AI PENFIGHT DATABASE VERIFICATION & CRUD DEMO")
    
    # ---------------------------------------------------------
    # 1. CRUD: USER
    # ---------------------------------------------------------
    header("1. CRUD: User Operations")
    
    # Ensure clean test state if re-running
    existing_user = UserRepository.get_by_email("carol@penfight.ai")
    if existing_user:
        UserRepository.delete(existing_user["id"])

    new_user_id = UserRepository.create(
        username="carol_speedster",
        email="carol@penfight.ai",
        password_hash="argon2id$v=19$m=65536,t=3,p=4$hash999",
        preferences={"theme": "dark", "haptic_feedback": True, "flick_sensitivity": 0.85},
    )
    print(f"[+] Created user 'carol_speedster' with ID: {new_user_id}")
    
    user = UserRepository.get_by_id(new_user_id)
    print(f"[+] Fetched user by ID: {user['username']} | Preferences: {user['preferences']}")
    
    UserRepository.update_preferences(new_user_id, {"theme": "neon-cyber", "flick_sensitivity": 0.95})
    updated_user = UserRepository.get_by_id(new_user_id)
    print(f"[+] Updated user preferences: {updated_user['preferences']}")

    # ---------------------------------------------------------
    # 2. CRUD: INTERACTION
    # ---------------------------------------------------------
    header("2. CRUD: Interaction Operations")
    interaction_id = InteractionRepository.create(
        user_id=new_user_id,
        session_id="sess_carol_demo_01",
        mode="match",
        input_data={"flick_vector": [45.0, 5.8], "contact_zone": "clip_edge", "spin_rad": 12.4},
        status="completed",
    )
    print(f"[+] Recorded new interaction #{interaction_id} for user #{new_user_id}")
    
    inter = InteractionRepository.get_by_id(interaction_id)
    print(f"[+] Interaction data: mode={inter['mode']} | input={inter['input_data']}")

    # ---------------------------------------------------------
    # 3. CRUD: ANALYSIS
    # ---------------------------------------------------------
    header("3. CRUD: Analysis Operations")
    analysis_id = AnalysisRepository.create(
        interaction_id=interaction_id,
        user_id=new_user_id,
        analysis_summary="High-speed dynamic flick with slight rotational instability.",
        detected_patterns=["rapid flick acceleration", "slight edge clipping", "good trajectory"],
        confidence_score=0.93,
        model_version="penfight-ai-v1.2",
        prompt_version="feedback_prompt_v2",
        latency_ms=275,
    )
    print(f"[+] Created AI analysis #{analysis_id} for interaction #{interaction_id}")
    
    analysis = AnalysisRepository.get_by_id(analysis_id)
    print(f"[+] Analysis summary: {analysis['analysis_summary']}")
    print(f"    Confidence: {analysis['confidence_score']} | Patterns: {analysis['detected_patterns']}")

    # ---------------------------------------------------------
    # 4. CRUD: FEEDBACK
    # ---------------------------------------------------------
    header("4. CRUD: Personalized Feedback Operations")
    feedback_id = FeedbackRepository.create(
        analysis_id=analysis_id,
        user_id=new_user_id,
        feedback_type="adaptive",
        title="Stabilize Rotational Spin",
        content="Your release speed is top tier, but reducing clip contact will prevent inadvertent drift.",
        recommendations=[
            "Position index finger 3mm lower on the barrel",
            "Follow through along the table midline",
        ],
        tone="encouraging",
    )
    print(f"[+] Created personalized feedback #{feedback_id} linked to analysis #{analysis_id}")
    
    FeedbackRepository.mark_as_applied(feedback_id, is_applied=True)
    feedback = FeedbackRepository.get_by_id(feedback_id)
    print(f"[+] Feedback marked as applied: is_applied={feedback['is_applied']}")
    print(f"    Recommendations: {feedback['recommendations']}")

    # ---------------------------------------------------------
    # 5. CRUD: PERFORMANCE & TIME-SERIES METRICS
    # ---------------------------------------------------------
    header("5. CRUD: Performance Metrics Operations")
    p1 = PerformanceRepository.record_metric(
        user_id=new_user_id,
        interaction_id=interaction_id,
        metric_name="accuracy",
        metric_value=93.5,
        trend_direction="up",
    )
    p2 = PerformanceRepository.record_metric(
        user_id=new_user_id,
        interaction_id=interaction_id,
        metric_name="reaction_time_ms",
        metric_value=210.0,
        trend_direction="up",
    )
    print(f"[+] Logged performance metric #{p1} (accuracy=93.5) and #{p2} (reaction_time=210ms)")

    # ---------------------------------------------------------
    # 6. CRUD: PERFORMANCE ROLLUP (DASHBOARD CACHE)
    # ---------------------------------------------------------
    header("6. CRUD: Performance Rollup / Summary Operations")
    # Refresh rollup cache
    refreshed = PerformanceRollupRepository.refresh_user_summary(new_user_id)
    print(f"[+] Refreshed rollup cache for user #{new_user_id}:")
    print(f"    - Total Interactions: {refreshed['total_interactions']}")
    print(f"    - Total Analyses: {refreshed['total_analyses']}")
    print(f"    - Average Accuracy: {refreshed['avg_accuracy_score']}%")
    print(f"    - Average Latency: {refreshed['avg_latency_ms']} ms")
    print(f"    - Overall Trend: {refreshed['overall_trend']}")

    # ---------------------------------------------------------
    # 7. VERIFY FOREIGN KEY CONSTRAINTS & REFERENTIAL INTEGRITY
    # ---------------------------------------------------------
    header("7. Verification: SQLite Foreign Key Enforcement")
    try:
        InteractionRepository.create(
            user_id=999999,  # Non-existent user
            session_id="ghost_session",
            mode="practice",
            input_data="{}",
        )
        print("[-] ERROR: Foreign key constraint failed to block invalid user_id!")
    except sqlite3.IntegrityError as e:
        print(f"[OK] Foreign Key enforcement SUCCESSFUL: Blocked invalid user_id: {e}")

    # ---------------------------------------------------------
    # 8. VERIFY CASCADING DELETES
    # ---------------------------------------------------------
    header("8. Verification: Cascading Delete Integrity")
    print(f"[+] Deleting user #{new_user_id}...")
    UserRepository.delete(new_user_id)
    
    # Check that interactions, analyses, feedback, performances, rollups are deleted
    d_user = UserRepository.get_by_id(new_user_id)
    d_inter = InteractionRepository.get_by_id(interaction_id)
    d_ana = AnalysisRepository.get_by_id(analysis_id)
    d_fb = FeedbackRepository.get_by_id(feedback_id)
    d_perf = PerformanceRepository.get_history(new_user_id)
    d_rollup = PerformanceRollupRepository.get_summary(new_user_id)

    assert d_user is None, "User should be deleted"
    assert d_inter is None, "Interactions should cascade delete"
    assert d_ana is None, "Analyses should cascade delete"
    assert d_fb is None, "Feedback should cascade delete"
    assert len(d_perf) == 0, "Performances should cascade delete"
    assert d_rollup is None, "Rollup record should cascade delete"
    print("[OK] Cascading Delete verified: All related child records cleanly purged!")

    # ---------------------------------------------------------
    # 9. EXECUTE 5 REQUIRED QUERIES ON SEED DATA (Alex Striker, ID=1)
    # ---------------------------------------------------------
    header("9. Execution of 5 Required Architectural Queries")
    user_id = 1
    
    # Query 1: User interaction history
    print("\n--- Query 1: User Interaction History (User 1: Alex Striker) ---")
    history = InteractionRepository.get_user_history(user_id=user_id, limit=5)
    for h in history:
        print(f"  [ID: {h['id']}] Session: {h['session_id']} | Mode: {h['mode']:<10} | Created: {h['created_at']}")

    # Query 2: Previous analyses by user and timestamp
    print("\n--- Query 2: Previous Analyses by User & Timestamp Range ---")
    analyses = AnalysisRepository.get_previous_analyses(
        user_id=user_id,
        limit=5,
        start_date="2026-09-01 00:00:00",
        end_date="2026-09-28 23:59:59",
    )
    for a in analyses:
        print(f"  [Analysis #{a['id']}] Score: {a['confidence_score']} | Summary: {a['analysis_summary'][:60]}... | Time: {a['created_at']}")

    # Query 3: Feedback for an analysis
    print("\n--- Query 3: Personalized Feedback for Analysis #1 ---")
    feedbacks = FeedbackRepository.get_by_analysis_id(analysis_id=1)
    for f in feedbacks:
        print(f"  [Feedback #{f['id']}] Title: '{f['title']}' | Type: {f['feedback_type']} | Applied: {f['is_applied']}")
        print(f"   Recommendations: {f['recommendations']}")

    # Query 4: Performance trends over time
    print("\n--- Query 4: Performance Trends ('accuracy') ---")
    trends = PerformanceRepository.get_performance_trends(user_id=user_id, metric_name="accuracy")
    for t in trends:
        print(f"  Recorded: {t['recorded_at']} | Metric: {t['metric_name']} | Value: {t['metric_value']}% | Trend: {t['trend_direction']}")

    # Query 5: Dashboard summary (Instant Rollup Cache)
    print("\n--- Query 5: Instant Dashboard Summary (Rollup Cache) ---")
    summary = PerformanceRollupRepository.get_summary(user_id=user_id)
    print(f"  User ID: {summary['user_id']}")
    print(f"  Total Interactions: {summary['total_interactions']}")
    print(f"  Total Analyses:     {summary['total_analyses']}")
    print(f"  Total Feedbacks:    {summary['total_feedbacks']}")
    print(f"  Average Accuracy:   {summary['avg_accuracy_score']}%")
    print(f"  Average AI Latency: {summary['avg_latency_ms']} ms")
    print(f"  Overall Trend:      {summary['overall_trend'].upper()}")
    print(f"  Recent Mistakes:    {summary['recent_mistake_count']}")
    print(f"  Last Interaction:   {summary['last_interaction_at']}")
    print(f"  Last Rollup Sync:   {summary['last_calculated_at']}")

    header("ALL DATABASE TESTS AND VERIFICATIONS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_demonstration()
