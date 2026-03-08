"""Unit tests for scripts/claude_usage.py"""
import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import claude_usage as cu  # noqa: E402


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class TestFmtTokens(unittest.TestCase):
    def test_below_thousand(self):
        self.assertEqual(cu.fmt_tokens(0), "0")
        self.assertEqual(cu.fmt_tokens(999), "999")

    def test_thousands(self):
        self.assertEqual(cu.fmt_tokens(1_000), "1.0K")
        self.assertEqual(cu.fmt_tokens(38_500), "38.5K")

    def test_millions(self):
        self.assertEqual(cu.fmt_tokens(1_000_000), "1.0M")
        self.assertEqual(cu.fmt_tokens(24_600_000), "24.6M")


class TestFmtCost(unittest.TestCase):
    def test_small(self):
        self.assertEqual(cu.fmt_cost(0.001), "$0.001")
        self.assertEqual(cu.fmt_cost(9.999), "$9.999")

    def test_medium(self):
        self.assertEqual(cu.fmt_cost(14.21), "$14.21")
        self.assertEqual(cu.fmt_cost(10.0), "$10.00")

    def test_large(self):
        self.assertEqual(cu.fmt_cost(100.0), "$100.0")
        self.assertEqual(cu.fmt_cost(200.5), "$200.5")


