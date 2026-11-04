import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.config import Config

def get_db_connection():
    """Returns a SQLite connection with row factory enabled for dict-like access."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds initial agricultural guidance records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 0: Registered Farmers / Cooperative Members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        mobile_number TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        village TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'Maharashtra',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 1: Disease Scans History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        crop_name TEXT NOT NULL,
        predicted_disease TEXT NOT NULL,
        disease_mr TEXT,
        disease_hi TEXT,
        confidence REAL NOT NULL,
        status TEXT NOT NULL,
        severity TEXT DEFAULT 'Medium',
        summary_en TEXT,
        summary_hi TEXT,
        summary_mr TEXT,
        organic_remedy TEXT,
        chemical_remedy TEXT,
        prevention_tip TEXT,
        model_mode TEXT DEFAULT 'Trained MobileNetV2 Prototype',
        farmer_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers (id)
    );
    """)

    # Ensure schema migration for existing databases
    cursor.execute("PRAGMA table_info(scans)")
    scan_cols = [col[1] for col in cursor.fetchall()]
    if "disease_mr" not in scan_cols:
        cursor.execute("ALTER TABLE scans ADD COLUMN disease_mr TEXT")
    if "disease_hi" not in scan_cols:
        cursor.execute("ALTER TABLE scans ADD COLUMN disease_hi TEXT")
    if "farmer_id" not in scan_cols:
        cursor.execute("ALTER TABLE scans ADD COLUMN farmer_id INTEGER")

    # Backfill seeded records if needed
    cursor.execute("""
        UPDATE scans SET disease_mr = 'कपाशीवरील जिवाणूजन्य करपा रोग', disease_hi = 'कपास का जीवाणु झुलसा'
        WHERE (disease_mr IS NULL OR disease_mr = '') AND crop_name = 'Cotton' AND predicted_disease LIKE '%Bacterial Blight%'
    """)
    cursor.execute("""
        UPDATE scans SET disease_mr = 'निरोगी सोयाबीन पान', disease_hi = 'स्वस्थ सोयाबीन पत्ती'
        WHERE (disease_mr IS NULL OR disease_mr = '') AND crop_name = 'Soybean' AND predicted_disease LIKE '%Healthy%'
    """)

    # Table 2: Agricultural Knowledge Base & Crop Guidance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS advisory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop TEXT NOT NULL,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        title_en TEXT NOT NULL,
        title_hi TEXT NOT NULL,
        title_mr TEXT NOT NULL,
        description_en TEXT NOT NULL,
        description_hi TEXT NOT NULL,
        description_mr TEXT NOT NULL,
        organic_remedy_en TEXT,
        organic_remedy_hi TEXT,
        organic_remedy_mr TEXT,
        chemical_remedy_en TEXT,
        chemical_remedy_hi TEXT,
        chemical_remedy_mr TEXT,
        prevention_en TEXT,
        prevention_hi TEXT,
        prevention_mr TEXT
    );
    """)

    # Table 3: Farmer Inquiries & Feedback
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_name TEXT NOT NULL,
        contact_number TEXT,
        district TEXT NOT NULL,
        crop_type TEXT,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Seed Initial Advisory Data if table is empty
    cursor.execute("SELECT COUNT(*) FROM advisory_items")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_advisory_data(conn)

    # Seed Demo Farmer if farmers table is empty
    cursor.execute("SELECT COUNT(*) FROM farmers")
    farmer_count = cursor.fetchone()[0]
    if farmer_count == 0:
        seed_sample_farmer(conn)

    # Seed 2 realistic historical scans if empty to give dashboard immediate appeal
    cursor.execute("SELECT COUNT(*) FROM scans")
    scan_count = cursor.fetchone()[0]
    if scan_count == 0:
        seed_sample_scans(conn)
    else:
        # Link existing unlinked scans to the first farmer if present
        cursor.execute("SELECT id FROM farmers ORDER BY id ASC LIMIT 1")
        first_farmer = cursor.fetchone()
        if first_farmer:
            cursor.execute("UPDATE scans SET farmer_id = ? WHERE farmer_id IS NULL", (first_farmer[0],))
            conn.commit()

    conn.close()

def seed_sample_farmer(conn):
    """Creates an initial demo farmer account for seamless evaluations and testing."""
    cursor = conn.cursor()
    sample_hash = generate_password_hash("password123")
    cursor.execute("""
        INSERT INTO farmers (
            full_name, mobile_number, email, password_hash, village, district, state
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "रमेश पाटील (Ramesh Patil)",
        "9876543210",
        "ramesh.patil@kisaan.org",
        sample_hash,
        "बारामती (Baramati)",
        "Pune",
        "Maharashtra"
    ))
    conn.commit()

