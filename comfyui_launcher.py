import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

import psutil

# Default port per profile. Override with COMFYUI_PORT in .env / .env.<profile>.
DEFAULT_PORTS = {"prod": 8188, "dev": 8189}


# ---------------------------------------------------------------------------
# Settings (.env files)
# ---------------------------------------------------------------------------
def load_env(path):
    """Read KEY=VALUE lines from a .env file."""
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_settings(root, profile):
    """prod reads only .env; other profiles read only .env.<profile> (e.g. .env.dev)."""
    if profile == "prod":
        return load_env(root / ".env")
    return load_env(root / f".env.{profile}")


def get_setting(env, key):
    """Priority: real environment variable > the profile's env file"""
    return os.environ.get(key) or env.get(key) or None


def build_directory_args(env):
    args = []
    for key, flag in (
        ("COMFYUI_INPUT_DIR", "--input-directory"),
        ("COMFYUI_OUTPUT_DIR", "--output-directory"),
    ):
        value = get_setting(env, key)
        if not value:
            continue
        path = Path(value).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        print(f"{flag}: {path}", flush=True)
        args += [flag, str(path)]
    return args


# ---------------------------------------------------------------------------
# Restart handling (only touches the server using the same port)
# ---------------------------------------------------------------------------
def is_repo_server(command, cwd, root):
    if len(command) < 2 or not Path(command[0]).name.lower().startswith("python"):
        return False
    args = iter(command[1:])
    for arg in args:
        if arg in ("-W", "-X"):
            next(args, None)
        elif arg in ("-u", "-B", "-E", "-I", "-O", "-OO", "-s", "-S", "-v", "-q"):
            continue
        elif arg.startswith("-"):
            return False
        else:
            entry = Path(arg)
            if not entry.is_absolute():
                entry = Path(cwd) / entry
            return entry.resolve() == root / "main.py"
    return False


def get_port(command):
    """Port given to main.py (ComfyUI's default is 8188)."""
    for index, arg in enumerate(command):
        if arg == "--port" and index + 1 < len(command):
            return command[index + 1]
        if arg.startswith("--port="):
            return arg.split("=", 1)[1]
    return "8188"


def stop_existing(root, port):
    targets = []
    for process in psutil.process_iter():
        try:
            command = process.cmdline()
            if is_repo_server(command, process.cwd(), root) and get_port(command) == str(port):
                targets.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    for process in targets:
        try:
            print(f"Restarting ComfyUI: stopping PID {process.pid}. Active generation will be interrupted.", flush=True)
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(targets, timeout=15)
    if alive:
        raise RuntimeError("ComfyUI did not stop within 15 seconds. Close its window and try again.")
    for connection in psutil.net_connections(kind="tcp"):
        if (connection.status == psutil.CONN_LISTEN and connection.laddr.port == port
                and connection.laddr.ip in ("127.0.0.1", "0.0.0.0", "::")):
            raise RuntimeError(f"Port {port} is held by another process (PID {connection.pid}); it was not stopped.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Launch ComfyUI")
    parser.add_argument("--profile", choices=sorted(DEFAULT_PORTS), default="prod",
                        help="prod: .env / dev: .env.dev only (default: prod)")
    options = parser.parse_args()

    root = Path(__file__).resolve().parent
    profile_env = root / f".env.{options.profile}"
    use_standard = options.profile != "prod" and not profile_env.is_file()
    try:
        if use_standard:
            # No .env.<profile>: ignore every env setting and start as standard.
            print(f"[INFO] {profile_env.name} was not found. Starting with standard settings (no env file).", flush=True)
            port = DEFAULT_PORTS["prod"]
            extra_args = []
        else:
            env = load_settings(root, options.profile)
            port = int(get_setting(env, "COMFYUI_PORT") or DEFAULT_PORTS[options.profile])
            extra_args = build_directory_args(env)
            extra_args += shlex.split(get_setting(env, "COMFYUI_EXTRA_ARGS") or "")
        stop_existing(root, port)
    except (psutil.Error, RuntimeError, OSError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print(f"Starting ComfyUI [{options.profile}]: http://127.0.0.1:{port}", flush=True)
    try:
        return subprocess.call(
            [sys.executable, "main.py", "--port", str(port), *extra_args],
            cwd=root,
        )
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
