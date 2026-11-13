import asyncio

from app import cli


def test_cli_disposes_engine_before_event_loop_closes(monkeypatch) -> None:
    loops = []

    async def fake_create_initial_admin() -> None:
        loops.append(asyncio.get_running_loop())

    async def fake_dispose(_engine) -> None:
        loops.append(asyncio.get_running_loop())

    monkeypatch.setattr(cli, "create_initial_admin", fake_create_initial_admin)
    monkeypatch.setattr(type(cli.engine), "dispose", fake_dispose)

    asyncio.run(cli._run_command("create-admin"))

    assert len(loops) == 2
    assert loops[0] is loops[1]
