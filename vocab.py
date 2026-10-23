"""Word lists and templates for the Project Pulse synthetic data generator.
Everything here is fictional. Edit freely (e.g. after Sandeep reviews it)."""

INDIA_PEOPLE = ["Rohan Mehta", "Priya Sharma", "Ankit Verma", "Neha Gupta", "Arjun Nair",
                "Kavya Iyer", "Vikram Singh", "Sneha Patel", "Rahul Joshi", "Pooja Reddy",
                "Aman Khanna", "Divya Menon", "Karan Malhotra", "Ishita Rao", "Siddharth Jain",
                "Tanvi Kulkarni", "Manish Yadav", "Ritika Bansal", "Varun Chopra", "Aditi Desai"]
US_UK_PEOPLE = ["Emily Carter", "Jake Thompson", "Sarah Collins", "Oliver Bennett", "Megan Hughes",
                "Daniel Brooks", "Hannah Price", "Tom Fletcher", "Laura Mitchell", "Chris Walker"]
DELIVERY_LEADS = ["Nikhil Arora", "Shweta Kapoor", "Mark Davies", "Rachel Green-Moore",
                  "Sameer Qureshi", "Julia Barnes", "Deepak Pillai", "Anjali Saxena"]

CLIENTS = ["Harborview Museum", "Northwind Health", "Bluepeak Retail", "Crestline Insurance",
           "Riverside Foundation", "Summit Learning", "Oakridge Bank", "Lumen Arts Council",
           "Pinecrest Hospital Group", "Metro Transit Authority", "Greenleaf Nonprofit Network",
           "Atlas Logistics", "Brightside Charities", "Cobalt Media", "Evergreen University",
           "Silverline Travel", "Redwood Legal", "Seaside Aquarium", "Ironbridge Manufacturing",
           "Clearwater Utilities"]
PROJECT_TYPES = [("Membership Portal", "HMP"), ("Patient App", "PAP"), ("eCommerce Replatform", "ECR"),
                 ("Claims Dashboard", "CLD"), ("Donor CRM Integration", "DCI"), ("Learning Platform", "LRN"),
                 ("Mobile Banking App", "MBA"), ("Ticketing System", "TKT"), ("Data Warehouse Migration", "DWM"),
                 ("Collections Website", "COL"), ("Booking Engine", "BKE"), ("Partner Portal", "PTP"),
                 ("AI Search Assistant", "AIS"), ("Grant Management System", "GMS"), ("Fleet Tracking", "FLT")]
COMPONENTS = ["Frontend", "Backend", "API", "Payments", "Auth", "Data", "CMS", "Mobile", "DevOps", "QA"]

# (summary, short spoken reference, keywords used for matching)
TICKET_TEMPLATES = [
    ("SSO login page times out after 30 seconds", "login timeout", ["login", "timeout", "sso"]),
    ("Payment gateway retry logic for failed transactions", "payment retry", ["payment", "retry", "gateway"]),
    ("Member renewal email not triggering", "renewal email", ["renewal", "email"]),
    ("Search results page slow on mobile", "search slow", ["search", "slow", "mobile"]),
    ("Add CSV export to admin reports", "csv export", ["csv", "export", "report"]),
    ("Donation form validation error on Safari", "safari validation", ["donation", "safari", "validation"]),
    ("Migrate user table to new schema", "user migration", ["migrate", "migration", "user", "schema"]),
    ("Push notifications not delivered on Android", "android push", ["push", "notification", "android"]),
    ("Checkout page crashes when coupon applied", "coupon crash", ["checkout", "coupon", "crash"]),
    ("Integrate Salesforce contact sync", "salesforce sync", ["salesforce", "sync", "contact"]),
    ("Dashboard charts show wrong totals", "dashboard totals", ["dashboard", "chart", "totals"]),
    ("Password reset link expires too early", "password reset", ["password", "reset", "link"]),
    ("Image upload fails above 5 MB", "image upload", ["image", "upload"]),
    ("Event calendar timezone bug", "calendar timezone", ["calendar", "timezone", "event"]),
    ("Accessibility fixes for homepage (WCAG)", "accessibility", ["accessibility", "wcag", "homepage"]),
    ("Set up CI pipeline for staging", "ci pipeline", ["pipeline", "staging", "ci"]),
    ("API rate limiting for partner endpoints", "rate limiting", ["rate", "limit", "partner", "api"]),
    ("Ticket booking double-charges customers", "double charge", ["booking", "double", "charge"]),
    ("Admin role permissions not saving", "role permissions", ["role", "permission", "admin"]),
    ("PDF invoice generation broken", "invoice pdf", ["invoice", "pdf"]),
    ("Content model for exhibition pages", "exhibition pages", ["exhibition", "content", "page"]),
    ("Session expires during long forms", "session expiry", ["session", "expire", "form"]),
    ("Analytics events missing for signup", "signup analytics", ["analytics", "signup", "events"]),
    ("Data sync job fails at midnight", "midnight sync", ["sync", "job", "midnight"]),
    ("Translate site into Spanish", "spanish translation", ["spanish", "translate", "translation"]),
    ("Map view not loading store locations", "map view", ["map", "location", "store"]),
    ("Upgrade Node runtime to v22", "node upgrade", ["node", "upgrade", "runtime"]),
    ("Duplicate records in donor import", "duplicate donors", ["duplicate", "donor", "import"]),
    ("Chatbot gives wrong opening hours", "chatbot hours", ["chatbot", "hours", "opening"]),
    ("Performance test for 10k concurrent users", "load test", ["performance", "load", "concurrent"]),
    ("Cookie consent banner overlaps footer", "cookie banner", ["cookie", "banner", "consent"]),
    ("Refund workflow approval step", "refund approval", ["refund", "approval", "workflow"]),
    ("Two-factor authentication for admins", "two factor", ["two", "factor", "2fa", "authentication"]),
    ("Product filters reset on back button", "filters reset", ["filter", "reset", "back"]),
    ("Email template branding update", "email branding", ["email", "template", "branding"]),
    ("Audit log for record changes", "audit log", ["audit", "log"]),
]
DEPENDENCIES = ["API credentials", "UAT sign-off", "design approval", "content", "test data",
                "VPN access", "payment sandbox keys", "final copy", "the Salesforce sandbox"]

