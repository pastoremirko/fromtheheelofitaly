"""Builds the welcome email as email-safe HTML (tables + inline styles).
python3 emails/build_welcome.py [BASE_URL] [en|nl] > emails/welcome.html   (or welcome.nl.html)"""
import json, sys, html
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://fromtheheelofitaly.org"
LANG = sys.argv[2] if len(sys.argv) > 2 else "en"
site = json.load(open("site.json"))
if LANG == "nl":
    nl = json.load(open("site.nl.json"))
    for a in site["areas"]:
        a["name"] = nl["areas"][a["slug"]]["name"]
P = "" if LANG == "en" else "/nl"
blurbs = {
  "family": "Our home, our children and how God is at work in our everyday life.",
  "church": "Our church family in Modugno: its people, its growth and the vision for our city.",
  "welcoming-immigrants": "Welcoming those who have come to Puglia from far away with friendship, practical help and the Gospel of Jesus.",
  "plant-and-strengthen": "Planting new churches in southern Italy and beyond, and walking alongside churches that need support.",
  "missions": "Training and sending workers beyond our borders.",
  "il-rifugio": "Our center in Ruvo di Puglia, a place of rest and training for churches and ministries.",
}
if LANG == "nl":
    blurbs = {
      "family": "Ons huis, onze kinderen en hoe God in ons dagelijks leven aan het werk is.",
      "church": "Onze kerkfamilie in Modugno: de mensen, de groei en de visie voor onze stad.",
      "welcoming-immigrants": "Wie van ver naar Puglia is gekomen ontvangen met vriendschap, praktische hulp en het evangelie van Jezus.",
      "plant-and-strengthen": "Nieuwe kerken stichten in Zuid-Italië en daarbuiten, en optrekken met kerken die steun nodig hebben.",
      "missions": "Werkers toerusten en uitzenden over de grens.",
      "il-rifugio": "Ons centrum in Ruvo di Puglia, een plek van rust en toerusting voor kerken en bedieningen.",
    }
