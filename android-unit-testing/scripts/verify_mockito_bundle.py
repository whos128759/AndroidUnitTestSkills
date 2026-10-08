"""Verify bundled Mockito jars without network access."""

from hashlib import sha1, sha256
from pathlib import Path
from zipfile import ZipFile


JARS = {
    "mockito-core-5.23.0.jar": "ae295bebd5d11fab97ab297815dc7617188b86003cbce3dfd5c0d5c3a6cc4a0c",
    "byte-buddy-1.17.7.jar": "3575dcb8a98faf943d3c1595c47a16047c4fce8a83ebbb26262f1a2f67546357",
    "byte-buddy-agent-1.17.7.jar": "a9ba887dca252ad61b7d5153294f34e6f3bdf4b2736b04373d13615a695fc0ff",
    "objenesis-3.3.jar": "02dfd0b0439a5591e35b708ed2f5474eb0948f53abf74637e959b8e4ef69bfeb",
}


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "assets" / "mockito"
    for name, expected_sha256 in JARS.items():
        data = (root / name).read_bytes()
        if sha256(data).hexdigest() != expected_sha256:
            raise SystemExit(f"SHA-256 mismatch: {name}")
        if sha1(data).hexdigest() != (root / f"{name}.sha1").read_text(encoding="ascii").strip():
            raise SystemExit(f"SHA-1 mismatch: {name}")
        with ZipFile(root / name) as jar:
            if jar.testzip() is not None:
                raise SystemExit(f"Corrupt JAR: {name}")
        print(f"OK {name}")


if __name__ == "__main__":
    main()