STATUS_COMMENTS = {
    "Green": ["On track.", "On track, minor QA delays.", "All good, sprint going as planned.",
              "Progressing well. Client happy.", "No major issues.", "On track - few open bugs, manageable.",
              "Green. Some dependency on client but under control.", ""],
    "Yellow": ["Some delays due to client dependencies.", "Velocity dipped this sprint, recovering.",
               "Scope additions under discussion.", "At risk - waiting on UAT feedback.",
               "Resource change, minor impact expected.", "Yellow - timelines tight."],
    "Red": ["Major delay. Escalated to account manager.", "Blocked on client for 2+ weeks.",
            "Release date will slip.", "Critical defects in UAT.", "Red - recovery plan in progress."],
}

TICKET_COMMENTS = {
    "normal": ["PR raised, pls review.", "Done on my end, moving to QA.", "@{p} can you check this?",
               "Deployed to staging.", "QA passed.", "Ye kal tak ho jayega.", "Working on it.",
               "Need clarification on acceptance criteria.", "Fixed in latest build."],
    "blocked": ["Waiting on client for {d}.", "Blocked - {d} pending.", "Client se {d} abhi tak nahi aaya.",
                "Still waiting on {d}, followed up again.", "Can't proceed without {d}."],
    "reopen": ["Reopening - issue still reproducible.", "QA failed, reopening.", "Bug wapas aa gaya prod pe."],
}

# ---------------- meeting language ----------------
HINDI_NUM = ("shunya ek do teen chaar paanch chhah saat aath nau das gyaarah baarah terah chaudah pandrah "
             "solah satrah athaarah unnees bees ikkees baees teyees chaubees pachchees chhabbees sattaees "
             "atthaees untees tees ikattees battees taintees chauntees paintees chhattees saintees adtees "
             "untaalees chaalees iktaalees bayaalees taintaalees chauvaalees paintaalees chhiyaalees "
             "saintaalees adtaalees unchaas pachaas ikyaavan baavan tirepan chauvan pachpan chhappan "
             "sattaavan atthaavan unsath saath iksath baasath tirsath chausath painsath chhiyaasath "
             "sadsath adsath unhattar sattar ikhattar bahattar tihattar chauhattar pachhattar chhihattar "
             "sathattar athhattar unaasi assi ikyaasi bayaasi tiraasi chauraasi pachaasi chhiyaasi "
             "sataasi athaasi nawaasi nabbe ikyaanve baanve tiraanve chauraanve pachaanve chhiyaanve "
             "sattaanve atthaanve ninyaanve").split()
assert len(HINDI_NUM) == 100

EN_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
EN_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

# Roman Hindi word -> Devanagari (what an ASR in "Hindi mode" tends to output)
DEVANAGARI = {
    "hai": "है", "hain": "हैं", "kar": "कर", "karo": "करो", "kar do": "कर दो", "nahi": "नहीं",
    "abhi": "अभी", "tak": "तक", "ye": "ये", "isko": "इसको", "isme": "इसमें", "mein": "में",
    "kya": "क्या", "haan": "हाँ", "theek": "ठीक", "toh": "तो", "chalo": "चलो", "kal": "कल",
    "aaj": "आज", "ho": "हो", "gaya": "गया", "jayega": "जाएगा", "wala": "वाला", "dekhte": "देखते",
    "hum": "हम", "main": "मैं", "tum": "तुम", "ke": "के", "ki": "की", "ka": "का", "se": "से",
    "pe": "पे", "bhi": "भी", "aur": "और", "lagta": "लगता", "mujhe": "मुझे", "raha": "रहा",
    "rahe": "रहे", "thoda": "थोड़ा", "sab": "सब", "log": "लोग", "baad": "बाद", "pehle": "पहले",
    "karte": "करते", "do": "दो", "lo": "लो", "le": "ले", "bata": "बता", "batao": "बताओ",
    "kahan": "कहाँ", "hua": "हुआ", "uska": "उसका", "iska": "इसका", "chal": "चल", "daal": "डाल",
    "rakh": "रख", "rakhte": "रखते", "shayad": "शायद", "padega": "पड़ेगा", "dunga": "दूँगा",
    "denge": "देंगे", "wait": "wait", "bas": "बस", "matlab": "मतलब", "accha": "अच्छा",
}

ASR_CONFUSIONS = {"QA": ["Q A", "queue A", "QA"], "PR": ["P R", "PR", "pier"], "UAT": ["U A T", "UAT", "you at"],
                  "staging": ["staging", "stating"], "deploy": ["deploy", "deployed", "the ploy"],
                  "sprint": ["sprint", "print", "spring"], "blocker": ["blocker", "blocked", "block"],
                  "ticket": ["ticket", "tikat", "ticket"], "Salesforce": ["sales force", "Salesforce"],
                  "timeout": ["time out", "timeout"], "SSO": ["S S O", "SSO", "esso"]}
