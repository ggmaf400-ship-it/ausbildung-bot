import os
import json
import logging
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

WAITING_FIRMA = 1
WAITING_TEXT = 2

FIRMS = [
    {"id":1,"datum":"08.03","firma":"Rub + GmbH","ort":"Straubing","kontakt":"info@rub.com","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":2,"datum":"04.03","firma":"Autohaus Kuschnow Straubing","ort":"Straubing","kontakt":"info@kv-schnupp.eu","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":3,"datum":"08.03","firma":"IT Box GmbH IS+ Rauning","ort":"Rauning","kontakt":"team@it-box.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":4,"datum":"09.03","firma":"Technische Hochschule Deggendorf","ort":"Deggendorf","kontakt":"info@th-dg.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Bildung"},
    {"id":5,"datum":"08.03","firma":"RPS Industry GmbH Straubing","ort":"Straubing","kontakt":"info@rpsindustry.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":6,"datum":"07.03","firma":"Hendrickson AG Straubing","ort":"Straubing","kontakt":"info@hendrickson.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":7,"datum":"08.03","firma":"Institut fuer angew. Logistik GmbH","ort":"Deggendorf","kontakt":"ial-bo@ial.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Bildung"},
    {"id":8,"datum":"08.03","firma":"Helmut Holz","ort":"Straubing","kontakt":"info@romanold.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":9,"datum":"08.03","firma":"IFA Technology GmbH Reut","ort":"Reut","kontakt":"anmeldung@ifa-technology.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":10,"datum":"10.03","firma":"Landratsamt Straubing-Bogen","ort":"Straubing","kontakt":"pauline.s@straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":11,"datum":"10.03","firma":"Stadt Straubing Stadtamt","ort":"Straubing","kontakt":"stadtamt@straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":12,"datum":"10.03","firma":"Agentur fuer Arbeit Regensburg","ort":"Regensburg","kontakt":"regensburg@arbeitsagentur.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":13,"datum":"11.03","firma":"Volksbank Straubing","ort":"Straubing","kontakt":"info@volksbank-straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":14,"datum":"11.03","firma":"Raiffeisenbank Straubing","ort":"Straubing","kontakt":"info@rb-straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":15,"datum":"11.03","firma":"MediaMarkt Straubing","ort":"Straubing","kontakt":"ausbildung@mediamarkt.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":16,"datum":"16.03","firma":"Klinikum Straubing Barmherzige Brueder","ort":"Straubing","kontakt":"bewerbung@klinikum-straubing.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":17,"datum":"16.03","firma":"DONAUISAR Klinikum Deggendorf","ort":"Deggendorf","kontakt":"personal@donau-isar-klinikum.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":18,"datum":"16.03","firma":"Barmherzige Brueder Regensburg","ort":"Regensburg","kontakt":"ausbildung@barmherzige-regensburg.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":19,"datum":"16.03","firma":"Kreisklinik Bogen","ort":"Bogen","kontakt":"info@kreisklinik-bogen.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":20,"datum":"16.03","firma":"Polizeipraesidium Niederbayern","ort":"Straubing","kontakt":"pp-nby.ausbildung@polizei.bayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":21,"datum":"16.03","firma":"Polizeiinspektion Straubing","ort":"Straubing","kontakt":"pi-straubing@polizei.bayern.de","bereich":"Fachinformatiker IT-Bereich","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":22,"datum":"16.03","firma":"Kriminalpolizeiinspektion Straubing","ort":"Straubing","kontakt":"kpi-straubing@polizei.bayern.de","bereich":"Fachinformatiker IT-Forensik","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":23,"datum":"16.03","firma":"Bundeswehr-DLZ Bogen","ort":"Bogen","kontakt":"bwdlz-bogen@bundeswehr.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Bundeswehr"},
    {"id":24,"datum":"16.03","firma":"Karrierecenter Bundeswehr Regensburg","ort":"Regensburg","kontakt":"kcbw-regensburg@bundeswehr.de","bereich":"Fachinformatiker IT-Ausbildung","art":"per E-Mail","ergebnis":"","kategorie":"Bundeswehr"},
    {"id":25,"datum":"16.03","firma":"Feuerwehr Straubing Berufsfeuerwehr","ort":"Straubing","kontakt":"feuerwehr@straubing.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Feuerwehr"},
    {"id":26,"datum":"16.03","firma":"Integrierte Leitstelle Straubing ILS","ort":"Straubing","kontakt":"ils-straubing@ils-niederbayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Feuerwehr"},
    {"id":27,"datum":"16.03","firma":"Bayerisches Rotes Kreuz KV Straubing","ort":"Straubing","kontakt":"info@kvstraubing.brk.de","bereich":"Fachinformatiker IT/Verwaltung","art":"per E-Mail","ergebnis":"","kategorie":"Rettung"},
    {"id":28,"datum":"16.03","firma":"Finanzamt Straubing","ort":"Straubing","kontakt":"poststelle@fa-sr.bayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":29,"datum":"16.03","firma":"Regierung von Niederbayern","ort":"Landshut","kontakt":"poststelle@reg-nb.bayern.de","bereich":"Fachinformatiker IT-Verwaltung","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":30,"datum":"16.03","firma":"TakeData Systems GmbH","ort":"Straubing","kontakt":"jobs@takedata.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":31,"datum":"16.03","firma":"Weum eier AC FDV","ort":"Straubing","kontakt":"D.Neumeter@aclv.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
]

USER_DATA = {}


def get_firms(uid):
    if uid not in USER_DATA:
        USER_DATA[uid] = [f.copy() for f in FIRMS]
    return USER_DATA[uid]


def build_pdf(firms, path, username="Danyla Kasprun"):
    DARK = colors.HexColor("#1a1a2e")
    GOLD = colors.HexColor("#e0c97f")
    CAT = {
        "Krankenhaus": colors.HexColor("#ffe0e8"),
        "Polizei": colors.HexColor("#e8eeff"),
        "Bundeswehr": colors.HexColor("#e0f5e8"),
        "Feuerwehr": colors.HexColor("#fff3e0"),
        "Rettung": colors.HexColor("#fff3e0"),
        "Behoerde": colors.HexColor("#f3e8ff"),
        "Bildung": colors.HexColor("#e8f4ff"),
        "Privat": colors.HexColor("#fafaf7"),
    }
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=1.2*cm, rightMargin=1.2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    sub = ParagraphStyle("s", fontSize=8, fontName="Helvetica", spaceAfter=2)
    tit = ParagraphStyle("t", fontSize=13, fontName="Helvetica-Bold", spaceAfter=4)
    sml = ParagraphStyle("m", fontSize=7.5, fontName="Helvetica", leading=10)
    tiny = ParagraphStyle("y", fontSize=7, fontName="Helvetica", leading=9)
    story = [
        Paragraph("IFP - Gesellschaft fuer Fortbildung und Personalentwicklung MbH", sub),
        Paragraph("Bewerbungsaktivitaeten - Fachinformatiker Ausbildung 2026", tit),
        Paragraph("Straubing und Umgebung 50km | Name: " + username + " | 16.03.2026", sub),
        Spacer(1, 0.3*cm),
    ]
    headers = ["#", "Datum", "Firma", "Ort", "E-Mail", "Bereich", "Art", "Ergebnis"]
    cw = [0.6*cm, 1.3*cm, 5.6*cm, 2.8*cm, 5.2*cm, 5.0*cm, 2.0*cm, 2.8*cm]
    hrow = [Paragraph("<b>" + h + "</b>", ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold", textColor=GOLD, leading=10)) for h in headers]
    data = [hrow]
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("BOX", (0, 0), (-1, -1), 0.8, DARK),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, f in enumerate(firms):
        kat = f.get("kategorie", "Privat")
        bg = CAT.get(kat, colors.HexColor("#fafaf7"))
        cmds.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))
        data.append([
            Paragraph(str(i+1), tiny),
            Paragraph(f["datum"], sml),
            Paragraph("<b>" + f["firma"] + "</b>", sml),
            Paragraph(f["ort"], sml),
            Paragraph(f["kontakt"], tiny),
            Paragraph(f["bereich"], tiny),
            Paragraph(f["art"], tiny),
            Paragraph(f.get("ergebnis", "") or "", tiny),
        ])
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(str(len(firms)) + " Eintraege - 16.03.2026", ParagraphStyle("ft", fontSize=7, fontName="Helvetica", textColor=colors.HexColor("#888888"))))
    doc.build(story)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "User"
    await update.message.reply_text(
        "Hallo " + name + "! Ich bin dein Ausbildungs-Assistent.\n\n"
        "Ich helfe dir, Ausbildungsplaetze als Fachinformatiker in Straubing (50km) zu verwalten.\n\n"
        "Befehle:\n"
        "/list - Alle Firmen anzeigen\n"
        "/search - Neue Firmen per KI suchen\n"
        "/pdf - PDF-Tabelle herunterladen\n"
        "/result - Ergebnis eintragen\n"
        "/stats - Statistik\n"
        "/help - Hilfe"
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    firms = get_firms(uid)
    by_kat = {}
    zusagen = absagen = offen = 0
    for f in firms:
        k = f.get("kategorie", "Privat")
        by_kat[k] = by_kat.get(k, 0) + 1
        e = (f.get("ergebnis") or "").lower()
        if "zusage" in e or "einladung" in e:
            zusagen += 1
        elif "absage" in e:
            absagen += 1
        else:
            offen += 1
    lines = ["Statistik - " + str(len(firms)) + " Bewerbungen\n"]
    for k, n in sorted(by_kat.items(), key=lambda x: -x[1]):
        lines.append(k + ": " + str(n))
    lines.append("\nZusagen/Einladungen: " + str(zusagen))
    lines.append("Absagen: " + str(absagen))
    lines.append("Offen: " + str(offen))
    await update.message.reply_text("\n".join(lines))


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    firms = get_firms(uid)
    by_kat = {}
    for f in firms:
        k = f.get("kategorie", "Privat")
        by_kat.setdefault(k, []).append(f)
    for kat, items in by_kat.items():
        lines = [kat + " (" + str(len(items)) + ")\n"]
        for f in items:
            e = f.get("ergebnis", "")
            status = ""
            if e:
                el = e.lower()
                if "zusage" in el or "einladung" in el:
                    status = " [+]"
                elif "absage" in el:
                    status = " [-]"
                else:
                    status = " [" + e[:12] + "]"
            lines.append("#" + str(f["id"]) + " " + f["firma"] + " - " + f["kontakt"] + status)
        msg = "\n".join(lines)
        if len(msg) > 4000:
            msg = msg[:4000] + "..."
        await update.message.reply_text(msg)


async def cmd_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    firms = get_firms(uid)
    await update.message.reply_text("PDF wird erstellt...")
    path = "/tmp/bew_" + str(uid) + ".pdf"
    name = update.effective_user.full_name or "Danyla Kasprun"
    build_pdf(firms, path, name)
    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename="Bewerbungsaktivitaeten_Kasprun.pdf",
            caption="Deine Bewerbungstabelle - " + str(len(firms)) + " Eintraege"
        )


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    firms = get_firms(uid)
    await update.message.reply_text("KI sucht neue Firmen... bitte warten.")
    existing = ", ".join(f["firma"] for f in firms)
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system='Du bist ein Ausbildungsplatz-Agent fuer Fachinformatiker in Straubing 50km. Gib NUR JSON-Array zurueck ohne Text ohne Backticks. Format: [{"datum":"TT.MM","firma":"Name","ort":"Stadt","kontakt":"email@firma.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"}]',
            messages=[{"role": "user", "content": "Finde 5 neue Firmen NICHT: " + existing + " in 50km Straubing die Fachinformatiker ausbilden. Datum 17.03"}]
        )
        raw = msg.content[0].text.strip().replace("```json", "").replace("```", "")
        new_rows = json.loads(raw)
        if isinstance(new_rows, list) and new_rows:
            max_id = max(f["id"] for f in firms)
            for i, r in enumerate(new_rows):
                r["id"] = max_id + i + 1
                r.setdefault("ergebnis", "")
                r.setdefault("kategorie", "Privat")
                firms.append(r)
            lines = [str(len(new_rows)) + " neue Firmen gefunden!\n"]
            for r in new_rows:
                lines.append(r["firma"] + " - " + r["ort"] + "\n  " + r["kontakt"])
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("Keine neuen Firmen gefunden.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Fehler: " + str(e))


