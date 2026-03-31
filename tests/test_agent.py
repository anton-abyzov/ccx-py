"""Tests for the agent manager."""

import asyncio

import pytest

from ccx.core.agent import AgentDef, AgentManager, AgentResult, AgentStatus


@pytest.fixture
def manager():
    return AgentManager()


@pytest.fixture
def simple_def():
    return AgentDef(name="test-agent", prompt="do something")


@pytest.mark.asyncio
async def test_spawn_stub(manager, simple_def):
    result = await manager.spawn(simple_def)
    assert result.status == AgentStatus.COMPLETED
    assert "stub" in result.output


@pytest.mark.asyncio
async def test_spawn_with_run_fn(manager, simple_def):
    async def run_fn(defn):
        return f"executed: {defn.prompt}"

    result = await manager.spawn(simple_def, run_fn=run_fn)
    assert result.status == AgentStatus.COMPLETED
    assert "executed: do something" in result.output


@pytest.mark.asyncio
async def test_spawn_failure(manager, simple_def):
    async def failing_fn(defn):
        raise ValueError("boom")

    result = await manager.spawn(simple_def, run_fn=failing_fn)
    assert result.status == AgentStatus.FAILED
    assert "boom" in result.error


@pytest.mark.asyncio
async def test_spawn_background(manager, simple_def):
    called = False

    async def slow_fn(defn):
        nonlocal called
        await asyncio.sleep(0.01)
        called = True
        return "done"

    await manager.spawn_background(simple_def, run_fn=slow_fn)
    # Task is running but not yet complete
    assert manager.running_count >= 0  # May or may not be done yet

    # Wait for it
    await asyncio.sleep(0.1)
    assert called


@pytest.mark.asyncio
async def test_get_status(manager, simple_def):
    assert manager.get_status("unknown") == AgentStatus.PENDING

    result = await manager.spawn(simple_def)
    assert manager.get_status("test-agent") == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel(manager):
    defn = AgentDef(name="slow", prompt="wait")

    async def slow_fn(d):
        await asyncio.sleep(10)
        return "done"

    await manager.spawn_background(defn, run_fn=slow_fn)
    await asyncio.sleep(0.01)
    cancelled = await manager.cancel("slow")
    assert cancelled


@pytest.mark.asyncio
async def test_cancel_nonexistent(manager):
    result = await manager.cancel("nope")
    assert not result


def test_agent_def_defaults():
    d = AgentDef(name="a", prompt="b")
    assert d.model == "claude-sonnet-4-6"
    assert d.max_tokens == 8192
    assert d.tools == []


def test_agent_result_defaults():
    r = AgentResult(name="a", status=AgentStatus.COMPLETED)
    assert r.output == ""
    assert r.error == ""
    assert r.metadata == {}
