"""블로그 왼쪽 위젯용 환율 카드 그림 (사용자 요청 2026-11-18: 달러·엔화, 깔끔하게).

  python widgets/fx/make_fx.py            → widgets/fx/out/fx.png (340px 폭, 위젯에는 width=170으로 넣음)

네이버 블로그 위젯은 스크립트가 막혀 실시간 숫자는 못 띄운다. 이 그림을 정해진 시간마다 새로 만들어
같은 주소에 올리고, 위젯에는 그 그림 주소만 넣는다.
자료: Frankfurter(유럽중앙은행 기준환율, 하루 한 번 갱신, 키 없음) https://www.frankfurter.app
"""
import json
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts" if (HERE / "fonts").exists() else HERE.parents[1] / "fonts"
OUT = HERE / "out"

S = 2                      # 2배로 그려서 위젯(170px)에서 선명하게
W = 170 * S
NAVY, BG, LINE, SUB = "#1F2B47", "#FFFFFF", "#E4E8EF", "#6B7486"
YELLOW, UP, DOWN = "#FFD25A", "#E5484D", "#2F6FED"   # 한국식: 오르면 빨강, 내리면 파랑
BLOG = "모아, 보아요"


def f(weight, size):
    name = {"r": "Pretendard-Regular.otf", "b": "Pretendard-Bold.otf", "x": "Pretendard-ExtraBold.otf"}[weight]
    return ImageFont.truetype(str(FONTS / name), size * S)


def fetch():
    start = (date.today() - timedelta(days=21)).isoformat()
    url = f"https://api.frankfurter.app/{start}..?from=USD&to=KRW,JPY"
    req = urllib.request.Request(url, headers={"User-Agent": "fx-widget/1.0"})
    data = json.load(urllib.request.urlopen(req, timeout=20))
    days = sorted(data["rates"])
    usd = [(d, data["rates"][d]["KRW"]) for d in days]
    jpy = [(d, data["rates"][d]["KRW"] / data["rates"][d]["JPY"] * 100) for d in days]  # 100엔당 원
    return usd, jpy


def spark(d, box, vals, color):
    x0, y0, x1, y1 = box
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * (v - lo) / span) for i, v in enumerate(vals)]
    d.line(pts, fill=color, width=2 * S, joint="curve")
    ex, ey = pts[-1]
    d.ellipse([ex - 3 * S, ey - 3 * S, ex + 3 * S, ey + 3 * S], fill=color)


def row(d, y, code, label, series):
    vals = [v for _, v in series]
    now, prev = vals[-1], vals[-2]
    ch = now - prev
    pct = ch / prev * 100
    col = UP if ch > 0 else DOWN if ch < 0 else SUB
    arrow = "▲" if ch > 0 else "▼" if ch < 0 else "-"
    # 통화 알약
    d.rounded_rectangle([12 * S, y, 50 * S, y + 17 * S], radius=9 * S, fill=NAVY)
    d.text((31 * S, y + 8.5 * S), code, font=f("b", 9), fill=YELLOW, anchor="mm")
    d.text((56 * S, y + 8.5 * S), label, font=f("r", 9.5), fill=SUB, anchor="lm")
    # 큰 숫자 + 원
    num = f"{now:,.2f}"
    d.text((12 * S, y + 22 * S), num, font=f("x", 21), fill=NAVY, anchor="lt")
    nw = d.textlength(num, font=f("x", 21))
    d.text((12 * S + nw + 3 * S, y + 32 * S), "원", font=f("b", 11), fill=NAVY, anchor="lt")
    # 변화
    d.text((12 * S, y + 52 * S), f"{arrow} {abs(ch):,.2f}  ({pct:+.2f}%)", font=f("b", 9.5), fill=col, anchor="lt")
    # 작은 추이선 (최근 2주쯤)
    spark(d, (112 * S, y + 50 * S, W - 12 * S, y + 62 * S), vals[-10:], col)


def make(usd, jpy):
    H = 228 * S
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=12 * S, outline=NAVY, width=2 * S, fill=BG)
    # 머리
    d.rounded_rectangle([0, 0, W - 1, 38 * S], radius=12 * S, fill=NAVY)
    d.rectangle([0, 26 * S, W - 1, 38 * S], fill=NAVY)
    d.text((14 * S, 19 * S), "오늘의 환율", font=f("x", 13), fill="#FFFFFF", anchor="lm")
    day = usd[-1][0]
    m, dd = int(day[5:7]), int(day[8:10])
    d.text((W - 14 * S, 19 * S), f"{m}.{dd} 기준", font=f("b", 9.5), fill=YELLOW, anchor="rm")
    row(d, 50 * S, "USD", "미국 1달러", usd)
    d.line([12 * S, 125 * S, W - 12 * S, 125 * S], fill=LINE, width=S)
    row(d, 136 * S, "JPY", "일본 100엔", jpy)
    d.text((W / 2, H - 12 * S), f"{BLOG} · 유럽중앙은행 기준", font=f("r", 8), fill=SUB, anchor="mm")
    OUT.mkdir(exist_ok=True)
    img.save(OUT / "fx.png", optimize=True)
    (OUT / "fx.json").write_text(json.dumps({"date": day, "usd": usd[-1][1], "jpy100": jpy[-1][1]},
                                           ensure_ascii=False), encoding="utf-8")
    return OUT / "fx.png"


if __name__ == "__main__":
    usd, jpy = fetch()
    if len(usd) < 2:
        sys.exit("환율 자료가 부족해요.")
    print(make(usd, jpy), usd[-1], jpy[-1])