class TestFmtPct(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(cu.fmt_pct(0.0), "0%")

    def test_full(self):
        self.assertEqual(cu.fmt_pct(1.0), "100%")

    def test_mid(self):
        self.assertEqual(cu.fmt_pct(0.78), "78%")
        self.assertEqual(cu.fmt_pct(0.84), "84%")


class TestPctBar(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(cu.pct_bar(0.0), "........")

    def test_full(self):
        self.assertEqual(cu.pct_bar(1.0), "XXXXXXXX")

    def test_three_quarters(self):
        self.assertEqual(cu.pct_bar(0.75), "XXXXXX..")

    def test_custom_width(self):
        self.assertEqual(cu.pct_bar(0.5, width=4), "XX..")


class TestStatusInd(unittest.TestCase):
    def test_denied(self):
        self.assertEqual(cu.status_ind("denied"), "X")
        self.assertEqual(cu.status_ind("blocked"), "X")

    def test_warning(self):
        self.assertEqual(cu.status_ind("allowed_warning"), "!")

    def test_allowed(self):
        self.assertEqual(cu.status_ind("allowed"), "")
        self.assertEqual(cu.status_ind(""), "")


class TestFmtAge(unittest.TestCase):
    _NOW = 1_000_000.0

    def test_no_data(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_age(None), " [--]")
            self.assertEqual(cu.fmt_age(0), " [--]")

    def test_fresh(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_age(self._NOW - 60), "")
            self.assertEqual(cu.fmt_age(self._NOW - 119), "")

    def test_minutes(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_age(self._NOW - 300), " [5m ago]")
            self.assertEqual(cu.fmt_age(self._NOW - 3599), " [59m ago]")

    def test_hours(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_age(self._NOW - 3600), " [1h ago]")
            self.assertEqual(cu.fmt_age(self._NOW - 7200), " [2h ago]")

    def test_days(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_age(self._NOW - 86400), " [1d ago]")


class TestFmtReset(unittest.TestCase):
    _NOW = 1_000_000.0

    def test_hours_and_minutes(self):
        # 2h47m = 167 min = 10020 sec
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_reset(self._NOW + 10_020), "2h47m")

    def test_zero_minutes(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_reset(self._NOW + 3600), "1h00m")

    def test_days(self):
        with patch("time.time", return_value=self._NOW):
            result = cu.fmt_reset(self._NOW + 86400 * 4.3)
            self.assertIn("d", result)

    def test_past_returns_zero(self):
        with patch("time.time", return_value=self._NOW):
            self.assertEqual(cu.fmt_reset(self._NOW - 100), "0h00m")


# ---------------------------------------------------------------------------
# Aggregation and cost
# ---------------------------------------------------------------------------

class TestAggregate(unittest.TestCase):
    @staticmethod
    def _rec(hours_ago, inp=100, out=50, cr=0, cw=0):
        dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        usage = {
            "input_tokens": inp,
            "output_tokens": out,
            "cache_read_input_tokens": cr,
            "cache_creation_input_tokens": cw,
        }
        return (dt, usage)

    def test_all_within_window(self):
        records = [self._rec(1), self._rec(2), self._rec(3)]
        since = datetime.now(timezone.utc) - timedelta(hours=5)
        result = cu.aggregate(records, since)
        self.assertEqual(result["records"], 3)
        self.assertEqual(result["input"], 300)
        self.assertEqual(result["output"], 150)

    def test_partial_window(self):
        records = [self._rec(1), self._rec(10)]  # 10h ago is outside 5h window
        since = datetime.now(timezone.utc) - timedelta(hours=5)
        result = cu.aggregate(records, since)
        self.assertEqual(result["records"], 1)
        self.assertEqual(result["input"], 100)

    def test_empty(self):
        since = datetime.now(timezone.utc) - timedelta(hours=5)
        result = cu.aggregate([], since)
        self.assertEqual(result["input"], 0)
        self.assertEqual(result["records"], 0)

    def test_cache_tokens(self):
        records = [self._rec(1, inp=0, out=0, cr=1000, cw=2000)]
        since = datetime.now(timezone.utc) - timedelta(hours=5)
        result = cu.aggregate(records, since)
        self.assertEqual(result["cache_read"], 1000)
        self.assertEqual(result["cache_create"], 2000)


class TestCalcCost(unittest.TestCase):
    def test_input_only(self):
        # 1M input tokens at $3.00/M
        t = {"input": 1_000_000, "output": 0, "cache_read": 0, "cache_create": 0}
        self.assertAlmostEqual(cu.calc_cost(t), 3.0, places=5)

    def test_output_only(self):
        # 1M output tokens at $15.00/M
        t = {"input": 0, "output": 1_000_000, "cache_read": 0, "cache_create": 0}
        self.assertAlmostEqual(cu.calc_cost(t), 15.0, places=5)

    def test_combined(self):
        t = {
            "input": 1_000_000,       # $3.00
            "output": 1_000_000,      # $15.00
            "cache_read": 1_000_000,  # $0.30
            "cache_create": 1_000_000, # $3.75
        }
        self.assertAlmostEqual(cu.calc_cost(t), 22.05, places=5)

    def test_zero(self):
        t = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
        self.assertEqual(cu.calc_cost(t), 0.0)


# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------

class TestCacheIO(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.json")
            with patch.object(cu, "CACHE_FILE", cache_path):
                data = {"fetched_at": 12345.0, "util_5h": 0.78, "util_7d": 0.84}
                cu.save_cache(data)
                loaded = cu.load_cache()
                self.assertIsNotNone(loaded)
                self.assertAlmostEqual(loaded["util_5h"], 0.78)
                self.assertEqual(loaded["fetched_at"], 12345.0)

    def test_load_missing_returns_none(self):
        with patch.object(cu, "CACHE_FILE", "/nonexistent/cache.json"):
            self.assertIsNone(cu.load_cache())

    def test_save_bad_path_does_not_raise(self):
        with patch.object(cu, "CACHE_FILE", "/nonexistent/path/cache.json"):
            cu.save_cache({"test": 1})  # must not raise


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettings(unittest.TestCase):
    def test_defaults_when_missing(self):
        with patch.object(cu, "SETTINGS_FILE", "/nonexistent"):
            s = cu.load_settings()
            self.assertFalse(s["realtime"])
            self.assertEqual(s["cache_ttl"], 300)

    def test_override_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"realtime": True, "cache_ttl": 60}, f)
            fname = f.name
        try:
            with patch.object(cu, "SETTINGS_FILE", fname):
                s = cu.load_settings()
                self.assertTrue(s["realtime"])
                self.assertEqual(s["cache_ttl"], 60)
        finally:
            os.unlink(fname)

    def test_partial_override_merges_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"realtime": True}, f)
            fname = f.name
        try:
            with patch.object(cu, "SETTINGS_FILE", fname):
                s = cu.load_settings()
                self.assertTrue(s["realtime"])
                self.assertEqual(s["cache_ttl"], 300)  # default preserved
        finally:
            os.unlink(fname)


