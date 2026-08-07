/*  РЕЛЕ ЗАЯВОК ЛЕНДИНГА Smart Attic → Telegram + e-mail
    ─────────────────────────────────────────────────────────────────────
    Розгортається на script.google.com. Форми лендинга шлють сюди
    {name, phone, note} методом POST з тілом text/plain.

    ⚠️  ДВА КРОКИ, БЕЗ ЯКИХ ЗАЯВКИ НЕ ДОХОДЯТЬ:

    1. Вписати справжній токен бота в BOT_TOKEN (без дужок < >).

    2. При розгортанні (Deploy → New deployment → Web app) виставити:
         Execute as:    Me
         Who has access: ANYONE            ← не «Anyone with Google account»
       Якщо тут стоїть щось інше, ендпоінт віддає 403 «Потрібен доступ»
       усім відвідувачам сайту. Саме так заявки й губилися.

       Перевірка: відкрий /exec у вікні інкогніто. Має бути напис
       "Smart Attic relay alive". Якщо бачиш сторінку Google про доступ —
       розгортання закрите.

    ⚠️  Після кожної правки коду треба саме NEW DEPLOYMENT (або Manage
        deployments → Edit → Version: New version). Просто зберегти файл
        недостатньо: на /exec лишиться стара версія.
*/

// ===================== НАЛАШТУВАННЯ =====================
const BOT_TOKEN = "1753703916:ВСТАВ_РЕШТУ_ТОКЕНА";  // <-- справжній токен від @BotFather, без < >
const CHAT_ID   = "918580618";                       // Telegram chat_id Григорія (звірено 07.08.2026)
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

    // Пробуємо обидва канали незалежно: якщо Telegram відвалився,
    // пошта все одно має піти, і навпаки.
    var problems = [];

    try {
      sendTelegram(msg);
    } catch (tgErr) {
      problems.push("telegram: " + tgErr.message);
    }

    if (EMAIL_TO) {
      try {
        MailApp.sendEmail(EMAIL_TO, "Заявка з лендинга Smart Attic", msg);
      } catch (mailErr) {
        problems.push("email: " + mailErr.message);
      }
    }

    // Сторінка вважає успіхом тільки відповідь "ok". Якщо жоден канал не
    // спрацював — чесно кажемо про помилку, щоб відвідувач побачив
    // запасні контакти, а не фальшиве «Дякую».
    if (problems.length === (EMAIL_TO ? 2 : 1)) {
      return reply("error: " + problems.join(" | "));
    }

    // Один канал з двох упав: заявка в нас є, але це варто знати.
    if (problems.length) {
      console.warn("Заявка дійшла частково — " + problems.join(" | "));
    }

    return reply("ok");
  } catch (err) {
    return reply("error: " + err.message);
  }
}

function sendTelegram(text) {
  if (!BOT_TOKEN || BOT_TOKEN.indexOf("ВСТАВ") !== -1) {
    throw new Error("BOT_TOKEN не заповнений");
  }
  var res = UrlFetchApp.fetch(
    "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage",
    {
      method: "post",
      payload: { chat_id: CHAT_ID, text: text, disable_web_page_preview: "true" },
      muteHttpExceptions: true
    }
  );
  // Раніше відповідь не перевірялася взагалі: при битому токені реле
  // однаково рапортувало «ok», а повідомлення нікуди не йшло.
  var code = res.getResponseCode();
  if (code !== 200) {
    throw new Error("Telegram HTTP " + code + " — " + res.getContentText().slice(0, 200));
  }
  var body = JSON.parse(res.getContentText());
  if (!body.ok) {
    throw new Error("Telegram: " + (body.description || "невідома помилка"));
  }
}

function reply(text) {
  return ContentService.createTextOutput(text)
                       .setMimeType(ContentService.MimeType.TEXT);
}

// Перевірка, що ендпоінт живий — відкрити URL у вікні інкогніто.
function doGet() {
  return reply("Smart Attic relay alive");
}

/*  Разова самоперевірка. Запусти вручну в редакторі Apps Script
    (обери testRelay у списку функцій → Run) і подивись у Executions:
    так видно справжню помилку Telegram, не виходячи на сайт.          */
function testRelay() {
  try {
    sendTelegram("🧪 Тест реле Smart Attic — якщо ти це бачиш, Telegram працює.");
    console.log("Telegram: ok");
  } catch (err) {
    console.error("Telegram НЕ працює: " + err.message);
  }
  if (EMAIL_TO) {
    MailApp.sendEmail(EMAIL_TO, "Тест реле Smart Attic", "Пошта працює.");
    console.log("Email надіслано на " + EMAIL_TO);
  }
}
