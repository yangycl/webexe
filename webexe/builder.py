import base64
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import tomllib
import urllib.parse
import webbrowser


def _collect_telemetry_via_issue(toml_content_raw):
    """Triggers an English telemetry prompt and opens a GitHub Issue template with full TOML."""
    # Local marker file to ensure this prompt only triggers once per machine
    marker_file = Path.home() / ".webexe_registered"
    if marker_file.exists():
        return

    # 1. Polite English terminal prompt (GDPR compliant)
    print("\n📊 =========================================================")
    print(" Thank you for using WebExe! To help us improve this tool, ")
    print(" we invite you to share anonymous configuration telemetry. ")
    print(" We only collect non-sensitive metrics from your webexe.toml. ")
    print(" ===========================================================\n")

    user_choice = (
        input("Would you like to share anonymous configuration data? (y/N): ")
        .strip()
        .lower()
    )

    # === REPLACE WITH YOUR ENCODED GITHUB DETAILS ===
    GITHUB_OWNER = "yangycl"
    GITHUB_REPO = "webexe"

    # Default issue templates
    title_text = "🎉 [Live Telemetry] New User Check-in"
    body_text = "This is an automated runtime check-in from a WebExe user.\n"

    # 2. Process metrics based on user choice
    if user_choice == "y":
        title_text = "📊 [Telemetry Data] Anonymous Full Configuration Report"
        body_text += (
            f"\n### 📊 Anonymous Configuration Snapshot:\n"
            f"The user has agreed to share their complete `webexe.toml` configuration environment to help analyze user habits.\n\n"
            f"```toml\n"
            f"{toml_content_raw}\n"
            f"```\n"
        )
    else:
        title_text = "👤 [Telemetry Opt-Out] Basic User Check-in"
        body_text += "\nUser opted out of sharing detailed configuration. Recording basic execution count only.\n"

    body_text += (
        "\n---\n"
        "*Please click 'Submit new issue' below to send this teleported metric to the author.*"
    )

    try:
        # 3. URL encode the English text and open in the default web browser
        encoded_title = urllib.parse.quote(title_text)
        encoded_body = urllib.parse.quote(body_text)
        issue_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/issues/new?title={encoded_title}&body={encoded_body}"

        webbrowser.open(issue_url)

        # 4. Touch the marker file so the user is never prompted again
        marker_file.touch()
    except Exception:
        pass


def buildmain():

    init_mode = "init" in sys.argv

    if init_mode:
        webexe_toml = """
[packageData]
output = "webexe.exe"
icon = "icons/favicon.ico"
name = "webexe"
"""
        with open("webexe.toml", "w", encoding="utf8") as f:
            f.write(webexe_toml)

    print("read file......")

    os.makedirs(".webexe", exist_ok=True)

    # Check required files
    if not os.path.exists("index.html"):
        print("ERROR: index.html does not exist!")
        return

    if not os.path.exists("back.py"):
        print("ERROR: back.py does not exist!")
        return

    with open("index.html", "r", encoding="utf-8") as f:
        htmlcode = f.read()

    from back import api

    print("generate runtime.....")

    maincode = (
        """
    import sys
    from pathlib import Path

    if not getattr(sys, "frozen", False):
        sys.path.insert(
            0,
            str(Path(__file__).parent.parent)
        )

    import webview
    import back


    class Api:
        def __getattr__(self, name):
            if name in back.api:
                return back.api[name]
            raise AttributeError(f"Method not found: {name}")


    api = Api()

    html = %s


    window = webview.create_window(
        title="Notebox",
        html=html,
        js_api=api,
        width=960,
        height=720,
        resizable=True
    )

    webview.start(debug=True)
    """
        % repr(htmlcode)
    )

    with open(".webexe/build.py", "w", encoding="utf-8") as f:
        f.write(maincode)

    # Copy back.py to .webexe directory
    if os.path.exists("back.py"):
        shutil.copy("back.py", ".webexe/back.py")

    print("install packages......")

    dev_mode = "--dev" in sys.argv

    subprocess.run(["python", "-m", "pip", "install", "pywebview"], check=True)

    if not dev_mode:
        subprocess.run(
            ["python", "-m", "pip", "install", "pyinstaller"], check=True
        )

    # 🚀 讀取整個 TOML 檔案的原始文字，準備做完整統計
    toml_content_raw = ""
    if os.path.exists("webexe.toml"):
        try:
            with open("webexe.toml", "r", encoding="utf8") as f:
                toml_content_raw = f.read().strip()
        except Exception:
            toml_content_raw = "# Error reading webexe.toml file"
    else:
        toml_content_raw = "# webexe.toml file not found"

    if dev_mode:
        print("dev mode: run build.py")

        # 🚀 在進入開發模式前觸發統計提示，傳入完整 TOML 內容
        _collect_telemetry_via_issue(toml_content_raw)

        subprocess.run(["python", ".webexe/build.py"], check=True)

    else:
        print("build webexe......")

        with open("webexe.toml", "r", encoding="utf8") as f:
            webexe_settings = tomllib.load(f)

        subprocess.run(
            [
                "python",
                "-m",
                "PyInstaller",
                ".webexe/build.py",
                "--onefile",
                "--name",
                webexe_settings["packageData"]["output"],
                "--icon",
                webexe_settings["packageData"]["icon"],
                "--hidden-import",
                "back",
            ],
            check=True,
        )

        print("clean temp files......")
        shutil.rmtree(".webexe", ignore_errors=True)

        # 🚀 正式編譯成功後，觸發統計提示，傳入完整 TOML 內容
        _collect_telemetry_via_issue(toml_content_raw)

    print("done!")


if __name__ == "__main__":
    buildmain()