def seed_advisory_data(conn):
    cursor = conn.cursor()
    advisories = [
        # 1. Soybean - Rust (तांबेरा)
        (
            "Soybean", "Fungal Disease", "High",
            "Soybean Asian Rust (Phakopsora pachyrhizi)",
            "सोयाबीन तांबेरा रोग",
            "सोयाबीन तांबेरा (एशियन रस्ट) रोग",
            "Yellow-brown pustules appearing on the underside of leaves, causing rapid leaf shedding.",
            "पत्तियों की निचली सतह पर पीले-भूरे रंग के धब्बे बनते हैं और पत्तियां जल्दी झड़ने लगती हैं।",
            "पानांच्या खालच्या बाजूवर पिवळसर-तपकिरी रंगाचे पुरळ तयार होतात व पाने अकाली गळतात.",
            "Neem oil spray (5 ml/liter) or Panchagavya application at early symptom onset.",
            "प्रारंभिक अवस्था में नीम तेल (5 मिली/लीटर) या पंचगव्य का छिड़काव करें।",
            "सुरुवातीला ५ मि.ली. कडुनिंब तेल प्रति लिटर पाण्यात मिसळून किंवा पंचगव्य फवारावे.",
            "Propiconazole 25% EC @ 1 ml/L or Tebuconazole 25.9% EC @ 1.5 ml/L of water.",
            "प्रोपीकोनाझोल 25% EC (1 मिली/लीटर) अथवा टेबुकोनाझोल का संतुलित छिड़काव।",
            "प्रोपिकोनाझोल २५% ईसी (१ मिली प्रति लिटर) किंवा टेबुकोनाझोल २५.९% ईसी (१.५ मिली/लिटर) फवारावे.",
            "Avoid dense planting, maintain field drainage, inspect after continuous monsoon drizzle.",
            "अधिक घनी बुवाई न करें, उचित जल निकासी रखें, रिमझिम बारिश के बाद खेत की निगरानी करें।",
            "दाट पेरणी टाळावी, शेतातून पाण्याचा योग्य निचरा ठेवावा आणि ढगाळ वातावरणात नियमित पाहणी करावी."
        ),
        # 2. Cotton - Pink Bollworm (गुलाबी बोंडअळी)
        (
            "Cotton", "Pest Infestation", "High",
            "Pink Bollworm (Pectinophora gossypiella)",
            "कपास गुलाबी सुंडी",
            "कापसावरील गुलाबी बोंडअळी",
            "Rosette flowers with petals twisted together, larvae burrowing into developing bolls.",
            "फूल गुलाब की तरह मुड़ जाते हैं और सुंडी बोंडों के भीतर छेद कर बीज को नष्ट करती है।",
            "फुल डोमकळी स्वरूपात उमलते व अळी बोंडात शिरून सरकी आणि कापूस खराब करते.",
            "Install pheromone traps (5 per acre), release Trichogramma egg parasitoids.",
            "प्रति एकड़ 5 फेरोमोन ट्रैप लगाएं और ट्राइकोग्रामा परजीवी मित्रकीट छोड़ें।",
            "एकर ५ कामगंध सापळे (फेरोमोन ट्रॅप) लावा आणि ट्रायकोड्रॉमा परोपजीवींचा वापर करा.",
            "Profenofos 50% EC @ 2 ml/L or Emamectin Benzoate 5% SG @ 5 g per 10 L water.",
            "प्रोफेनोफॉस 50% EC (2 मिली/लीटर) या इमामेक्टिन बेंजोएट का नियंत्रित उपयोग करें।",
            "प्रोफेनोफॉस ५०% ईसी (२ मिली/लिटर) किंवा इमामेक्टिन बेंझोएट ५% एसजी (५ ग्रॅम/१० लिटर) फवारावे.",
            "Destroy crop residues after harvest, use certified Bt-cotton seeds, avoid late-season crops.",
            "फसल कटाई के बाद अवशेषों को नष्ट करें, प्रमाणित बीज प्रयोग करें।",
            "फरदड (Rattoning) कापूस घेणे टाळावे व हंगाम संपताच शेतातील अवशेष नष्ट करावेत."
        ),
        # 3. Tomato - Early Blight (करपा)
        (
            "Tomato", "Fungal Disease", "Medium",
            "Tomato Early Blight (Alternaria solani)",
            "टमाटर अगेती झुलसा",
            "टोमॅटोवरील लवकर येणारा करपा रोग",
            "Concentric dark brown rings forming target-like patterns on older leaves and stems.",
            "पुरानी पत्तियों पर गाढ़े भूरे रंग के छल्लेदार धब्बे बनते हैं जो लक्ष्य (Target) जैसे दिखते हैं।",
            "जुनाट पानांवर चक्राकार (Target spot) तपकिरी काळे ठिपके पडतात आणि पाने करपतात.",
            "Spray baking soda solution (3 g/L) + liquid organic soap or bio-fungicide Trichoderma.",
            "बेकिंग सोडा घोल (3 ग्राम/लीटर) या ट्राइकोडर्मा बायो-फंगिसाइड का स्प्रे करें।",
            "ट्रायकोडर्मा व्हिरीडी (५ ग्रॅम/लिटर) किंवा जिवाणू संवर्धकाची फवारणी करावी.",
            "Mancozeb 75% WP @ 2.5 g/L or Azoxystrobin 23% SC @ 1 ml/L.",
            "मैंकोजेब 75% WP (2.5 ग्राम/लीटर) अथवा एज़ोक्सीस्ट्रोबिन का छिड़काव।",
            "मँकोझेब ७५% डब्ल्यूपी (२.५ ग्रॅम प्रति लिटर) किंवा ॲझॉक्सीस्ट्रॉबिन (१ मिली/लिटर) फवारावे.",
            "Prune bottom foliage, use drip irrigation to keep leaves dry, rotate with non-solanaceous crops.",
            "निचली पत्तियों की छंटाई करें, ड्रिप सिंचाई का प्रयोग करें जिससे पत्तियां सूखी रहें।",
            "खालची रोगट पाने काढून टाकावीत, ठिबक सिंचन वापरावे जेणेकरून पानांवर ओलावा राहणार नाही."
        ),
        # 4. Sugarcane - Red Rot (ऊसाचा लाल कुजव्या)
        (
            "Sugarcane", "Fungal Disease", "High",
            "Sugarcane Red Rot (Colletotrichum falcatum)",
            "गन्ने का लाल सड़न रोग",
            "ऊसावरील लाल कुजव्या रोग (रेड रॉट)",
            "Yellowing and drying of crown leaves, internal split stem reveals red tissue with white patches.",
            "पौधे के शीर्ष पत्ते सूखने लगते हैं, तने को चीरने पर अंदर लाल रंग और सफेद आड़े धब्बे दिखते हैं।",
            "टोकाकडील पाने पिवळी पडून वाळतात, ऊस चिरल्यास आतून लाल रंग व पांढरे पट्टे आढळतात व अल्कोहोलचा वास येतो.",
            "Treat setts with hot water (52°C for 30 mins) and dip in Trichoderma suspension.",
            "बीज को गर्म पानी (52°C 30 मिनट) और ट्राइकोडर्मा घोल से उपचारित करें।",
            "बेणे प्रक्रिया: ५०° से. तापमानाच्या गरम पाण्यात बेणे उपचार किंवा ट्रायकोडर्मा द्रावणात बुडवणे.",
            "Carbendazim 50% WP sett treatment @ 2 g/L before sowing.",
            "बुवाई से पहले कार्बेन्डाजिम 50% WP (2 ग्राम/लीटर) में बीज डुबोएं।",
            "पेरणीपूर्वी कार्बेन्डाझिम ५०% डब्ल्यूपी (२ ग्रॅम/लिटर) द्रावणात बेणे १० मिनिटे बुडवून लावावे.",
            "Use disease-free certified setts, ensure good drainage, practice multi-year crop rotation.",
            "रोगमुक्त प्रमाणित बेने चुनें, खेत में जलजमाव न होने दें।",
            "रोगमुक्त प्रमाणित बेणे वापरावे, पाण्याचा साचणारा भाग टाळावा आणि फेरपालट करावी."
        ),
        # 5. Rice / Paddy - Blast (तांदूळ करपा)
        (
            "Rice", "Fungal Disease", "High",
            "Rice Blast Disease (Magnaporthe oryzae)",
            "धान का झुलसा रोग (ब्लास्ट)",
            "भातावरील करपा (ब्लास्ट) रोग",
            "Spindle-shaped lesions with ash-grey centers and brown borders on leaves and neck nodes.",
            "पत्तियों पर नाव या आंख के आकार के धब्बे जिनका केंद्र भूरा-सफेद और किनारा गहरा होता है।",
            "पानांवर डोळ्याच्या किंवा बोटीच्या आकाराचे मधोमध राखाडी व कडेने तपकिरी ठिपके पडतात.",
            "Seed treatment with Pseudomonas fluorescens (10 g/kg seed) and cow urine foliar spray (10%).",
            "स्यूडोमोनास फ्लोरोसेंस (10 ग्राम/किग्रा बीज) द्वारा बीज उपचार और 10% गोमूत्र स्प्रे।",
            "स्यूडोमोनास फ्लुरोसन्स (१० ग्रॅम/किलो बियाणे) बीजप्रक्रिया व १०% गोमूत्र अर्क फवारणी.",
            "Tricyclazole 75% WP @ 0.6 g/L or Isoprothiolane 40% EC @ 1.5 ml/L.",
            "ट्राइसाइक्लाजोल 75% WP (0.6 ग्राम/लीटर) का छिड़काव समय पर करें।",
            "ट्रायसायक्लॅझोल ७५% डब्ल्यूपी (०.६ ग्रॅम प्रति लिटर पाणी) फवारावे.",
            "Avoid excessive nitrogen application, maintain optimum spacing, drain fields intermittently.",
            "अत्यधिक यूरिया के उपयोग से बचें, पौधों में उचित दूरी रखें।",
            "नत्राचा (युरिया) अतिवापर टाळावा, शिफारशीत मात्रेत पालाश द्यावे व हवा खेळती ठेवावी."
        )
    ]

    cursor.executemany("""
    INSERT INTO advisory_items (
        crop, category, severity,
        title_en, title_hi, title_mr,
        description_en, description_hi, description_mr,
        organic_remedy_en, organic_remedy_hi, organic_remedy_mr,
        chemical_remedy_en, chemical_remedy_hi, chemical_remedy_mr,
        prevention_en, prevention_hi, prevention_mr
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, advisories)
    conn.commit()

def seed_sample_scans(conn):
    cursor = conn.cursor()
    # Check if a farmer exists to link these scans
    cursor.execute("SELECT id FROM farmers ORDER BY id ASC LIMIT 1")
    farmer_row = cursor.fetchone()
    farmer_id = farmer_row[0] if farmer_row else None

    samples = [
        (
            "sample_cotton_leaf.jpg", "Cotton", "Bacterial Blight (Angular Leaf Spot)",
            "कपाशीवरील जिवाणूजन्य करपा रोग", "कपास का जीवाणु झुलसा (बैक्टीरियल ब्लाइट)",
            94.2, "Action Required", "High",
            "Angular water-soaked spots on leaf surfaces bounded by veins.",
            "पत्तियों की नसों के बीच पानी जैसे कोणीय धब्बे दिखाई दे रहे हैं।",
            "पानांच्या शिरांमध्ये कोनीय पाणीयुक्त ठिपके तयार झाले आहेत.",
            "कडुनिंब तेल ५ मि.ली./लिटर किंवा बोर्डो मिश्रण १% फवारावे.",
            "Copper Oxychloride 50% WP (2.5 g/L) + Streptocycline (1 g/10L).",
            "Maintain plant spacing and sanitize field equipment.",
            "Trained MobileNetV2 Prototype",
            farmer_id
        ),
        (
            "sample_soybean_leaf.jpg", "Soybean", "Healthy Foliage (निरोगी पान)",
            "निरोगी सोयाबीन पान", "स्वस्थ सोयाबीन पत्ती",
            98.5, "Optimal Health", "Low",
            "No pathogens or discoloration observed; lush green healthy leaf structure.",
            "कोई रोग या कीड़ा नहीं पाया गया; फसल स्वस्थ एवं सामान्य है।",
            "कोणत्याही रोगाची लक्षणे नाहीत; पीक अत्यंत निरोगी आणि जोमदार आहे.",
            "Continue standard organic compost and microbial soil health boosters.",
            "N/A (Crop is healthy)",
            "Regular scouting and clean weeding.",
            "Trained MobileNetV2 Prototype",
            farmer_id
        )
    ]
    cursor.executemany("""
    INSERT INTO scans (
        filename, crop_name, predicted_disease, disease_mr, disease_hi,
        confidence, status, severity,
        summary_en, summary_hi, summary_mr,
        organic_remedy, chemical_remedy, prevention_tip, model_mode, farmer_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, samples)
    conn.commit()
