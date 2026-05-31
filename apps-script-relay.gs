/*  РЕЛЕ ЗАЯВОК ЛЕНДИНГА Smart Attic → Telegram + e-mail
    Розгортається на script.google.com. Форми лендинга шлють сюди {name, phone, note}.
    Єдине, що треба вписати вручну — СПРАВЖНІЙ токен бота @Gregory_Ivd_bot (рядок BOT_TOKEN), БЕЗ дужок < >.
*/

// ===================== НАЛАШТУВАННЯ =====================
const BOT_TOKEN = "1753703916:ВСТАВ_РЕШТУ_ТОКЕНА";  // <-- справжній токен від @BotFather, без < >
const CHAT_ID   = "8910651331";                      // Telegram chat_id Григорія
const EMAIL_TO  = "apshanuivd@gmail.com";            // дубль заявки на пошту ("" — вимкнути)
// ========================================================

function doPost(e) {
  try {
    var p = JSON.parse(e.postData.contents);
    var name  = p.name  || "—";
    var phone = p.phone || "—";
    var note  = p.note  || "";
    var msg = "🟢 Нова заявка з лендинга Smart Attic\n\n"
            + "👤 " + name + "\n"
            + "📞 " + phone
            + (note ? ("\n📝 " + note) : "");

    sendTelegram(msg);
    if (EMAIL_TO) {
      MailApp.sendEmail(EMAIL_TO, "Заявка з лендинга Smart Attic", msg);
    }
    return ContentService.createTextOutput("ok");
  } catch (err) {
    return ContentService.createTextOutput("error: " + err);
  }
}

function sendTelegram(text) {
  UrlFetchApp.fetch("https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage", {
    method: "post",
    payload: { chat_id: CHAT_ID, text: text, disable_web_page_preview: "true" },
    muteHttpExceptions: true
  });
}

// перевірка, що ендпоінт живий — відкрити URL у браузері
function doGet() {
  return ContentService.createTextOutput("Smart Attic relay alive");
}
