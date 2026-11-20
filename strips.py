"""네이버 위젯용 환율 띠 3장 (2026-11-18). 네이버 직접등록 위젯은 높이를 30px로 고정해서
카드 한 장 대신 170x30 띠 3장(제목·달러·엔화)을 위젯 3개로 쌓는다.

  python widgets/fx/strips.py   → out/fx_head.png, out/fx_usd.png, out/fx_jpy.png (2배 크기 340x60)

자료(2026-11-20 바꿈, 사용자 "오늘이 11.20인데 매일 업데이트가 안 되나"):
  1순위 Yahoo Finance 시세(KRW=X, JPYKRW=X, 거의 실시간) — 제목에 "11.20 09시" 처럼 한국 시각
  실패하면 Frankfurter(유럽중앙은행, 하루 한 번 한국 자정쯤) — 제목에 "11.19 기준"
"""
import json
import urllib.request
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw

from make_fx import DOWN, NAVY, OUT, SUB, UP, YELLOW, S, W, f, fetch

H = 30 * S
KST = timezone(timedelta(hours=9))


def yahoo(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=5m"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    m = json.load(urllib.request.urlopen(req, timeout=20))["chart"]["result"][0]["meta"]
    now, prev = float(m["regularMarketPrice"]), float(m["chartPreviousClose"])
    return now, prev, datetime.fromtimestamp(m["regularMarketTime"], KST)


def fetch_live():
    """(라벨, (달러 지금, 전일), (100엔 지금, 전일))"""
    try:
        un, up, t = yahoo("KRW=X")
        jn, jp, _ = yahoo("JPYKRW=X")
        if not (900 < un < 2500 and 3 < jn < 20):      # 엉뚱한 값이면 버림
            raise ValueError((un, jn))
        return f"{t.month}.{t.day} {t.hour:02d}시 기준", (un, up), (jn * 100, jp * 100)
    except Exception as e:
        print("yahoo 실패, 유럽중앙은행 자료로:", e)
        usd, jpy = fetch()
        day = usd[-1][0]
        lab = f"{int(day[5:7])}.{int(day[8:10])} 기준"
        return lab, (usd[-1][1], usd[-2][1]), (jpy[-1][1], jpy[-2][1])


def base(fill="#FFFFFF", outline=NAVY):
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * S, fill=fill, outline=outline, width=S)
    return img, d


def head(label):
    img, d = base(NAVY)
    d.text((10 * S, H / 2), "오늘의 환율", font=f("x", 12), fill="#FFFFFF", anchor="lm")
    d.text((W - 10 * S, H / 2), label, font=f("b", 9.5), fill=YELLOW, anchor="rm")
    return img


def strip(code, pair):
    now, prev = pair
    ch = now - prev
    pct = ch / prev * 100
    col = UP if ch > 0 else DOWN if ch < 0 else SUB
    arrow = "▲" if ch > 0 else "▼" if ch < 0 else "-"
    img, d = base()
    d.rounded_rectangle([6 * S, 7 * S, 40 * S, 23 * S], radius=8 * S, fill=NAVY)
    d.text((23 * S, H / 2), code, font=f("b", 8.5), fill=YELLOW, anchor="mm")
    d.text((46 * S, H / 2 + 0.5 * S), f"{now:,.2f}", font=f("x", 12.5), fill=NAVY, anchor="lm")
    d.text((W - 8 * S, H / 2), f"{arrow}{abs(pct):.2f}%", font=f("b", 9), fill=col, anchor="rm")
    return img


if __name__ == "__main__":
    label, usd, jpy = fetch_live()
    OUT.mkdir(exist_ok=True)
    head(label).save(OUT / "fx_head.png", optimize=True)
    strip("1달러", usd).save(OUT / "fx_usd.png", optimize=True)
    strip("100엔", jpy).save(OUT / "fx_jpy.png", optimize=True)
    print("ok", label, usd, jpy)
