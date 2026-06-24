# Google API Installation Guide — Gmail & Calendar (Dr. Yoram Segal)


## **Google APIs שילוב ממשקי** 

# **TokenוClient מדריך שלב-אחר-שלב להגדרת** 

## **Google CalendarוGmail עבור** 

**Integrating Google APIs: A Step­by­Step Guide to Client and Token Setup for Gmail & Calendar** 

ד”ר יורם סגל 

–כל הזכויות שמורות ©Dr. Yoram Segal 

May 2026 

_הספר נכתב בלשון זכר מטעמי נוחות וקיצור בלבד, אך הוא פונה ומיועד לכל המגדרים כאחד._

## **תוכן העניינים** 

|1מילות מפתח. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .4|
|---|
|2מבוא. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .4|
|3מטרה<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .4|
|4לפני שמתחילים. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .5|
|5שלב1<br>:בחירת סוג ה-<br>Credentialהנכון<br>. . . . . . . . . . . . . . . . . . . . .5|
|5.1למה לבחורOAuth client ID<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>6|
|6שלב2<br>:התחלת יצירת ה-<br>OAuth Client<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>6|
|7שלב3<br>:כניסה ל-<br>Google Auth Platform<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>6|
|7.1דרך א: מתוךGoogle Cloud Console<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>7|
|7.2דרך ב: דרך קישור ישיר<br>. . . . . . . . . . . . . . . . . . . . . . . .7|
|7.3הערה חשובה. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .8|
|8שלב4<br>:מסך הפתיחה שלGoogle Auth Platform<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>8|
|9שלב5<br>:מילוי פרטי האפליקציה<br>. . . . . . . . . . . . . . . . . . . . . . . . .9|
|10שלב6<br>:בחירת קהל היעד של האפליקציה. . . . . . . . . . . . . . . . . . .9|
|10.1למה לבחורExternal<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>9|
|11שלב7<br>:הזנת כתובת איש הקשר. . . . . . . . . . . . . . . . . . . . . . . .10|
|12שלב8<br>:הפעלתGmail API<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>10|
|13שלב9<br>:הפעלתGoogle Calendar API<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>11|
|14שלב10<br>:חזרה ל-<br>Google Auth Platformלאחר הפעלתAPI<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>11|
|15שלב11<br>:היכרות עם מסך ה-<br>Overviewבממשק החדש. . . . . . . . . . . .12|
|16שלב12<br>:הגדרת ההרשאות המדויקות ב-<br>Data access<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>13|
|16.1פירוש ההרשאות<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . .13|
|17שלב13<br>:יצירתOAuth ClientמסוגDesktop<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>13|
|17.1איך נראה המסך לאחר יצירת הלקוח. . . . . . . . . . . . . . . . .14|
|18שלב14<br>:הוספת משתמש בדיקה )Test user<br>(<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>14|
|19שלב15<br>:קובץ פייתון לבדיקה<br>. . . . . . . . . . . . . . . . . . . . . . . . .15|
|20שלב16<br>:התקנתuvוהרצת תוכנית הבדיקה. . . . . . . . . . . . . . . . . .16|
|20.1התקנתuvב-<br>Windows PowerShell<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>16|
|20.2התקנתuvב-<br>macOS / Linux<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>16|
|20.3קובץpyproject.toml<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>.<br>17|
|20.4הרצה<br>. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .17|
|21בדיקות סופיות. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .17|
|22תקלות נפוצות ופתרון מהיר. . . . . . . . . . . . . . . . . . . . . . . . . . .18|
|22.1שגיאה:Access blockedאוThis app isn't verified<br>.<br>18|
|22.2שגיאה: ההתחברות לא מצליחה למרות שה-<br>Clientנוצר. . . . . . .18|
|22.3שגיאה: הקוד מבקש הרשאות ישנות<br>. . . . . . . . . . . . . . . . .18|



–כל הזכויות שמורות © Dr. Yoram Segal 

2

## **רשימת האיורים** 

- 5 . . . Create credentials בתפריט OAuth client ID יצירת אישורים — בחירת 1 6 . . . . . Configure consent screen עם הכפתור Create OAuth client ID מסך 2 — 

- אינו גלוי Google Auth Platform Google Cloud תפריט הצד הראשי של 3 

- 7 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . בקלות 8 . . . . . .המשך גלילה בתפריט הראשי — הפריט עדיין אינו נגיש ישירות 4 8 . . . Get started עם הכפתור Google auth platform not configured yet מסך 5 9 . . . . . . . . . . . . . . ExternalלInternal —בחירה בין Audience מסך 6 10 . . . . . . . . . . . . . Email addresses —שדה Contact Information מסך 7 11 . . . . . . . . . . . . . . . Enabled במצב Google Calendar API מסך פרטי 8 12 . APIsלאחר הפעלת ה- Google Auth PlatformבOAuth overviewחזרה ל- 9 12 . . . . . . . . . . . . . . . Create OAuth client עם הכפתור Overview מסך 10 

©Dr. Yoram Segal כל הזכויות שמורות – 

3

## **מילות מפתח 1** 

token.json ,credentials.json ,OAuth client ID ,OAuth 2.0 - - APIs & Ser­ ,Google Auth Platform ,Google Cloud Console vices Test users ,Scopes ,Google Calendar API ,Gmail API - - Data access ,Audience ,Branding ,Desktop application google­auth­oauthlib ,google­api­python­client ,uv -פייתון, 

בשל עדכוני המערכת התכופים של גוגל, ייתכנו הבדלים בין צילומי המסך **הערה:** והתפריטים המוצגים במדריך זה לבין הממשק בפועל. במידה ואינכם מאתרים רכיב )מודל שפה( לקבלת הכוונה מותאמת אישית. מומלץ LLMמסוים, מומלץ להסתייע ב- לצרף לפנייה תצלום מסך והסבר של המטרה המבוקשת, על מנת לקבל מענה מדויק ורלוונטי למערכת שלכם. 

**מבוא 2** 

עבור **OAuth Client** מדריך זה מרכז את כל השלבים הנכונים, הקצרים והמעודכנים ליצירת ,הורדת קובץ **Test User** ,כולל הוספתGoogle Calendarול־ Gmailתוכנית פייתון שמתחברת ל־ GoogleAuth הלקוח, והרצת תוכנית בדיקה בסיסית. ההוראות מותאמות לממשק החדש של APIs & Services כפי שהופיע בפועל במהלך העבודה, ולא רק למבנה הישן של Platform 

שמופיע בחוברת המקורית. 

**==> picture [59 x 11] intentionally omitted <==**

את כל הרכיבים הבאים: Google Cloud המטרה היא להגיע למצב שבו יש בפרויקט 

מופעל. Gmail API - 

מופעל. Google Calendar API - 

. **Google Auth Platform** הוגדר בממשק החדש של OAuth -מסך 

-הוגדרו ההרשאות המדויקות: 

.https://www.googleapis.com/auth/gmail.modify - .https://www.googleapis.com/auth/calendar - 

–כל הזכויות שמורות © Dr. Yoram Segal 

4

.Desktop מסוג **OAuth Client** -נוצר 

.Testing כדי שההתחברות תעבוד במצב **Test User** -הוסף 

עבור קוד פייתון. credentials.json -הורד קובץ 

## **לפני שמתחילים 4** 

יש לוודא אחד קבוע מתחילת התהליך ועד סופו. Google Cloud יש לעבוד עם פרויקט שבחלק העליון של המסך נבחר הפרויקט הנכון לפני כל פעולה. 

בממשק החדש יש שני אזורי עבודה שונים: 

- .Google CalendarAPIו־ GmailAPI כמו APIs —משמש להפעלת **APIs & Services** - Clients ,Data access ,Audience ,Branding —משמש להגדרת **Google Auth Platform** .Test usersו־ 

אינן מתבצעות באותו מקום, OAuth והגדרת API זו הנקודה החשובה ביותר: הפעלת ולכן צריך לעבור ביניהן באופן מודע. 

**הנכון Credential:בחירת סוג ה-1 שלב 5** ובדוק שהפרויקט הרצוי נבחר בחלק העליון. Google Cloud Console1.היכנס ל־ 

.Credentials _→_ APIs & Services2.עבור ל־ .Create credentials 3.לחץ על .API key ולא OAuth client ID .בתפריט שנפתח בחר4 

Create credentials בתפריט OAuth client ID :יצירת אישורים — בחירת1 איור 

©Dr. Yoram Segal כל הזכויות שמורות – 

5

> **[תיאור מדויק של צילום המסך]:** מסך "Credentials" ב-Google Cloud Console (כתובת: console.cloud.google.com/apis/credentials?project=api-rmi-007). בפס החיפוש מופיעה המילה "Gmail". תחת הכפתור הכחול "+ Create credentials" נפתחה רשימה נפתחת עם ארבע אפשרויות ליצירת אישור: (1) "API key" – Identifies your project using a simple API key to check quota and access; (2) "OAuth client ID" – Requests user consent so that your app can access the user's data; (3) "Service account" – Enables server-to-server, app-level authentication using robot accounts; (4) "Help me choose". מתחת אזור "API keys" עם ההודעה "No API keys to display". בראש העמוד באנר של ניסיון חינם בסך 300$.

## **OAuth client ID למה לבחור 5.1** 

שנדרש כאשר תוכנית פייתון צריכה להתחבר Credentialהוא סוג ה־ OAuth client ID של משתמש אמיתי ולקבל הרשאה באמצעות מסך Google Calendarאו ל־ Gmail לחשבון לא מתאים למטרה זו. API key .Google 

## **OAuth Client:התחלת יצירת ה-2 שלב 6** 

Create OAuth client ,ייתכן שייפתח מסךOAuth client ID 1.לאחר בחירת .ID 

Con­ ,לחץ עלconsent screen מציג הודעה שצריך קודם להגדיר Google 2.אם .figure consent screen 

Configure consent screen עם הכפתור Create OAuth client ID :מסך2 איור 

## **Google Auth Platform:כניסה ל-3 שלב 7** :Google Auth Platformיש שתי דרכים מהירות להגיע ל־ 

–כל הזכויות שמורות 

© Dr. Yoram Segal 

6

> **[תיאור מדויק של צילום המסך]:** מסך "Create OAuth client ID" בנתיב Google Auth Platform / Clients / Create client. בתפריט הצד: Overview, Branding, Audience, Clients (מסומן), Data access, Verification centre, Settings. טקסט הסבר: "A client ID is used to identify a single app to Google's OAuth servers...". מתחת הודעת אזהרה צהובה: "To create an OAuth client ID, you must first configure your consent screen", ולצדה כפתור "Configure consent screen". המסקנה: אי אפשר ליצור client לפני הגדרת מסך ההסכמה.

## **Google Cloud Console דרך א: מתוך 7.1** 

.Google Cloud 1.פתח את תפריט הצד הראשי של 

- מופיע ברשימה או באזור של פריטים שנעשה בהם Google Auth Platform 2.אם שימוש לאחרונה, לחץ עליו. 

— אינו גלוי בקלות Google Auth Platform Google Cloud :תפריט הצד הראשי של3 איור 

## **דרך ב: דרך קישור ישיר 7.2** 

לא מופיע בתפריט, פתח ידנית בדפדפן את הכתובת Google Auth Platform אם הבאה, עם מזהה הפרויקט שלך: 

https://console.cloud.google.com/auth/platform/overview?project=YOUR_PR _⌋_ OJECT_ID 

©Dr. Yoram Segal כל הזכויות שמורות – 

7

> **[תיאור מדויק של צילום המסך]:** תפריט הניווט הראשי של Google Cloud (פתוח מהצד). רשימת המוצרים: Marketplace, APIs and services (מודגש בכחול), Agent Platform, Compute Engine, Kubernetes Engine, Cloud Storage, Security (מודגש, עם תת-תפריט פתוח), BigQuery, Monitoring, Cloud Run, VPC network, Databases, Cloud SQL, Google Maps Platform. בתחתית: "Pins appear here" ו-"View all products". מימין נפתח תת-תפריט "Security Command Centre" עם הפריטים: Overview, Graph search, Issues, Findings, Assets, Compliance, Posture management, Rules, Sources, וקטגוריית "Detections and controls" (Google SecOps, Fraud Defense, Model armour, Web Security Scanner ועוד).

**הערה חשובה 7.3** 

אינו מציג Google Cloud במהלך העבודה בפועל עלול להיווצר מצב שבו התפריט הראשי של בצורה גלויה. במקרה כזה אין לבזבז זמן על חיפוש בתפריט; Google Auth Platform הדרך המהירה והמדויקת ביותר היא להשתמש בקישור הישיר. 

:המשך גלילה בתפריט הראשי — הפריט עדיין אינו נגיש ישירות4 איור 

**Google Auth Platform :מסך הפתיחה של4 שלב 8** 

Google auth עבור הפרויקט, יופיע מסך GoogleAuth Platformאם זו הכניסה הראשונה ל־ .Get started עם כפתור platform not configured yet 

.Get started 1.לחץ על 

.Audienceוה־ Branding2.לאחר מכן יתחיל אשף הגדרת ה־ 

Get started עם הכפתור Google auth platform not configured yet :מסך5 איור 

–כל הזכויות שמורות © Dr. Yoram Segal 

8

> **[תיאור מדויק של צילום המסך]:** מסך "Clients" תחת Google Auth Platform. כותרת "OAuth 2.0 Client IDs" וטבלה עם שורה אחת: שם ה-client "desktop-client-for-gmail-and-calendar", תאריך יצירה 25 May 2026, Type = Desktop, ו-Client ID המתחיל ב-"282342983791-561i..." (מקוצר, עם אייקון העתקה). מימין אייקוני עריכה ומחיקה. בראש המסך הכפתורים "+ Create client", "Delete", "Restore deleted OAuth clients". כלומר ה-client מסוג Desktop נוצר בהצלחה.

> **[תיאור מדויק של צילום המסך]:** מסך "Branding" ב-Google Auth Platform במצב לא-מוגדר. במרכז איור קווי של מעטפה/ענן ומתחתיו הכיתוב: "Google auth platform not configured yet — Get started with configuring your application's identity and manage credentials for calling Google APIs and Sign in with Google." ולמטה כפתור כחול "Get started".

**:מילוי פרטי האפליקציה5 שלב 9** 

יש למלא את פרטי האפליקציה הבסיסיים. App Information במסך 

.gmail­calendar­test כתוב שם ברור, לדוגמה App name 1.בשדה 

שלך. Gmailבחר את כתובת ה־ User support email 2.בשדה 

.Next 3.לחץ 

אם המסך הראשון כבר הושלם ואתה נמצא בשלב הבא, פשוט המשך לפי ההוראות 

הבאות. 

**:בחירת קהל היעד של האפליקציה6 שלב 10** יש לבחור מי יוכל להשתמש באפליקציה. Audience במסך 

.External 1.בחר 

שמנוהל באופן Google Workspace ,אלא אם מדובר בארגוןInternal 2.אל תבחר ארגוני. 

.Next 3.לחץ 

ExternalלInternal —בחירה בין Audience :מסך6 איור 

**External למה לבחור 10.1** 

הוא המסלול הנכון, משום External רגיל או פרויקט בדיקה מקומי, Gmail עבור חשבון .Test users עם רשימת Testing שהוא מאפשר עבודה במצב 

©Dr. Yoram Segal כל הזכויות שמורות – 

9

> **[תיאור מדויק של צילום המסך]:** אשף "Project configuration". שלב 1 "App Information" מסומן כהושלם (וי כחול). שלב 2 "Audience" פתוח עם שתי אפשרויות בחירה (radio): "Internal" – Only available to users within your organisation. You will not need to submit your app for verification; ו-"External" – Available to any test user with a Google Account. Your app will start in testing mode and will only be available to users that you add to the list of test users. Once your app is ready to push to production, you may need to verify your app. בתחתית כפתור "Next".

**:הזנת כתובת איש הקשר7 שלב 11** 

יש להקליד את כתובת האימייל שמקבלת עדכונים מגוגל. Contact Information במסך 

הקלד את כתובת האימייל שלך. Email addresses 1.בשדה .Next 2.לחץ .Create 3.במסך הבא לחץ 

Email addresses —שדה Contact Information :מסך7 איור 

**Gmail API :הפעלת8 שלב 12** 

ובדוק שהפרויקט הנכון נבחר. Google Cloud Console1.חזור ל־ 

2.פתח את תפריט הצד השמאלי הראשי. .APIs & Services 3.בחר .Library .בתפריט המשנה בחר4 .Gmail API 5.בשדה החיפוש כתוב .Gmail API .לחץ על התוצאה6 .Enable 7.לחץ על 

כבר פעיל, אין צורך לבצע פעולה נוספת. Gmail API אם 

–כל הזכויות שמורות 

© Dr. Yoram Segal 

10

> **[תיאור מדויק של צילום המסך]:** המשך אשף "Project configuration". שלבים 1 "App Information" ו-2 "Audience" מסומנים כהושלמו (וי כחול). שלב 3 "Contact Information" פתוח עם שדה חובה "Email addresses *" וההערה "These email addresses are for Google to notify you about any changes to your project." כפתור "Next". שלב 4 "Finish" טרם הושלם. בתחתית כפתורים "Create" ו-"Cancel".

## **Google Calendar API :הפעלת9 שלב 13** 

.Google Cloud Console1.הישאר ב־ .Library _→_ APIs & Services2.עבור שוב ל־ .Google Calendar API 3.בשדה החיפוש כתוב .Google Calendar API .לחץ על התוצאה4 .Enable 5.לחץ על 

Enabled במצב Google Calendar API :מסך פרטי8 איור 

,משום שבלי הפעלתCalendar API וגם את Gmail API המערכת דורשת להפעיל גם את הוגדר נכון. OAuthאי אפשר לבצע קריאות מאפליקציית פייתון גם אם ה־ API 

**API לאחר הפעלת Google Auth Platform:חזרה ל-10 שלב 14** API/Service de­ ,ייתכן שתישאר במסך שלGoogle Calendar API אחרי הפעלת .Google Auth Platformולא תראה דרך ברורה לחזור ל־ tails במקרה כזה: 

1.אין צורך לחפש זמן רב בתפריטים. 

2.פתח ישירות את הקישור: 

https://console.cloud.google.com/auth/platform/overview?project=YOUR_PR _⌋_ OJECT_ID 

- 3.ודא שאתה חוזר למסך שבו בתפריט השמאלי מופיעים: 

©Dr. Yoram Segal כל הזכויות שמורות – 

11

> **[תיאור מדויק של צילום המסך]:** מסך "API/Service details" עבור Google Calendar API. כותרת "Google Calendar API" עם התיאור "The Google Calendar API lets you manage your calendars and events." פרטים: Service name = calendar-json.googleapis.com, Type = Public API, Status = Enabled (ה-API הופעל). קישורי Documentation: Overview, Quickstarts, API reference. בראש קישור "Disable API" ולחצן "Create credentials". מתחת לשונית "Metrics" עם גרפים וסינונים (Versions, Credentials, Methods).

- Overview - Branding - Audience - Clients Data access - - Verification centre - Settings 

APIsלאחר הפעלת ה- Google Auth PlatformבOAuth overview:חזרה ל-9 איור 

## **בממשק החדש Overview:היכרות עם מסך ה-11 שלב 15** 

אפשר לוודא שהפרויקט נמצא במקום הנכון Google Auth Platform של Overview במסך בהמשך הדרך. Client ,או שכבר נוצרClient ושעדיין לא נוצר 

Create OAuth client עם הכפתור Overview :מסך10 איור 

,המשמעות היא שאתה נמצא במקוםCreate OAuth client אם אתה רואה כפתור הנכון בממשק החדש. 

–כל הזכויות שמורות © Dr. Yoram Segal 

12

> **[תיאור מדויק של צילום המסך]:** מסך "OAuth overview" ב-Google Auth Platform. תחת "Metrics" ההודעה: "You haven't configured any OAuth clients for this project yet", ולצדה כפתור "Create OAuth client". תחת "Project checkup": "No project health recommendations found for your project", עם קישור "Learn more about OAuth 2.0 policies".

> **[תיאור מדויק של צילום המסך]:** אותו מסך "OAuth overview" מהתמונה הקודמת (חיתוך מעט שונה) — "Metrics": "You haven't configured any OAuth clients for this project yet" + כפתור "Create OAuth client"; "Project checkup": "No project health recommendations found for your project".

## **Data access:הגדרת ההרשאות המדויקות ב-12 שלב 16** 

OAuth con­ בפועל. בממשק החדש לא מחפשים Scopesזהו השלב שבו מגדירים את ה־ .Google Auth Platform בתוך Data access הישן, אלא עובדים דרך sent screen 

.Data access 1.בתפריט השמאלי לחץ על 

.Add or Remove Scopes 2.לחץ על 

הוסף את שתי ההרשאות הבאות: Manually add scopes 3.באזור 

https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/calendar 

.Add to table .לחץ4 5.ודא ששתי הרשאות אלה מופיעות ברשימה. בהתאם למה שמופיע במסך. Save או Update .לחץ6 

## **פירוש ההרשאות 16.1** 

## :פירוש ההרשאות הנדרשות1 טבלה 

|**משמעות**|**הרשאה**|
|---|---|
|קריאה,<br>חיפוש,<br>תיוג,<br>שינוי<br>מצב,<br>יצירת<br>טיוטות, ושליחה/ניהול הודעות ברמתGmail<br>API<br>.|gmail.modify|
|גישה<br>מלאה<br>ללוח<br>השנה<br>הראשי<br>וליומנים<br>הזמינים,<br>כולל<br>יצירה,<br>עדכון<br>ומחיקה<br>של<br>אירועים.|calendar|



**Desktop מסוג OAuth Client :יצירת13 שלב 17** 

.Clients 1.בתפריט הצד השמאלי לחץ על 

.Create OAuth client או Create client 2.לחץ על .Desktop או Desktop app בחר Application type 3.בשדה 

הקלד שם ברור, לדוגמה: Name .בשדה4 

©Dr. Yoram Segal –כל הזכויות שמורות 

13

desktop­client­for­gmail­and­calendar 

.Create 5.לחץ ושמור את הקובץ במחשב. Download JSON .לאחר יצירת הלקוח, לחץ על6 בתוך תיקיית הפרויקט של פייתון. credentials.json7.שנה את שם הקובץ ל־ 

**איך נראה המסך לאחר יצירת הלקוח 17.1** 

אמורה להופיע שורה אחת עם: Clients לאחר יצירת הלקוח, ברשימת 

- desktop­client­for­gmail­and­calendar **:Name** 

- תאריך היצירה **:Creation date** 

Desktop **:Type** - - תווים 72מזהה ייחודי באורך של כ- **:Client ID** 

_הערה: לא צורף צילום מסך לשלב זה. בעת ביצוע השלב יש לוודא שהשורה מופיעה במסך הלקוחות לפני המעבר לשלב הבא._ 

**)Test user:הוספת משתמש בדיקה (14 שלב 18** 

יוכלו Test users ,רק משתמשים שמופיעים ברשימתTesting כאשר האפליקציה במצב .token לבצע התחברות ולקבל 

בתפריט השמאלי. Audience לחץ על Google Auth Platform 1.מתוך 

.Test users 2.גלול עד האזור .Add users 3.לחץ על 

שממנה תתבצע ההתחברות בפועל. Gmail.בחלון שנפתח הקלד את כתובת ה־4 

5.אם נדרש, ניתן להוסיף כמה כתובות בדיקה נוספות. .Save .לחץ6 

.Test users 7.ודא שהכתובת מופיעה כעת ברשימת 

–כל הזכויות שמורות 

© Dr. Yoram Segal 

14

**:קובץ פייתון לבדיקה15 שלב 19** 

ואירוע בלוח השנה הראשי Draftsלהלן תוכנית בדיקה מינימלית שיוצרת טיוטת מייל ב־ שעות. הקוד תואם להגדרות שהוגדרו במדריך זה. 4 לעוד 

from __future__ import annotations import base64 from datetime import datetime, timedelta from email.message import EmailMessage from pathlib import Path from google.auth.transport.requests import Request from google.oauth2.credentials import Credentials from google_auth_oauthlib.flow import InstalledAppFlow from googleapiclient.discovery import build SCOPES = [ "https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/calendar", ] CREDENTIALS_FILE = "credentials.json" TOKEN_FILE = "token.json" def get_credentials() ­> Credentials: creds = None if Path(TOKEN_FILE).exists(): creds = Credentials.from_authorized_user_file(TOKEN_FILE, _�→_ SCOPES) if not creds or not creds.valid: if creds and creds.expired and creds.refresh_token: creds.refresh(Request()) else: flow = InstalledAppFlow.from_client_secrets_file( CREDENTIALS_FILE, SCOPES) creds = flow.run_local_server(port=0) Path(TOKEN_FILE).write_text(creds.to_json(), encoding="utf­8") return creds def create_gmail_draft(gmail_service): msg = EmailMessage() msg["To"] = "me" msg["Subject"] = "Test draft from Python" msg.set_content("This is a minimal test draft created by Python.") raw = base64.urlsafe_b64encode(msg.as_bytes()).decode() draft = gmail_service.users().drafts().create( userId="me", body={"message": {"raw": raw}}, ).execute() return draft["id"] def create_calendar_event(calendar_service): start = datetime.now().astimezone() + timedelta(hours=4) 

©Dr. Yoram Segal –כל הזכויות שמורות 

15

end = start + timedelta(hours=1) event = { "summary": "Python API test event", "description": "Minimal test event created by Python.", "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()}, } created = calendar_service.events().insert( calendarId="primary", body=event, ).execute() return created["id"], created.get("htmlLink") def main(): creds = get_credentials() gmail_service = build("gmail", "v1", credentials=creds) calendar_service = build("calendar", "v3", credentials=creds) draft_id = create_gmail_draft(gmail_service) event_id, event_link = create_calendar_event(calendar_service) print(f"Draft created: {draft_id}") print(f"Calendar event created: {event_id}") print(f"Event link: {event_link}") if __name__ == "__main__": main() 

**והרצת תוכנית הבדיקה uv :התקנת16 שלב 20** 

**Windows PowerShellבuv התקנת 20.1** 

powershell ­ExecutionPolicy ByPass ­c "irm _�→_ https://astral.sh/uv/install.ps1 | iex" 

**macOS / Linuxבuv התקנת 20.2** 

curl ­LsSf https://astral.sh/uv/install.sh | sh 

לאחר ההתקנה, פתח טרמינל חדש ובדוק: 

uv ­­version 

–כל הזכויות שמורות 

© Dr. Yoram Segal 

16

## **pyproject.toml קובץ 20.3** 

[project] name = "gmail­calendar­test" version = "0.1.0" requires­python = ">=3.10" dependencies = [ "google­api­python­client", "google­auth­oauthlib", "google­auth­httplib2", ] 

**הרצה 20.4** 

1.צור תיקייה חדשה לפרויקט. .main.py 2.שמור בה את 

.pyproject.toml 3.שמור בה את .Google Auth Platformשהורד מ־ credentials.json .העתק אליה את4 

5.פתח טרמינל בתוך התיקייה והריץ: 

uv sync uv run main.py 

,ולאחר האישורGoogle בהרצה הראשונה ייפתח דפדפן, תתבצע התחברות לחשבון מקומי שישמש את ההרצות הבאות. token.json יווצר קובץ 

**בדיקות סופיות 21** 

לאחר הרצת התוכנית צריך לוודא את ארבע התוצאות הבאות: 

הרשאה ללא שגיאת גישה. Google 1.בדפדפן הופיע מסך .Drafts נוצרה טיוטה חדשה תחת Gmail 2.בתיבת שעות מזמן ההרצה. 4 3.בלוח השנה הראשי נוצר אירוע חדש שמתחיל .token.json .בתיקיית הפרויקט נוצר קובץ4 

©Dr. Yoram Segal כל הזכויות שמורות – 

17

## **תקלות נפוצות ופתרון מהיר 22** 

**This app isn't verified או Access blocked שגיאה: 22.1** ,זה תקין לראות מסך אזהרה. כל עוד החשבון המחוברTesting אם האפליקציה במצב ,ניתן להמשיך בתהליך ההרשאה.Test usersנמצא ב־ 

**נוצר Clientשגיאה: ההתחברות לא מצליחה למרות שה22.2** 

יש לוודא את שלושת הדברים הבאים: 

.Test users _→_ Audience -החשבון המחובר נוסף תחת .Data access הוגדרו תחת Scopes-ה־ 

APIs & Services הופעלו תחת Google Calendar API וגם Gmail API -גם .Library _→_ 

## **שגיאה: הקוד מבקש הרשאות ישנות 22.3** 

ולהריץ שוב את התוכנית token.json אחרים, יש למחוק את Scopes אם הוגדרו קודם חדש עם ההרשאות המעודכנות. OAuth כדי לכפות תהליך 

–כל הזכויות שמורות 

© Dr. Yoram Segal 

18