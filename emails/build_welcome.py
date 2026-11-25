"""Builds the welcome email as email-safe HTML (tables + inline styles).
python3 emails/build_welcome.py [BASE_URL] > emails/welcome.html"""
import json, sys, html
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://fromtheheelofitaly.org"
site = json.load(open("site.json"))
blurbs = {
  "family": "Our home, our children and how God is at work in our everyday life.",
  "church": "Our church family in Modugno: its people, its growth and the vision for our city.",
  "reaching-the-nations": "Reaching those who have come to Puglia from far away with friendship, practical help and the Gospel of Jesus.",
  "plant-and-strengthen": "Planting new churches in southern Italy and beyond, and walking alongside churches that need support.",
  "missions": "Training and sending workers beyond our borders.",
  "il-rifugio": "Our center in Ruvo di Puglia, a place of rest and training for churches and ministries.",
}
RED, INK, SOFT = "#e74759", "#1f2326", "#5b6166"
F = "font-family:Manrope,Helvetica,Arial,sans-serif;"
rows = ""
for a in site["areas"]:
    url = f'{BASE}/{a["slug"]}/'
    rows += f'''<tr><td style="padding:0 0 18px 0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td width="168" valign="top" style="padding-right:18px;"><a href="{url}"><img src="{BASE}{a["image"]}" width="168" height="126" alt="{html.escape(a["name"])}" style="display:block;width:168px;height:126px;object-fit:cover;border-radius:12px;border:0;"></a></td>
<td valign="middle" style="{F}">
<a href="{url}" style="{F}font-size:18px;font-weight:800;color:{INK};text-decoration:none;">{html.escape(a["name"])}</a>
<p style="{F}margin:6px 0 0;font-size:15px;line-height:1.5;color:{SOFT};">{html.escape(blurbs[a["slug"]])}</p>
</td></tr></table></td></tr>'''
out = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Welcome · Updates from the Heel of Italy</title></head>
<body style="margin:0;padding:0;background:#f4f4f4;">
<div style="display:none;max-height:0;overflow:hidden;">From the heel of Italy to the ends of the earth, and now you are part of the story.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f4f4;"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:100%;background:#ffffff;border-radius:18px;overflow:hidden;">
<tr><td style="background:{RED};padding:38px 36px 34px;text-align:left;">
<img src="{BASE}/img/pv-glifo.svg" width="44" height="44" alt="Pieno Vangelo" style="display:block;border:0;margin-bottom:22px;">
<h1 style="{F}margin:0;font-size:40px;line-height:1.05;font-weight:800;color:#ffffff;">Welcome</h1>
<p style="{F}margin:10px 0 0;font-size:19px;font-weight:700;color:#ffe3e6;">Updates from the Heel of Italy</p>
</td></tr>
<tr><td style="padding:34px 36px 8px;{F}font-size:16px;line-height:1.65;color:{INK};">
<p style="margin:0 0 14px;">Dear friend,</p>
<p style="margin:0 0 14px;">We're so glad you're here, and thrilled that you've chosen to walk with us! With this newsletter we'd love to keep you updated on what God is doing here in Puglia, the "heel" of Italy, and from here to the ends of the earth.</p>
<p style="margin:0 0 24px;">On our blog, <a href="{BASE}/" style="color:#e74759;font-weight:700;">fromtheheelofitaly.org</a>, you can follow every update on our ministry in this part of Italy. There you'll find news from these six areas:</p>
</td></tr>
<tr><td style="padding:0 36px 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table></td></tr>
<tr><td style="padding:6px 36px 8px;{F}font-size:16px;line-height:1.65;color:{INK};">
<p style="margin:0 0 14px;">This story is still being written, and now you are part of it too. Every prayer, every word of encouragement and every gift helps this work grow stronger. <strong>Thank you for being with us!</strong></p>
<p style="margin:0 0 24px;">Once a month, our newsletter will bring you an update from one of these areas, right to your inbox.</p>
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="background:{RED};border-radius:999px;"><a href="{BASE}/" style="{F}display:inline-block;padding:13px 24px;font-size:15px;font-weight:800;color:#ffffff;text-decoration:none;">Explore the updates →</a></td>
<td width="10"></td>
<td style="border:2px solid {RED};border-radius:999px;"><a href="{BASE}/support/" style="{F}display:inline-block;padding:11px 22px;font-size:15px;font-weight:800;color:{RED};text-decoration:none;">Support the work</a></td>
</tr></table>
<p style="margin:30px 0 4px;">With joy and gratitude,</p>
<p style="margin:0 0 30px;font-weight:800;">Pastor Mirko and Giorgia</p>
</td></tr>
<tr><td style="background:#1f2326;padding:22px 36px;{F}font-size:12px;line-height:1.6;color:#9aa1a6;">
Pieno Vangelo Church · Modugno (BA), Italy · <a href="{BASE}/" style="color:#ffffff;">fromtheheelofitaly.org</a><br>
You are receiving this because you subscribed to our updates. <a href="{{{{ unsubscribe }}}}" style="color:#ffffff;">Unsubscribe</a>
</td></tr>
</table></td></tr></table></body></html>'''
print(out)
