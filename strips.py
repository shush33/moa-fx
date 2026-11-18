"""네이버 위젯용 환율 띠 3장 (2026-11-18). 네이버 직접등록 위젯은 높이를 30px로 고정해서
카드 한 장 대신 170x30 띠 3장(제목·달러·엔화)을 위젯 3개로 쌓는다.

  python widgets/fx/strips.py   → out/fx_head.png, out/fx_usd.png, out/fx_jpy.png (2배 크기 340x60)
"""
from PIL import Image, ImageDraw

from make_fx import DOWN, NAVY, OUT, SUB, UP, YELLOW, S, W, f, fetch

H = 30 * S


def base(fill="#FFFFFF", outline=NAVY):
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * S, fill=fill, outline=outline, width=S)
    return img, d


def head(day):
    img, d = base(NAVY)
    d.text((10 * S, H / 2), "오늘의 환율", font=f("x", 12), fill="#FFFFFF", anchor="lm")
    m, dd = int(day[5:7]), int(day[8:10])
    d.text((W - 10 * S, H / 2), f"{m}.{dd} 기준", font=f("b", 9.5), fill=YELLOW, anchor="rm")
    return img


def strip(code, series):
    vals = [v for _, v in series]
    now, prev = vals[-1], vals[-2]
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
    usd, jpy = fetch()
    OUT.mkdir(exist_ok=True)
    head(usd[-1][0]).save(OUT / "fx_head.png", optimize=True)
    strip("1달러", usd).save(OUT / "fx_usd.png", optimize=True)
    strip("100엔", jpy).save(OUT / "fx_jpy.png", optimize=True)
    print("ok", usd[-1], jpy[-1])
