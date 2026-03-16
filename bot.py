import os
import json
import logging
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

WAITING_RESULT_FIRMA = 1
WAITING_RESULT_TEXT  = 2

COMPANIES_DEFAULT = [
    {"id":1,  "datum":"08.03","firma":"Rub + GmbH","ort":"Straubing","kontakt":"info@rub.com","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":2,  "datum":"04.03","firma":"Autohaus Kuschnow Straubing","ort":"Straubing","kontakt":"info@kv-schnupp.eu","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":3,  "datum":"08.03","firma":"IT Box GmbH IS+ Rauning","ort":"Rauning","kontakt":"team@it-box.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":4,  "datum":"09.03","firma":"Technische Hochschule Deggendorf","ort":"Deggendorf (~30km)","kontakt":"info@th-dg.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Bildung"},
    {"id":5,  "datum":"08.03","firma":"RPS Industry GmbH Straubing","ort":"Straubing","kontakt":"info@rpsindustry.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":6,  "datum":"07.03","firma":"Hendrickson AG Straubing","ort":"Straubing","kontakt":"info@hendrickson.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":7,  "datum":"08.03","firma":"Institut fuer angew. Logistik GmbH","ort":"Deggendorf (~30km)","kontakt":"ial-bo@ial.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Bildung"},
    {"id":8,  "datum":"08.03","firma":"Helmut Holz","ort":"Straubing","kontakt":"info@romanold.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":9,  "datum":"08.03","firma":"IFA Technology GmbH Reut","ort":"Reut","kontakt":"anmeldung@ifa-technology.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":10, "datum":"10.03","firma":"Landratsamt Straubing-Bogen","ort":"Straubing","kontakt":"pauline.s@straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":11, "datum":"10.03","firma":"Stadt Straubing (Stadtamt)","ort":"Straubing","kontakt":"stadtamt@straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":12, "datum":"10.03","firma":"Agentur fuer Arbeit Regensburg","ort":"Regensburg (~45km)","kontakt":"regensburg@arbeitsagentur.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":13, "datum":"11.03","firma":"Volksbank Straubing","ort":"Straubing","kontakt":"info@volksbank-straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":14, "datum":"11.03","firma":"Raiffeisenbank Straubing","ort":"Straubing","kontakt":"info@rb-straubing.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":15, "datum":"11.03","firma":"MediaMarkt Straubing","ort":"Straubing","kontakt":"ausbildung@mediamarkt.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":16, "datum":"16.03","firma":"Klinikum Straubing Barmherzige Brueder","ort":"Straubing","kontakt":"bewerbung@klinikum-straubing.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":17, "datum":"16.03","firma":"DONAUISAR Klinikum Deggendorf","ort":"Deggendorf (~30km)","kontakt":"personal@donau-isar-klinikum.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":18, "datum":"16.03","firma":"Barmherzige Brueder Regensburg","ort":"Regensburg (~45km)","kontakt":"ausbildung@barmherzige-regensburg.de","bereich":"Fachinformatiker alle Fachrichtungen","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":19, "datum":"16.03","firma":"Kreisklinik Bogen","ort":"Bogen (~15km)","kontakt":"info@kreisklinik-bogen.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus"},
    {"id":20, "datum":"16.03","firma":"Polizeipraesidium Niederbayern","ort":"Straubing","kontakt":"pp-nby.ausbildung@polizei.bayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":21, "datum":"16.03","firma":"Polizeiinspektion Straubing","ort":"Straubing","kontakt":"pi-straubing@polizei.bayern.de","bereich":"Fachinformatiker IT-Bereich","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":22, "datum":"16.03","firma":"Kriminalpolizeiinspektion Straubing","ort":"Straubing","kontakt":"kpi-straubing@polizei.bayern.de","bereich":"Fachinformatiker IT-Forensik","art":"per E-Mail","ergebnis":"","kategorie":"Polizei"},
    {"id":23, "datum":"16.03","firma":"Bundeswehr-DLZ Bogen","ort":"Bogen (~15km)","kontakt":"bwdlz-bogen@bundeswehr.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Bundeswehr"},
    {"id":24, "datum":"16.03","firma":"Karrierecenter Bundeswehr Regensburg","ort":"Regensburg (~45km)","kontakt":"kcbw-regensburg@bundeswehr.de","bereich":"Fachinformatiker IT-Ausbildung","art":"per E-Mail","ergebnis":"","kategorie":"Bundeswehr"},
    {"id":25, "datum":"16.03","firma":"Feuerwehr Straubing Berufsfeuerwehr","ort":"Straubing","kontakt":"feuerwehr@straubing.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Feuerwehr"},
    {"id":26, "datum":"16.03","firma":"Integrierte Leitstelle Straubing ILS","ort":"Straubing","kontakt":"ils-straubing@ils-niederbayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Feuerwehr"},
    {"id":27, "datum":"16.03","firma":"Bayerisches Rotes Kreuz KV Straubing","ort":"Straubing","kontakt":"info@kvstraubing.brk.de","bereich":"Fachinformatiker IT/Verwaltung","art":"per E-Mail","ergebnis":"","kategorie":"Rettung"},
    {"id":28, "datum":"16.03","firma":"Finanzamt Straubing","ort":"Straubing","kontakt":"poststelle@fa-sr.bayern.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":29, "datum":"16.03","firma":"Regierung von Niederbayern","ort":"Landshut (~45km)","kontakt":"poststelle@reg-nb.bayern.de","bereich":"Fachinformatiker IT-Verwaltung","art":"per E-Mail","ergebnis":"","kategorie":"Behoerde"},
    {"id":30, "datum":"16.03","firma":"TakeData Systems GmbH","ort":"Straubing","kontakt":"jobs@takedata.de","bereich":"Fachinformatiker Systemintegration","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
    {"id":31, "datum":"16.03","firma":"Weum eier AC FDV","ort":"Straubing","kontakt":"D.Neumeter@aclv.de","bereich":"Fachinformatiker","art":"per E-Mail","ergebnis":"","kategorie":"Privat"},
]

KAT_EMOJI = {
    "Krankenhaus":"Krankenhaus",
    "Polizei":"Polizei",
    "Bundeswehr":"Bundeswehr",
    "Feuerwehr":"Feuerwehr",
    "Rettung":"Rettung",
    "Behoerde":"Behoerde",
    "Bildung":"Bildung",
    "Privat":"Privat"
}

USER_DATA = {}

def get_companies(user_id):
    if user_id not in USER_DATA:
        USER_DATA[user_id] = [c.copy() for c in COMPANIES_DEFAULT]
    return USER_DATA[user_id]


def build_pdf(companies, path, user_name="Danyla Kasprun"):
    DARK  = colors.HexColor("#1a1a2e")
    GOLD  = colors.HexColor("#e0c97f")
    CAT_C = {
        "Krankenhaus": colors.HexColor("#ffe0e8"),
        "Polizei":     colors.HexColor("#e8eeff"),
        "Bundeswehr":  colors.HexColor("#e0f5e8"),
        "Feuerwehr":   colors.HexColor("#fff3e0"),
        "Rettung":     colors.HexColor("#fff3e0"),
        "Behoerde":    colors.HexColor("#f3e8ff"),
        "Bildung":     colors.HexColor("#e8f4ff"),
        "Privat":      colors.HexColor("#fafaf7"),
    }
    doc = SimpleDocTemplate(path, pagesize=landscape(A4),
                            leftMargin=1.2*cm, rightMargin=1.2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    sub  = ParagraphStyle("sub",  fontSize=8,  fontName="Helvetica", spaceAfter=2)
    titl = ParagraphStyle("titl", fontSize=13, fontName="Helvetica-Bold", spaceAfter=4)
    tiny = ParagraphStyle("tiny", fontSize=7,  fontName="Helvetica", leading=9)
    sml  = ParagraphStyle("sml",  fontSize=7.5,fontName="Helvetica", leading=10)

    story = [
        Paragraph("IFP - Gesellschaft fuer Fortbildung und Personalentwicklung MbH", sub),
        Paragraph("Bewerbungsaktivitaeten - Fachinformatiker Ausbildung 2026", titl),
        Paragraph("Straubing & Umgebung - 50km Radius   |   Name: " + user_name + "   |   Ausgabe 2.0, 16.03.2026", sub),
        Spacer(1, 0.3*cm),
    ]
    headers = ["#","Datum","Firma / Institution","Ort","Kontakt (E-Mail)","Taetigkeitsbereich","Art","Ergebnis"]
    col_w   = [0.6*cm,1.3*cm,5.6*cm,3.0*cm,5.4*cm,5.0*cm,2.1*cm,2.8*cm]
    hdr_row = [Paragraph("<b>" + h + "</b>",
               ParagraphStyle("h", fontSize=8, fontName="Helvetica-Bold",
                              textColor=GOLD, leading=10)) for h in headers]
    data = [hdr_row]
    cmds = [
        ("BACKGROUND",(0,0),(-1,0),DARK),
        ("BOX",(0,0),(-1,-1),0.8,DARK),
        ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
    ]
    for i, c in enumerate(companies):
        kat = c.get("kategorie","Privat")
        bg  = CAT_C.get(kat, colors.HexColor("#fafaf7"))
        cmds.append(("BACKGROUND",(0,i+1),(-1,i+1),bg))
        data.append([
            Paragraph(str(i+1), tiny),
            Paragraph(c["datum"], sml),
            Paragraph("<b>" + c["firma"] + "</b>", sml),
            Paragraph(c["ort"], sml),
            Paragraph(c["kontakt"], tiny),
            Paragraph(c["bereich"], tiny),
            Paragraph(c["art"], tiny),
            Paragraph(c.get("ergebnis","") or "", tiny),
        ])
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Bewerbungsaktivitaeten - " + str(len(companies)) + " Eintraege - 16.03.2026",
        ParagraphStyle("ft", fontSize=7, fontName="Helvetica",
                       textColor=colors.HexColor("#888888"))
    ))
    doc.build(story)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = (
        "Hallo " + name + "! Ich bin dein Ausbildungs-Assistent.\n\n"
        "Ich helfe dir, Ausbildungsplaetze als Fachinformatiker in Straubing (50km) zu verwalten.\n\n"
        "Befehle:\n"
        "/list - Alle Firmen anzeigen\n"
        "/search - Neue Firmen per KI suchen\n"
        "/pdf - PDF-Tabelle herunterladen\n"
        "/result - Ergebnis einer Bewerbung eintragen\n"
        "/stats - Statistik anzeigen\n"
        "/help - Hilfe"
    )
    await update.message.reply_text(text)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    companies = get_companies(uid)
    total = len(companies)
    by_kat = {}
    zusagen = absagen = offen = 0
    for c in companies:
        kat = c.get("kategorie","Privat")
        by_kat[kat] = by_kat.get(kat, 0) + 1
        e = (c.get("ergebnis") or "").lower()
        if "zusage" in e or "einladung" in e:
            zusagen += 1
        elif "absage" in e:
            absagen += 1
        else:
            offen += 1
    lines = ["Statistik - " + str(total) + " Bewerbungen\n"]
    for kat, n in sorted(by_kat.items(), key=lambda x: -x[1]):
        lines.append(kat + ": " + str(n))
    lines.append("\nZusagen/Einladungen: " + str(zusagen))
    lines.append("Absagen: " + str(absagen))
    lines.append("Offen: " + str(offen))
    await update.message.reply_text("\n".join(lines))


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    companies = get_companies(uid)
    by_kat = {}
    for c in companies:
        k = c.get("kategorie","Privat")
        by_kat.setdefault(k, []).append(c)
    for kat, items in by_kat.items():
        lines = [kat + " (" + str(len(items)) + ")\n"]
        for c in items:
            e = c.get("ergebnis","")
            status = ""
            if e:
                el = e.lower()
                if "zusage" in el or "einladung" in el:
                    status = " [Zusage]"
                elif "absage" in el:
                    status = " [Absage]"
                else:
                    status = " [" + e[:15] + "]"
            lines.append("#" + str(c["id"]) + " " + c["firma"] + " - " + c["kontakt"] + status)
        msg = "\n".join(lines)
        if len(msg) > 4000:
            msg = msg[:4000] + "..."
        await update.message.reply_text(msg)


