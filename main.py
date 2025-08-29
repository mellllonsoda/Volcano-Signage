from flask import Flask, render_template_string, request, redirect, url_for
import volcanic_checker as checker
from datetime import datetime

app = Flask(__name__)

ALERT_MESSAGES = {
    1: "活火山であることに留意",
    2: "火口周辺規制",
    3: "入山規制",
    4: "高齢者等避難",
    5: "避難"
}

ALERT_COLORS = {
    1: "#FFFFFF",
    2: "#F2E700",
    3: "#F6AA00",
    4: "#FF4B00",
    5: "#990099"
}

SIGNAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="60">
<title>火山警戒情報</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&display=swap');

    .biz-udpgothic-regular {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 400;
        font-style: normal;
    }

    .biz-udpgothic-bold {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 700;
        font-style: normal;
    }

    body {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        font-family: BIZ UDPGothic;
        flex-direction: column;
        text-align: center;
        background-color: {{ bg_color }};
        transition: background-color 0.5s;
    }
    .volcano { font-size: 7em; margin: 0.5em 0; color: {{ fg_color }}; }
    .level   { font-size: 6em; margin: 0.3em 0; color: {{ fg_color }}; }
    .alert   { font-size: 5em; margin: 0.3em 0; color: {{ fg_color }}; }
    .time { font-size: 4em; margin-top: 2em; color: #333; }
</style>
</head>
<body>
    <div class="volcano">{{ volcano.name }}</div>
    <div class="level">噴火警戒レベル: {{ volcano.level }}</div>
    {% if volcano.level in alert_messages %}
        <div class="alert">{{ alert_messages[volcano.level] }}</div>
    {% endif %}
    <div class="time">最終取得時刻: {{ retrieved_at }}</div>
</body>
</html>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>火山情報ポータル</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&display=swap');

    .biz-udpgothic-regular {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 400;
        font-style: normal;
    }

    .biz-udpgothic-bold {
        font-family: "BIZ UDPGothic", sans-serif;
        font-weight: 700;
        font-style: normal;
    }

    body {
        margin: 0;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: linear-gradient(135deg, #1e1e1e, #3a3a3a);
        font-family: 'BIZ UDPGothic', sans-serif;
        color: #fff;
        flex-direction: column;
        text-align: center;
        padding: 20px;
        box-sizing: border-box;
    }

    h1 {
        font-size: 4em;
        margin-bottom: 0.3em;
        letter-spacing: 2px;
    }

    p.description {
        font-size: 1.5em;
        margin-bottom: 1.5em;
        max-width: 800px;
    }

    .error {
        color: #ff5555;
        font-size: 1.2em;
        margin-bottom: 1em;
    }

    form {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    input[type="text"] {
        padding: 1em;
        font-size: 1.5em;
        border-radius: 10px;
        border: none;
        margin-bottom: 1em;
        width: 300px;
        max-width: 80%;
    }

    input[type="submit"] {
        padding: 1em 2em;
        font-size: 1.5em;
        color: #fff;
        background: #ff4b00;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    input[type="submit"]:hover {
        background: #ff6622;
        transform: scale(1.05);
    }
</style>
</head>
<body>
    <h1>火山情報デジタルサイネージ</h1>
    <p class="description">
        このページでは日本国内の常時観測火山の最新の噴火警戒レベルを確認できます。
        火山名を入力して「確認」ボタンを押すと、画面中央に警戒情報が表示されます。
        このプログラムを利用した場合の事故に製作者は責任を一切負いません。
    </p>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <form action="/signage" method="get">
        <input type="text" name="name" placeholder="例: 鶴見岳・伽藍岳" required>
        <input type="submit" value="確認">
    </form>
</body>
</html>
"""


@app.route("/")
def home():
    # エラー文をオプションで渡せる
    error = request.args.get("error")
    return render_template_string(HOME_TEMPLATE, error=error)

@app.route("/signage")
def signage():
    volcano_name = request.args.get("name")
    if not volcano_name:
        return redirect(url_for("home", error="火山名を指定してください。"))
    try:
        alert = checker.get_alert_level_by_name(volcano_name)
    except:
        return redirect(url_for("home", error=f"'{volcano_name}' の情報取得に失敗しました。"))

    # 警戒レベルが0の場合はトップページに戻す
    if alert.level == 0:
        return redirect(url_for("home", error=f"'{volcano_name}' の情報が取得できませんでした。"))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bg_color = ALERT_COLORS.get(alert.level, "#FFFFFF")
    if alert.level == 5:
        fg_color = "#FFFFFF"
    else:
        fg_color = "#000000"

    return render_template_string(
        SIGNAGE_TEMPLATE,
        volcano=alert,
        retrieved_at=now,
        alert_messages=ALERT_MESSAGES,
        bg_color=bg_color,
        fg_color=fg_color
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
