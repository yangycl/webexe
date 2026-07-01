import os
import shutil
import subprocess
import sys
import tomllib

def buildmain():

    init_mode = "init" in sys.argv

    if init_mode :
        webexe_toml = """
[packageData]
output = "webexe.exe"
icon = "icons/favicon.ico"
name = "webexe"
"""
        with open("webexe.toml", "w", encoding="utf8") as f :
            f.write(webexe_toml)



    print("read file......")

    os.makedirs(".webexe", exist_ok=True)

    with open("index.html", "r", encoding="utf-8") as f:
        htmlcode = f.read()

    from back import api

    print("generate runtime.....")

    maincode = '''
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
            raise AttributeError(f"找不到方法: {name}")


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
    ''' % repr(htmlcode)


    with open(".webexe/build.py", "w", encoding="utf-8") as f:
        f.write(maincode)

    # 複製 back.py 到 .webexe 目錄
    if os.path.exists("back.py"):
        shutil.copy("back.py", ".webexe/back.py")

    print("install packages......")

    dev_mode = "--dev" in sys.argv


    subprocess.run(
        ["python", "-m", "pip", "install", "pywebview"],
        check=True
    )

    if not dev_mode:

        subprocess.run(
            ["python", "-m", "pip", "install", "pyinstaller"],
            check=True
        )




    if dev_mode:
        print("dev mode: run build.py")

        subprocess.run(
            [
                "python",
                ".webexe/build.py"
            ],
            check=True
        )

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
                webexe_settings.output,
                "--icon",
                webexe_settings.icon,
                "--hidden-import",
                "back"
            ],
            check=True
        )

        print("clean temp files......")
        shutil.rmtree(".webexe", ignore_errors=True)

    print("done!")
