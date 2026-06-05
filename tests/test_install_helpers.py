from __future__ import annotations

import subprocess
from pathlib import Path


def test_discover_conda_finds_home_miniconda(tmp_path: Path) -> None:
    home = tmp_path / "home"
    conda_root = home / "miniconda3"
    bin_dir = conda_root / "bin"
    profile_dir = conda_root / "etc" / "profile.d"
    bin_dir.mkdir(parents=True)
    profile_dir.mkdir(parents=True)

    fake_conda = bin_dir / "conda"
    fake_conda.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_conda.chmod(0o755)
    (profile_dir / "conda.sh").write_text(
        'export PATH="$HOME/miniconda3/bin:$PATH"\n',
        encoding="utf-8",
    )

    helper = Path(__file__).resolve().parents[1] / "src" / "scripts" / "install_helpers.sh"
    cmd = (
        f'export HOME="{home}"; '
        'export PATH="/usr/bin:/bin"; '
        f'source "{helper}"; '
        'discover_conda >/dev/null; '
        'type -P conda'
    )
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-c", cmd],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == str(fake_conda)