async def cmd_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    firms = get_firms(uid)
    keyboard = []
    for f in firms:
        e = f.get("ergebnis", "")
        if e:
            el = e.lower()
            s = "[+]" if ("zusage" in el or "einladung" in el) else "[-]" if "absage" in el else "[?]"
        else:
            s = "[ ]"
        label = s + " #" + str(f["id"]) + " " + f["firma"][:28]
        keyboard.append([InlineKeyboardButton(label, callback_data="rf_" + str(f["id"]))])
    await update.message.reply_text("Waehle eine Firma:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FIRMA


async def cb_firma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = int(query.data.split("_")[1])
    ctx.user_data["fid"] = fid
    uid = update.effective_user.id
    firms = get_firms(uid)
    firma = next((f for f in firms if f["id"] == fid), None)
    if not firma:
        await query.edit_message_text("Firma nicht gefunden.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton("Einladung zum Gespraech", callback_data="rv_Einladung zum Vorstellungsgespraech")],
        [InlineKeyboardButton("Zusage erhalten", callback_data="rv_Zusage erhalten")],
        [InlineKeyboardButton("Absage erhalten", callback_data="rv_Absage erhalten")],
        [InlineKeyboardButton("Bewerbung gesendet", callback_data="rv_Bewerbung gesendet")],
        [InlineKeyboardButton("Rueckruf erhalten", callback_data="rv_Rueckruf erhalten")],
        [InlineKeyboardButton("Eigenen Text eingeben", callback_data="rv_CUSTOM")],
    ]
    await query.edit_message_text(firma["firma"] + "\n\nWaehle das Ergebnis:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_TEXT


async def cb_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    value = query.data[3:]
    if value == "CUSTOM":
        await query.edit_message_text("Schreibe dein Ergebnis:")
        return WAITING_TEXT
    return await save_result(update, ctx, value)


async def msg_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return await save_result(update, ctx, update.message.text)


async def save_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE, value: str):
    uid = update.effective_user.id
    firms = get_firms(uid)
    fid = ctx.user_data.get("fid")
    firma = next((f for f in firms if f["id"] == fid), None)
    if firma:
        firma["ergebnis"] = value
        msg = "Gespeichert!\n\n" + firma["firma"] + "\n-> " + value
    else:
        msg = "Firma nicht gefunden."
    if update.callback_query:
        await update.callback_query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN nicht gesetzt!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("result", cmd_result)],
        states={
            WAITING_FIRMA: [CallbackQueryHandler(cb_firma, pattern=r"^rf_\d+$")],
            WAITING_TEXT: [
                CallbackQueryHandler(cb_text, pattern=r"^rv_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_text),
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("pdf", cmd_pdf))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(conv)
    logger.info("Bot gestartet!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