TX = {
  "en": dict(title="Welcome · Updates from the Heel of Italy", pre="From the heel of Italy to the ends of the earth, and now you are part of the story.",
    h1="Welcome", sub="Updates from the Heel of Italy", dear="Dear friend,",
    p1="We're so glad you're here, and thrilled that you've chosen to walk with us! With this newsletter we'd love to keep you updated on what God is doing here in Puglia, the \"heel\" of Italy, and from here to the ends of the earth.",
    p2a="On our blog, ", p2b=", you can follow every update on our ministry in this part of Italy. There you'll find news from these six areas:",
    p3="This story is still being written, and now you are part of it too. Every prayer, every word of encouragement and every gift helps this work grow stronger. <strong>Thank you for being with us!</strong>",
    p4="About once a month, you'll find a short letter from us in your inbox: one story, one photo and a glimpse of what God is doing among us. Whenever you'd like more details, you'll find them on our blog.",
    b1="Explore the updates →", b2="Support the work", bye="With joy and gratitude,", sig="Pastor Mirko and Giorgia",
    foot1="Pieno Vangelo Church · Modugno (BA), Italy", foot2="You are receiving this because you subscribed to our updates.", unsub="Unsubscribe"),
  "nl": dict(title="Welkom · Nieuws uit de hak van Italië", pre="Vanuit de hak van Italië tot aan de uiteinden van de aarde, en nu ben jij een deel van het verhaal.",
    h1="Welkom", sub="Nieuws uit de hak van Italië", dear="Lieve vriend, lieve vriendin,",
    p1="Wat fijn dat je er bent, en dat je met ons mee wilt lopen! Met deze nieuwsbrief houden we je graag op de hoogte van wat God doet hier in Puglia, de \"hak\" van Italië, en van hieruit tot aan de uiteinden van de aarde.",
    p2a="Op onze blog, ", p2b=", kun je al het nieuws over ons werk in dit deel van Italië volgen. Je vindt daar berichten uit deze zes gebieden:",
    p3="Dit verhaal wordt nog geschreven, en nu ben jij er ook een deel van. Elk gebed, elk bemoedigend woord en elke gift helpt dit werk te groeien. <strong>Dank je wel dat je met ons meeleeft!</strong>",
    p4="Ongeveer één keer per maand vind je een korte brief van ons in je inbox: één verhaal, één foto en een inkijkje in wat God hier doet. Wil je meer weten? Op onze blog lees je alle details.",
    b1="Lees het nieuws →", b2="Steun het werk", bye="Met vreugde en dankbaarheid,", sig="Pastor Mirko en Giorgia",
    foot1="Pieno Vangelo-kerk · Modugno (BA), Italië", foot2="Je ontvangt deze e-mail omdat je je hebt aangemeld voor ons nieuws.", unsub="Afmelden"),
}[LANG]
RED, INK, SOFT = "#e74759", "#1f2326", "#5b6166"
F = "font-family:Manrope,Helvetica,Arial,sans-serif;"
rows = ""
for a in site["areas"]:
    url = f'{BASE}{P}/{a["slug"]}/'
    rows += f'''<tr><td style="padding:0 0 18px 0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td width="168" valign="top" style="padding-right:18px;"><a href="{url}"><img src="{BASE}{a["image"]}" width="168" height="126" alt="{html.escape(a["name"])}" style="display:block;width:168px;height:126px;object-fit:cover;border-radius:12px;border:0;"></a></td>
<td valign="middle" style="{F}">
<a href="{url}" style="{F}font-size:18px;font-weight:800;color:{INK};text-decoration:none;">{html.escape(a["name"])}</a>
<p style="{F}margin:6px 0 0;font-size:15px;line-height:1.5;color:{SOFT};">{html.escape(blurbs[a["slug"]])}</p>
</td></tr></table></td></tr>'''
out = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TX["title"]}</title></head>
<body style="margin:0;padding:0;background:#f4f4f4;">
<div style="display:none;max-height:0;overflow:hidden;">{TX["pre"]}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f4f4;"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:100%;background:#ffffff;border-radius:18px;overflow:hidden;">
<tr><td style="background:{RED};padding:38px 36px 34px;text-align:left;">
<img src="{BASE}/img/pv-logo-icon.png" width="44" height="44" alt="Pieno Vangelo" style="display:block;border:0;margin-bottom:22px;">
<h1 style="{F}margin:0;font-size:40px;line-height:1.05;font-weight:800;color:#ffffff;">{TX["h1"]}</h1>
<p style="{F}margin:10px 0 0;font-size:19px;font-weight:700;color:#ffe3e6;">{TX["sub"]}</p>
</td></tr>
<tr><td style="padding:34px 36px 8px;{F}font-size:16px;line-height:1.65;color:{INK};">
<p style="margin:0 0 14px;">{TX["dear"]}</p>
<p style="margin:0 0 14px;">{TX["p1"]}</p>
<p style="margin:0 0 24px;">{TX["p2a"]}<a href="{BASE}{P}/" style="color:#e74759;font-weight:700;">fromtheheelofitaly.org</a>{TX["p2b"]}</p>
</td></tr>
<tr><td style="padding:0 36px 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table></td></tr>
<tr><td style="padding:6px 36px 8px;{F}font-size:16px;line-height:1.65;color:{INK};">
<p style="margin:0 0 14px;">{TX["p3"]}</p>
<p style="margin:0 0 24px;">{TX["p4"]}</p>
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="background:{RED};border-radius:999px;"><a href="{BASE}{P}/" style="{F}display:inline-block;padding:13px 24px;font-size:15px;font-weight:800;color:#ffffff;text-decoration:none;">{TX["b1"]}</a></td>
<td width="10"></td>
<td style="border:2px solid {RED};border-radius:999px;"><a href="{BASE}{P}/support/" style="{F}display:inline-block;padding:11px 22px;font-size:15px;font-weight:800;color:{RED};text-decoration:none;">{TX["b2"]}</a></td>
</tr></table>
<p style="margin:30px 0 4px;">{TX["bye"]}</p>
<p style="margin:0 0 30px;font-weight:800;">{TX["sig"]}</p>
</td></tr>
<tr><td style="background:#1f2326;padding:22px 36px;{F}font-size:12px;line-height:1.6;color:#9aa1a6;">
{TX["foot1"]} · <a href="{BASE}{P}/" style="color:#ffffff;">fromtheheelofitaly.org</a><br>
{TX["foot2"]} <a href="{{{{ unsubscribe }}}}" style="color:#ffffff;">{TX["unsub"]}</a>
</td></tr>
</table></td></tr></table></body></html>'''
print(out)
