"""
Lab 11 — Main Entry Point (OpenAI backend)

Usage:
    python main.py              # Run all parts
    python main.py --part 1     # Part 1: Attacks
    python main.py --part 2     # Part 2: Guardrails
    python main.py --part 3     # Part 3: Testing pipeline
    python main.py --part 4     # Part 4: HITL design
"""
import sys
import asyncio
import argparse

from core.config import setup_api_key


async def part1_attacks():
    print("\n" + "=" * 60)
    print("PART 1: Attack Unprotected Agent")
    print("=" * 60)
    from agents.agent import create_unsafe_agent, test_agent
    from attacks.attacks import run_attacks, generate_ai_attacks

    agent, runner = create_unsafe_agent()
    await test_agent(agent, runner)

    print("\n--- Running manual attacks (TODO 1) ---")
    results = await run_attacks(agent, runner)

    print("\n--- Generating AI attacks (TODO 2) ---")
    ai_attacks = await generate_ai_attacks()
    return results


async def part2_guardrails():
    print("\n" + "=" * 60)
    print("PART 2: Guardrails")
    print("=" * 60)

    print("\n--- Part 2A: Input Guardrails ---")
    from guardrails.input_guardrails import (
        test_injection_detection, test_topic_filter, test_input_plugin,
    )
    test_injection_detection()
    print()
    test_topic_filter()
    print()
    await test_input_plugin()

    print("\n--- Part 2B: Output Guardrails ---")
    from guardrails.output_guardrails import test_content_filter
    test_content_filter()

    print("\n--- Part 2C: NeMo Guardrails ---")
    try:
        from guardrails.nemo_guardrails import init_nemo, test_nemo_guardrails
        init_nemo()
        await test_nemo_guardrails()
    except ImportError:
        print("NeMo Guardrails not available. Skipping Part 2C.")
    except Exception as e:
        print(f"NeMo error: {e}. Skipping Part 2C.")


async def part3_testing():
    print("\n" + "=" * 60)
    print("PART 3: Security Testing Pipeline")
    print("=" * 60)
    from testing.testing import run_comparison, print_comparison, SecurityTestPipeline
    from agents.agent import create_unsafe_agent

    print("\n--- TODO 10: Before/After Comparison ---")
    unprotected, protected = await run_comparison()
    if unprotected and protected:
        print_comparison(unprotected, protected)

    print("\n--- TODO 11: Security Test Pipeline ---")
    agent, runner = create_unsafe_agent()
    pipeline = SecurityTestPipeline(agent, runner)
    results = await pipeline.run_all()
    if results:
        pipeline.print_report(results)


def part4_hitl():
    print("\n" + "=" * 60)
    print("PART 4: Human-in-the-Loop Design")
    print("=" * 60)
    from hitl.hitl import test_confidence_router, test_hitl_points

    print("\n--- TODO 12: Confidence Router ---")
    test_confidence_router()

    print("\n--- TODO 13: HITL Decision Points ---")
    test_hitl_points()


async def main(parts=None):
    setup_api_key()
    if parts is None:
        parts = [1, 2, 3, 4]
    for part in parts:
        if part == 1:
            await part1_attacks()
        elif part == 2:
            await part2_guardrails()
        elif part == 3:
            await part3_testing()
        elif part == 4:
            part4_hitl()
    print("\n" + "=" * 60)
    print("Lab 11 complete!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lab 11: Guardrails, HITL & Responsible AI")
    parser.add_argument("--part", type=int, choices=[1, 2, 3, 4])
    args = parser.parse_args()
    asyncio.run(main(parts=[args.part] if args.part else None))