async def cmd_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    companies = get_companies(uid)
    await update.message.reply_text("PDF wird erstellt...")
    path = "/tmp/bewerbung_" + str(uid) + ".pdf"
    name = update.effective_user.full_name or "Danyla Kasprun"
    build_pdf(companies, path, name)
    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename="Bewerbungsaktivitaeten_Kasprun.pdf",
            caption="Deine Bewerbungstabelle mit " + str(len(companies)) + " Eintraegen. 16.03.2026 - Straubing 50km"
        )


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    companies = get_companies(uid)
    await update.message.reply_text("KI sucht neue Firmen... bitte warten.")
    existing = ", ".join(c["firma"] for c in companies)
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=(
                "Du bist ein Ausbildungsplatz-Agent fuer Fachinformatiker in Straubing 50km Radius. "
                "Gib NUR ein JSON-Array zurueck, ohne Text, ohne Backticks. "
                'Format: [{"datum":"TT.MM","firma":"Name","ort":"Stadt",'
                '"kontakt":"email@firma.de","bereich":"Fachinformatiker Systemintegration",'
                '"art":"per E-Mail","ergebnis":"","kategorie":"Krankenhaus oder Polizei oder Bundeswehr oder Feuerwehr oder Rettung oder Behoerde oder Bildung oder Privat"}]'
            ),
            messages=[{"role":"user","content":
                "Finde 5 neue Firmen (NICHT: " + existing + ") in 50km Straubing die Fachinformatiker ausbilden. Datum 16.03"
            }]
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","")
        new_rows = json.loads(raw)
        if isinstance(new_rows, list) and new_rows:
            max_id = max(c["id"] for c in companies)
            for i, r in enumerate(new_rows):
                r["id"] = max_id + i + 1
                r.setdefault("ergebnis","")
                r.setdefault("kategorie","Privat")
                companies.append(r)
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
    companies = get_companies(uid)
    keyboard = []
    for c in companies:
        e = c.get("ergebnis","")
        if e:
            el = e.lower()
            status = "[+]" if ("zusage" in el or "einladung" in el) else "[-]" if "absage" in el else "[?]"
        else:
            status = "[ ]"
        label = status + " #" + str(c["id"]) + " " + c["firma"][:28]
        keyboard.append([InlineKeyboardButton(label, callback_data="result_" + str(c["id"]))])
    await update.message.reply_text(
        "Waehle eine Firma fuer das Ergebnis:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_RESULT_FIRMA


async def callback_result_firma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    firma_id = int(query.data.split("_")[1])
    ctx.user_data["result_firma_id"] = firma_id
    uid = update.effective_user.id
    companies = get_companies(uid)
    firma = next((c for c in companies if c["id"]==firma_id), None)
    if not firma:
        await query.edit_message_text("Firma nicht gefunden.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton("Einladung zum Vorstellungsgespraech", callback_data="res_Einladung zum Vorstellungsgespraech")],
        [InlineKeyboardButton("Zusage erhalten", callback_data="res_Zusage erhalten")],
        [InlineKeyboardButton("Absage erhalten", callback_data="res_Absage erhalten")],
        [InlineKeyboardButton("Bewerbung gesendet", callback_data="res_Bewerbung gesendet")],
        [InlineKeyboardButton("Rueckruf erhalten", callback_data="res_Rueckruf erhalten")],
        [InlineKeyboardButton("Eigenen Text eingeben", callback_data="res_CUSTOM")],
    ]
    await query.edit_message_text(
        firma["firma"] + "\n\nWaehle das Ergebnis:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_RESULT_TEXT


async def callback_result_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    value = query.data[4:]
    if value == "CUSTOM":
        await query.edit_message_text("Bitte schreibe dein Ergebnis als Text:")
        return WAITING_RESULT_TEXT
    return await _save_result(update, ctx, value)


async def msg_custom_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return await _save_result(update, ctx, update.message.text)


async def _save_result(update: Update, ctx: ContextTypes.DEFAULT_TYPE, value: str):
    uid = update.effective_user.id
    companies = get_companies(uid)
    firma_id = ctx.user_data.get("result_firma_id")
    firma = next((c for c in companies if c["id"]==firma_id), None)
    if firma:
        firma["ergebnis"] = value
        msg = "Ergebnis gespeichert!\n\n" + firma["firma"] + "\n-> " + value
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
            WAITING_RESULT_FIRMA: [CallbackQueryHandler(callback_result_firma, pattern=r"^result_\d+$")],
            WAITING_RESULT_TEXT:  [
                CallbackQueryHandler(callback_result_text, pattern=r"^res_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_custom_result),
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("pdf",    cmd_pdf))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("stats",  cmd_stats))
    app.add_handler(conv)

    logger.info("Bot gestartet!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