# ---------------------------------------------------------------------------
# Display mode toggle
# ---------------------------------------------------------------------------

class TestDisplayMode(unittest.TestCase):
    def test_default_is_percent(self):
        with patch.object(cu, "MODE_FILE", "/nonexistent"):
            self.assertEqual(cu.get_display_mode(), "percent")

    def test_toggle_percent_to_cost(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("percent")
            fname = f.name
        try:
            with patch.object(cu, "MODE_FILE", fname):
                self.assertEqual(cu.toggle_display_mode(), "cost")
                self.assertEqual(cu.get_display_mode(), "cost")
        finally:
            os.unlink(fname)

    def test_toggle_cost_to_percent(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("cost")
            fname = f.name
        try:
            with patch.object(cu, "MODE_FILE", fname):
                self.assertEqual(cu.toggle_display_mode(), "percent")
        finally:
            os.unlink(fname)


# ---------------------------------------------------------------------------
# Hook management
# ---------------------------------------------------------------------------

class TestInstallHook(unittest.TestCase):
    def _tmp_settings(self, content=None):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(content or {}, f)
            return f.name

    def test_install_adds_hook(self):
        fname = self._tmp_settings()
        try:
            with patch.object(cu, "CLAUDE_SETTINGS", fname):
                cu.install_hook()
                with open(fname) as f:
                    s = json.load(f)
                commands = [
                    h["command"]
                    for entry in s["hooks"]["Stop"]
                    for h in entry["hooks"]
                ]
                self.assertTrue(any("claude-usage" in c for c in commands))
        finally:
            os.unlink(fname)

    def test_install_is_idempotent(self):
        fname = self._tmp_settings()
        try:
            with patch.object(cu, "CLAUDE_SETTINGS", fname):
                cu.install_hook()
                cu.install_hook()  # second call should be a no-op
                with open(fname) as f:
                    s = json.load(f)
                self.assertEqual(len(s["hooks"]["Stop"]), 1)
        finally:
            os.unlink(fname)

    def test_install_preserves_existing_hooks(self):
        existing = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "other-tool"}]}]}}
        fname = self._tmp_settings(existing)
        try:
            with patch.object(cu, "CLAUDE_SETTINGS", fname):
                cu.install_hook()
                with open(fname) as f:
                    s = json.load(f)
                self.assertEqual(len(s["hooks"]["Stop"]), 2)
        finally:
            os.unlink(fname)


