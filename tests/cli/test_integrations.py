from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from app.cli.__main__ import cli


def test_integrations_show_redacts_api_token() -> None:
    runner = CliRunner()

    with patch(
        "app.integrations.cli.get_integration",
        return_value={
            "id": "vercel-1234",
            "service": "vercel",
            "status": "active",
            "credentials": {
                "api_token": "vcp_sensitive_token_value",
                "team_id": "team_123",
            },
        },
    ):
        result = runner.invoke(cli, ["integrations", "show", "vercel"])

    assert result.exit_code == 0
    assert "vcp_****" in result.output
    assert "vcp_sensitive_token_value" not in result.output


def test_integrations_setup_accepts_github() -> None:
    runner = CliRunner()

    with (
        patch("app.cli.commands.integrations.capture_integration_setup_started"),
        patch("app.cli.commands.integrations.capture_integration_setup_completed"),
        patch("app.integrations.cli.cmd_setup") as mock_setup,
    ):
        result = runner.invoke(cli, ["integrations", "setup", "github"])

    assert result.exit_code == 0
    mock_setup.assert_called_once_with("github")


def test_integrations_verify_accepts_github() -> None:
    runner = CliRunner()

    with (
        patch("app.cli.commands.integrations.capture_integration_verified"),
        patch("app.integrations.cli.cmd_verify") as mock_verify,
    ):
        result = runner.invoke(cli, ["integrations", "verify", "github"])

    assert result.exit_code == 0
    mock_verify.assert_called_once_with("github", send_slack_test=False)


def test_integrations_vercel_dispatches_browser() -> None:
    runner = CliRunner()

    with patch("app.integrations.vercel_incidents.cmd_vercel_incidents") as mock_browser:
        result = runner.invoke(cli, ["integrations", "vercel", "--limit", "5"])

    assert result.exit_code == 0
    mock_browser.assert_called_once_with(limit=5)