class TestUninstallHook(unittest.TestCase):
    def test_removes_hook(self):
        initial = {
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "claude-usage --refresh >/dev/null 2>&1"}]}]
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial, f)
            fname = f.name
        try:
            with patch.object(cu, "CLAUDE_SETTINGS", fname):
                cu.uninstall_hook()
                with open(fname) as f:
                    s = json.load(f)
                # hooks key removed entirely when empty
                self.assertNotIn("hooks", s)
        finally:
            os.unlink(fname)

    def test_missing_file_does_not_raise(self):
        with patch.object(cu, "CLAUDE_SETTINGS", "/nonexistent/settings.json"):
            cu.uninstall_hook()  # must not raise

    def test_no_hook_to_remove(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            fname = f.name
        try:
            with patch.object(cu, "CLAUDE_SETTINGS", fname):
                cu.uninstall_hook()  # must not raise
        finally:
            os.unlink(fname)


# ---------------------------------------------------------------------------
# Short output formatters
# ---------------------------------------------------------------------------

class TestHas7dLimit(unittest.TestCase):
    def test_has_7d_when_reset_nonzero(self):
        rl = {"reset_7d": 1234, "util_7d": 0.0}
        self.assertTrue(cu.has_7d_limit(rl))

    def test_has_7d_when_util_nonzero(self):
        rl = {"reset_7d": 0, "util_7d": 0.5}
        self.assertTrue(cu.has_7d_limit(rl))

    def test_no_7d_when_both_zero(self):
        rl = {"reset_7d": 0, "util_7d": 0.0}
        self.assertFalse(cu.has_7d_limit(rl))

    def test_no_7d_when_keys_missing(self):
        rl = {}
        self.assertFalse(cu.has_7d_limit(rl))


class TestDetectProvider(unittest.TestCase):
    def test_auto_with_oauth_returns_anthropic(self):
        creds = {"claudeAiOauth": {"accessToken": "tok123"}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(creds, f)
            fname = f.name
        try:
            with patch.object(cu, "CREDENTIALS_FILE", fname):
                self.assertEqual(cu.detect_provider({"provider": "auto"}), "anthropic")
        finally:
            os.unlink(fname)

    def test_auto_without_credentials_file_returns_other(self):
        with patch.object(cu, "CREDENTIALS_FILE", "/nonexistent/creds.json"):
            self.assertEqual(cu.detect_provider({"provider": "auto"}), "other")

    def test_auto_with_no_oauth_key_returns_other(self):
        creds = {"someOtherKey": {}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(creds, f)
            fname = f.name
        try:
            with patch.object(cu, "CREDENTIALS_FILE", fname):
                self.assertEqual(cu.detect_provider({"provider": "auto"}), "other")
        finally:
            os.unlink(fname)

    def test_override_anthropic(self):
        with patch.object(cu, "CREDENTIALS_FILE", "/nonexistent/creds.json"):
            self.assertEqual(cu.detect_provider({"provider": "anthropic"}), "anthropic")

    def test_override_bedrock_returns_other(self):
        self.assertEqual(cu.detect_provider({"provider": "bedrock"}), "other")

    def test_override_other(self):
        self.assertEqual(cu.detect_provider({"provider": "other"}), "other")


class TestShortPercent(unittest.TestCase):
    _NOW = 1_000_000.0

    def _rl(self, u5=0.78, u7=0.84, s5="allowed", s7="allowed_warning",
            age_offset=-10, reset5_offset=10_020, reset7_offset=345_600):
        return {
            "fetched_at": self._NOW + age_offset,
            "util_5h": u5,
            "util_7d": u7,
            "reset_5h": int(self._NOW) + reset5_offset,
            "reset_7d": int(self._NOW) + reset7_offset,
            "status_5h": s5,
            "status_7d": s7,
        }

    def _rl_5h_only(self, u5=0.78, s5="allowed", age_offset=-10, reset5_offset=10_020):
        """Rate-limit data with no 7d limit (e.g. 5h-only plan)."""
        return {
            "fetched_at": self._NOW + age_offset,
            "util_5h": u5,
            "util_7d": 0.0,
            "reset_5h": int(self._NOW) + reset5_offset,
            "reset_7d": 0,
            "status_5h": s5,
            "status_7d": "",
        }

    def test_basic_output(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl())
            self.assertIn("78%", out)
            self.assertIn("84%", out)

    def test_warning_indicator(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl(s7="allowed_warning"))
            self.assertIn("!", out)

    def test_denied_indicator(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl(s5="denied", s7="denied", u5=1.0, u7=1.0))
            self.assertIn("X", out)

    def test_stale_age_shown(self):
        with patch("time.time", return_value=self._NOW):
            # fetched 10 minutes ago → "[10m ago]"
            out = cu.short_percent(self._rl(age_offset=-600))
            self.assertIn("ago]", out)

    def test_fresh_no_age(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl(age_offset=-10))
            self.assertNotIn("ago", out)

    def test_5h_only_plan_no_7d_in_output(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl_5h_only())
            self.assertIn("5h:", out)
            self.assertNotIn("7d:", out)

    def test_5h_only_plan_shows_utilization(self):
        with patch("time.time", return_value=self._NOW):
            out = cu.short_percent(self._rl_5h_only(u5=0.55))
            self.assertIn("55%", out)


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------

class TestVersion(unittest.TestCase):
    def test_version_constant_is_string(self):
        self.assertIsInstance(cu.VERSION, str)

    def test_version_format(self):
        parts = cu.VERSION.split(".")
        self.assertEqual(len(parts), 3, "VERSION must be semver X.Y.Z")
        for part in parts:
            self.assertTrue(part.isdigit(), f"Non-numeric version component: {part!r}")

    def test_version_in_json_output(self):
        with patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"), \
             patch.object(cu, "CLAUDE_PROJECTS", "/nonexistent"), \
             patch.object(cu, "MODE_FILE", "/nonexistent"):
            settings = cu.load_settings()
            # Simulate json command output construction
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            out = {
                "version": cu.VERSION,
                "provider": cu.detect_provider(settings),
            }
        self.assertEqual(out["version"], cu.VERSION)

    def test_version_in_dashboard_render(self):
        with patch("time.time", return_value=1_000_000.0), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            out = cu.render_dashboard(None, [], {}, cu.load_settings())
        self.assertIn(f"v{cu.VERSION}", out)

    def test_cli_version_flag(self, *_):
        for flag in ("--version", "-V"):
            with patch.object(sys, "argv", ["claude-usage", flag]), \
                 patch("sys.stdout", new_callable=__import__("io").StringIO) as mock_out:
                cu.main()
            self.assertIn(cu.VERSION, mock_out.getvalue())


class TestHelp(unittest.TestCase):
    def _run_help(self, flag):
        with patch.object(sys, "argv", ["claude-usage", flag]), \
             patch("sys.stdout", new_callable=__import__("io").StringIO) as mock_out:
            cu.main()
        return mock_out.getvalue()

    def test_help_flag(self):
        out = self._run_help("--help")
        self.assertIn("claude-usage", out)
        self.assertIn("USAGE", out)

    def test_help_short_flag(self):
        out = self._run_help("-h")
        self.assertIn("USAGE", out)

    def test_help_contains_all_sections(self):
        out = self._run_help("--help")
        for section in ("STATUS BAR COMMANDS", "INTERACTIVE COMMANDS",
                        "UTILITY", "SETTINGS", "TMUX KEYBINDINGS"):
            self.assertIn(section, out, f"Missing section: {section}")

    def test_help_contains_all_commands(self):
        out = self._run_help("--help")
        for cmd in ("short", "long", "json", "cost", "toggle", "dashboard",
                    "--refresh", "--install-hook", "--uninstall-hook",
                    "--version", "--help"):
            self.assertIn(cmd, out, f"Missing command: {cmd}")

    def test_help_exit_zero(self):
        with patch.object(sys, "argv", ["claude-usage", "--help"]), \
             patch("sys.stdout", new_callable=__import__("io").StringIO):
            try:
                cu.main()
            except SystemExit as e:
                self.fail(f"--help raised SystemExit({e.code})")

    def test_unknown_command_exits_nonzero(self):
        with patch.object(sys, "argv", ["claude-usage", "badcmd"]), \
             patch("sys.stderr", new_callable=__import__("io").StringIO) as mock_err:
            with self.assertRaises(SystemExit) as ctx:
                cu.main()
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("claude-usage --help", mock_err.getvalue())


class TestDecodeProjectName(unittest.TestCase):
    def test_home_prefix_stripped(self):
        # /home/user/my-project → -home-user-my-project → my-project
        self.assertEqual(cu.decode_project_name("-home-user-my-project"), "my-project")

    def test_deep_path(self):
        # /home/user/src/my-app → -home-user-src-my-app → src-my-app
        self.assertEqual(cu.decode_project_name("-home-user-src-my-app"), "src-my-app")

    def test_no_home_prefix(self):
        # Paths that don't start with home- are returned as-is (minus leading -)
        self.assertEqual(cu.decode_project_name("-srv-myapp"), "srv-myapp")

    def test_empty_string(self):
        result = cu.decode_project_name("")
        self.assertIsInstance(result, str)

    def test_just_dashes(self):
        result = cu.decode_project_name("---")
        self.assertIsInstance(result, str)


class TestProgressBar(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(cu.progress_bar(0.0, width=4), "[....]")

    def test_full(self):
        self.assertEqual(cu.progress_bar(1.0, width=4), "[####]")

    def test_half(self):
        self.assertEqual(cu.progress_bar(0.5, width=4), "[##..]")

    def test_clamps_above_one(self):
        self.assertEqual(cu.progress_bar(1.5, width=4), "[####]")

    def test_clamps_below_zero(self):
        self.assertEqual(cu.progress_bar(-0.5, width=4), "[....]")

    def test_custom_fill_empty(self):
        result = cu.progress_bar(0.5, width=4, fill='X', empty='o')
        self.assertEqual(result, "[XXoo]")

    def test_default_width(self):
        result = cu.progress_bar(0.5)
        self.assertEqual(len(result), 22)  # [####...] = 2 + 20 = 22


class TestLoadJsonlByProject(unittest.TestCase):
    def _write_jsonl(self, path, records):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def _make_record(self, hours_ago=1, inp=100, out=50):
        dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        return {
            "timestamp": dt.isoformat(),
            "message": {
                "usage": {
                    "input_tokens": inp,
                    "output_tokens": out,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                }
            },
        }

    def test_groups_by_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            proj_a = os.path.join(tmpdir, "-home-user-proj-a")
            proj_b = os.path.join(tmpdir, "-home-user-proj-b")
            self._write_jsonl(
                os.path.join(proj_a, "session.jsonl"),
                [self._make_record(1), self._make_record(2)],
            )
            self._write_jsonl(
                os.path.join(proj_b, "session.jsonl"),
                [self._make_record(1)],
            )
            with patch.object(cu, "CLAUDE_PROJECTS", tmpdir):
                result = cu.load_jsonl_records_by_project()
            self.assertIn("proj-a", result)
            self.assertIn("proj-b", result)
            self.assertEqual(len(result["proj-a"]), 2)
            self.assertEqual(len(result["proj-b"]), 1)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(cu, "CLAUDE_PROJECTS", tmpdir):
                result = cu.load_jsonl_records_by_project()
            self.assertEqual(result, {})

    def test_missing_dir(self):
        with patch.object(cu, "CLAUDE_PROJECTS", "/nonexistent/path"):
            result = cu.load_jsonl_records_by_project()
        self.assertEqual(result, {})


class TestRenderDashboard(unittest.TestCase):
    """Smoke tests: verify render_dashboard() produces well-formed output."""

    _NOW = 1_000_000.0

    def _rl(self):
        return {
            "fetched_at": self._NOW - 10,
            "util_5h": 0.78,
            "util_7d": 0.84,
            "reset_5h": int(self._NOW) + 10_020,
            "reset_7d": int(self._NOW) + 345_600,
            "status_5h": "allowed",
            "status_7d": "allowed_warning",
        }

    def _settings(self, provider="auto", realtime=False):
        return {"provider": provider, "realtime": realtime, "cache_ttl": 300}

    def _records(self):
        dt = datetime.now(timezone.utc) - timedelta(hours=1)
        usage = {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_input_tokens": 200,
            "cache_creation_input_tokens": 100,
        }
        return [(dt, usage)]

    def test_output_is_string(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            out = cu.render_dashboard(self._rl(), self._records(), {}, self._settings())
        self.assertIsInstance(out, str)

    def test_contains_rate_limit_pct(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            # anthropic override so rate-limit block is rendered
            s = self._settings(provider="anthropic")
            out = cu.render_dashboard(self._rl(), self._records(), {}, s)
        self.assertIn("78%", out)
        self.assertIn("84%", out)

    def test_contains_cost_section(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            out = cu.render_dashboard(self._rl(), self._records(), {}, self._settings())
        self.assertIn("Token Usage & Cost", out)

    def test_contains_projects_section(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            proj = {"my-app": self._records()}
            out = cu.render_dashboard(self._rl(), self._records(), proj, self._settings())
        self.assertIn("Top Projects", out)
        self.assertIn("my-app", out)

    def test_no_rl_data_shows_no_data(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            s = self._settings(provider="anthropic")
            out = cu.render_dashboard(None, [], {}, s)
        self.assertIn("[no data]", out)

    def test_bedrock_provider_hides_rate_limit(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            s = self._settings(provider="other")
            out = cu.render_dashboard(None, [], {}, s)
        self.assertIn("not available", out)

    def test_box_lines_consistent_width(self):
        with patch("time.time", return_value=self._NOW), \
             patch.object(cu, "CREDENTIALS_FILE", "/nonexistent"):
            out = cu.render_dashboard(self._rl(), self._records(), {}, self._settings())
        box_lines = [ln for ln in out.splitlines() if ln.startswith('+') or ln.startswith('|')]
        widths = {len(ln) for ln in box_lines}
        self.assertEqual(len(widths), 1, f"Inconsistent box widths: {widths}")


if __name__ == "__main__":
    unittest.main()
