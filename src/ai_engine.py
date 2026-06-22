import json
import os
import google.generativeai as genai
from datetime import datetime
import streamlit as st

# Pre-compiled high-quality travel data for demo mode
MOCK_DESTINATIONS = {
    "goa": {
        "trip_overview": {
            "weather_summary": "Warm, sunny beach weather (26°C to 33°C). High humidity, gentle sea breeze.",
            "safety_level": "Generally Safe (Low Crime)",
            "risk_score": 15,
            "currency_code": "INR",
            "exchange_rate_vs_usd": 1.0, # Domestic trip, 1 INR = 1 INR
            "local_languages": ["Konkani", "Hindi", "English", "Marathi"]
        },
        "risk_scorecard": {
            "physical_safety": 88,
            "health_medical": 80,
            "scams_theft": 75,
            "solo_traveler": 86
        },
        "safety_recommendations": [
            {
                "category": "Beach & Water Safety",
                "tips": [
                    "Pay close attention to red flags on beaches. Rip currents are strong in Goa, especially during monsoon margins.",
                    "Avoid swimming after dark or under the influence of alcohol.",
                    "Always wear lifejackets during water sports."
                ]
            },
            {
                "category": "Local Transit & Scams",
                "tips": [
                    "Goa does not have standard Uber/Ola services. Cabs are run by local unions and can be expensive; agree on the price beforehand or use the GoaMiles app.",
                    "Renting a scooter is popular but make sure you have a valid license and wear a helmet (fines are heavy, and road safety is volatile).",
                    "Politely ignore drug dealers and touts in tourist areas (Calangute, Anjuna)."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Local Tourism Office / Police HQ, Panaji",
            "address": "Patto Plaza, Panaji, Goa 403001",
            "phone": "+91-832-243-7755",
            "website": "https://goatourism.gov.in/"
        },
        "emergency_contacts": {
            "police": "112 / 100",
            "fire_ambulance": "108 / 102",
            "tourist_helpline": "1363"
        },
        "packing_list": [
            {"item": "High SPF Sunscreen & Sunglasses", "category": "Personal Care", "reason": "Goa sun is extremely intense on beaches."},
            {"item": "Light Cotton & Breathable Beachwear", "category": "Clothing", "reason": "High humidity and temperatures require airy fabrics."},
            {"item": "Mosquito Repellent Cream", "category": "Health", "reason": "Tropical climate leads to high mosquito density at night."},
            {"item": "Waterproof Phone Pouch", "category": "Accessories", "reason": "Protects your phone from sand and water splashes during beach activities."},
            {"item": "Slip-on Sandals / Flip-flops", "category": "Clothing", "reason": "Convenient for sandy beaches and easy removal."}
        ],
        "pocket_phrases": [
            {"phrase": "Dev borem korum", "pronunciation": "dev bo-rem ko-room", "meaning": "Thank you / God bless you (in Konkani)"},
            {"phrase": "Khushal asa?", "pronunciation": "khoo-shal ah-sah", "meaning": "How are you?"},
            {"phrase": "Maka naka", "pronunciation": "mah-kah nah-kah", "meaning": "I don't want it (useful to refuse pushy vendors)"},
            {"phrase": "Kitle rupya?", "pronunciation": "kit-leh roop-yah", "meaning": "How much money / price?"},
            {"phrase": "Hanga rao", "pronunciation": "hang-ah rao", "meaning": "Stop here (useful for bus/auto navigation)"}
        ],
        "budget_allocation": {
            "accommodation": 35.0,
            "food": 30.0,
            "transport": 15.0,
            "activities": 12.0,
            "emergency_fund": 8.0
        }
    },
    "kerala": {
        "trip_overview": {
            "weather_summary": "Humid and tropical (24°C to 31°C). Lush green backwaters, seasonal showers.",
            "safety_level": "Very Safe (Low crime rate)",
            "risk_score": 12,
            "currency_code": "INR",
            "exchange_rate_vs_usd": 1.0,
            "local_languages": ["Malayalam", "English", "Tamil"]
        },
        "risk_scorecard": {
            "physical_safety": 92,
            "health_medical": 88,
            "scams_theft": 82,
            "solo_traveler": 90
        },
        "safety_recommendations": [
            {
                "category": "Backwater & Houseboat Safety",
                "tips": [
                    "Ensure your houseboat has valid government safety licenses and life buoys.",
                    "Verify that the boat moors by 5:30 PM as night cruising is legally banned in backwaters.",
                    "Avoid drinking untreated local tap water; stick to bottled mineral water."
                ]
            },
            {
                "category": "Forest & Hill Stations (Munnar/Wayanad)",
                "tips": [
                    "Avoid driving in hill stations after dark due to thick fog and narrow roads.",
                    "Do not approach wild elephants or stray animals on forest routes.",
                    "Be mindful of leeches on jungle trails; carry salt or sanitizer to remove them."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Kerala Tourism Information Desk, Trivandrum",
            "address": "Park View, Opposite Museum, Thiruvananthapuram 695033",
            "phone": "+91-471-232-1132",
            "website": "https://www.keralatourism.org/"
        },
        "emergency_contacts": {
            "police": "112 / 100",
            "fire_ambulance": "101 / 108",
            "tourist_helpline": "1-800-425-4747"
        },
        "packing_list": [
            {"item": "Umbrella or Rain Poncho", "category": "Clothing", "reason": "Kerala experiences sudden rain showers even outside monsoon seasons."},
            {"item": "Mosquito Repellent & Nets", "category": "Health", "reason": "Lakes and backwaters can attract insects at dusk."},
            {"item": "Comfortable Walking Sandals", "category": "Clothing", "reason": "Perfect for boating, spice gardens, and slippery tea gardens."},
            {"item": "Light Cotton Outfits", "category": "Clothing", "reason": "Maintains comfort in highly humid coastal environments."},
            {"item": "Basic Stomach Meds", "category": "Health", "reason": "Spicy coconut-infused local curries can require adjustment."}
        ],
        "pocket_phrases": [
            {"phrase": "Namaskaram", "pronunciation": "nah-mah-skah-rahm", "meaning": "Hello / Respectful Greeting (in Malayalam)"},
            {"phrase": "Nanni", "pronunciation": "nah-nee", "meaning": "Thank you"},
            {"phrase": "Ethra roopa?", "pronunciation": "eth-rah roo-pah", "meaning": "How much does this cost?"},
            {"phrase": "Vazhi ethraya?", "pronunciation": "vah-zhi eth-rah-yah", "meaning": "Which way is it?"},
            {"phrase": "Sahayikkyu!", "pronunciation": "sah-hah-yee-kyoo", "meaning": "Help me! (emergency)"}
        ],
        "budget_allocation": {
            "accommodation": 40.0,
            "food": 25.0,
            "transport": 15.0,
            "activities": 12.0,
            "emergency_fund": 8.0
        }
    },
    "leh ladakh": {
        "trip_overview": {
            "weather_summary": "Cold desert weather. Day: 10°C to 18°C. Night: 0°C to 6°C. High UV index.",
            "safety_level": "Extremely Safe (Highly secure military zone)",
            "risk_score": 18,
            "currency_code": "INR",
            "exchange_rate_vs_usd": 1.0,
            "local_languages": ["Ladakhi", "Tibetan", "Hindi", "English"]
        },
        "risk_scorecard": {
            "physical_safety": 96,
            "health_medical": 65, # Remote area, limited hospitals
            "scams_theft": 90,
            "solo_traveler": 88
        },
        "safety_recommendations": [
            {
                "category": "Altitude Sickness (AMS)",
                "tips": [
                    "Acclimatize completely in Leh for the first 24-48 hours before traveling to Pangong or Nubra Valley.",
                    "Keep portable oxygen cans and medicines like Diamox handy.",
                    "Drink plenty of water but avoid alcohol and smoke completely."
                ]
            },
            {
                "category": "Road & Border Safety",
                "tips": [
                    "Obtain Inner Line Permits (ILP) online before going to Nubra, Pangong, or Tso Moriri.",
                    "Be careful of black ice and landslides on passes like Khardung La and Chang La.",
                    "Only rent local Ladakhi-registered taxis/scooters for local sightseeing (outside rental bikes are banned)."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Tourist Reception Centre, Leh",
            "address": "Fort Road, Leh, Ladakh 194101",
            "phone": "+91-1982-252-297",
            "website": "https://lahdcleh.nic.in/"
        },
        "emergency_contacts": {
            "police": "112 / +91-1982-252218",
            "fire_ambulance": "108 / +91-1982-252014",
            "tourist_helpline": "+91-1982-252-297"
        },
        "packing_list": [
            {"item": "Thermal Innerwear & Heavy Jacket", "category": "Clothing", "reason": "Evenings and high passes can drop below freezing temperatures."},
            {"item": "Diamox or Altitude Medicine", "category": "Health", "reason": "Crucial to combat Acute Mountain Sickness (AMS) at 11,000+ feet."},
            {"item": "High SPF Sunblock & Lip Balm", "category": "Personal Care", "reason": "Thin atmosphere causes extremely harsh UV rays and dry winds."},
            {"item": "Postpaid SIM Card (Airtel/Jio)", "category": "Electronics", "reason": "Only postpaid SIM connections work in Ladakh; prepaid connections are cut off for border security."},
            {"item": "Cash (Rupees)", "category": "Financial", "reason": "Network coverage is poor; UPI and card payments often fail outside Leh town."}
        ],
        "pocket_phrases": [
            {"phrase": "Julley", "pronunciation": "joo-lay", "meaning": "Hello / Goodbye / Thank you (Universal Ladakhi greeting)"},
            {"phrase": "Khamzang?", "pronunciation": "kham-zang", "meaning": "How are you?"},
            {"phrase": "Tukshey-che", "pronunciation": "took-shay-chay", "meaning": "Thank you"},
            {"phrase": "Mane madad chahiye", "pronunciation": "mah-nay mah-dad chah-hee-yea", "meaning": "I need help (in Hindi, widely spoken)"},
            {"phrase": "Aane po kitle?", "pronunciation": "ah-nay po kit-lay", "meaning": "How much for this?"}
        ],
        "budget_allocation": {
            "accommodation": 30.0,
            "food": 25.0,
            "transport": 25.0, # High cab rental costs
            "activities": 10.0,
            "emergency_fund": 10.0
        }
    },
    "jaipur": {
        "trip_overview": {
            "weather_summary": "Dry and hot (20°C to 36°C). High sunshine levels.",
            "safety_level": "Moderate Safety (Petty theft / vendor pressure)",
            "risk_score": 30,
            "currency_code": "INR",
            "exchange_rate_vs_usd": 1.0,
            "local_languages": ["Hindi", "Rajasthani", "English"]
        },
        "risk_scorecard": {
            "physical_safety": 82,
            "health_medical": 80,
            "scams_theft": 60,
            "solo_traveler": 78
        },
        "safety_recommendations": [
            {
                "category": "Vendor Pressure & Scams",
                "tips": [
                    "Politely but firmly decline aggressive tour guides and street sellers near Hawa Mahal and Amer Fort.",
                    "Verify prices in local markets and bargain (often starting at 50% of the quote).",
                    "Avoid gem and jewelry store recommendations from auto/cab drivers; they receive heavy commissions."
                ]
            },
            {
                "category": "Transport Safety",
                "tips": [
                    "Use app-based aggregators like Ola, Uber, or Rapido to avoid fare negotiations.",
                    "Ensure auto-rickshaws agree on a fixed price before starting if not using an app."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Rajasthan Tourist Information Centre, Jaipur",
            "address": "Government Hostel Campus, M.I. Road, Jaipur 302001",
            "phone": "+91-141-506-6688",
            "website": "https://www.tourism.rajasthan.gov.in/"
        },
        "emergency_contacts": {
            "police": "112 / 100",
            "fire_ambulance": "101 / 108",
            "tourist_helpline": "+91-141-220-3700"
        },
        "packing_list": [
            {"item": "Wide-brim Hat & Sunglasses", "category": "Clothing", "reason": "Protects against direct Rajasthan heat while touring forts."},
            {"item": "Lightweight Cotton Clothing", "category": "Clothing", "reason": "Keeps you cool while visiting monuments."},
            {"item": "Comfortable Walking Shoes", "category": "Clothing", "reason": "Monuments like Amber Fort involve walking uphill on stone pavements."},
            {"item": "Hand Sanitizer & Wipes", "category": "Personal Care", "reason": "Useful for cleaning up before trying local street delicacies."},
            {"item": "Small Change (10, 20, 50, 100 Notes)", "category": "Financial", "reason": "Useful for paying monuments fees and street vendors."}
        ],
        "pocket_phrases": [
            {"phrase": "Khamma Ghani", "pronunciation": "kham-mah ghah-nee", "meaning": "Hello / Greetings (traditional Rajasthani greeting)"},
            {"phrase": "Dhanyawaad", "pronunciation": "dhan-yah-vaad", "meaning": "Thank you (in Hindi)"},
            {"phrase": "Yeh kitne ka hai?", "pronunciation": "yeh kit-nay kah hai", "meaning": "How much is this?"},
            {"phrase": "Nahi chahiye", "pronunciation": "nah-hee chah-hee-yea", "meaning": "I do not want this (crucial for rejecting sellers)"},
            {"phrase": "Meri madad kijiye", "pronunciation": "may-ree mah-dad kee-jee-yea", "meaning": "Help me (in emergency)"}
        ],
        "budget_allocation": {
            "accommodation": 35.0,
            "food": 25.0,
            "transport": 15.0,
            "activities": 15.0,
            "emergency_fund": 10.0
        }
    },
    "tokyo": {
        "trip_overview": {
            "weather_summary": "Mild temperatures (15°C to 23°C) with occasional light showers. Perfect for city exploration.",
            "safety_level": "Extremely Safe (Low Crime)",
            "risk_score": 8,
            "currency_code": "JPY",
            "exchange_rate_vs_usd": 1.88, # 1 INR = 1.88 JPY
            "local_languages": ["Japanese"]
        },
        "risk_scorecard": {
            "physical_safety": 98,
            "health_medical": 95,
            "scams_theft": 92,
            "solo_traveler": 99
        },
        "safety_recommendations": [
            {
                "category": "General Safety",
                "tips": [
                    "Tokyo is one of the safest cities in the world. Solo walking at night is generally very safe.",
                    "Keep your passport on you as it is legally required for foreign tourists in Japan.",
                    "Earthquake preparedness: familiarise yourself with evacuation routes in your hotel."
                ]
            },
            {
                "category": "Local Scams",
                "tips": [
                    "Avoid bar-touts in nightlife districts like Roppongi and Kabukicho (Shinjuku) offering 'all you can drink' deals. They can lead to credit card skimming or spiked drinks.",
                    "Be wary of 'monk scams' near major temples where fake monks demand donations for gold cards."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Embassy of India, Tokyo",
            "address": "2-11 Kudan-minami, Chiyoda-ku, Tokyo 102-0074",
            "phone": "+81-3-3262-2391",
            "website": "https://www.indembassy-tokyo.gov.in/"
        },
        "emergency_contacts": {
            "police": "110",
            "fire_ambulance": "119",
            "tourist_helpline": "050-3786-2200"
        },
        "packing_list": [
            {"item": "Pocket Wi-Fi or eSIM", "category": "Electronics", "reason": "Essential for navigating Tokyo's complex subway system and streets."},
            {"item": "Comfortable Walking Shoes", "category": "Clothing", "reason": "You will easily walk 15,000+ steps daily exploring stations and sights."},
            {"item": "Cash (Yen)", "category": "Financial", "reason": "Many temples, street food vendors, and older establishments do not accept credit cards."},
            {"item": "Small Coin Purse", "category": "Accessories", "reason": "Japanese currency relies heavily on coins (1, 5, 10, 50, 100, 500 Yen)."},
            {"item": "Hand Towel / Handkerchief", "category": "Personal Care", "reason": "Many public restrooms in Japan do not provide paper towels or dryers."}
        ],
        "pocket_phrases": [
            {"phrase": "Sumimasen", "pronunciation": "soo-mee-mah-sen", "meaning": "Excuse me / I'm sorry (used to get attention or apologize)"},
            {"phrase": "Arigatou gozaimasu", "pronunciation": "ah-ree-gah-toe go-zy-mahs", "meaning": "Thank you very much"},
            {"phrase": "Eigo ga hanasemasu ka?", "pronunciation": "ay-go gah hah-nah-seh-mahs-kah", "meaning": "Can you speak English?"},
            {"phrase": "Tasukete kudasai", "pronunciation": "tah-soo-keh-teh koo-dah-sigh", "meaning": "Please help me (emergency)"},
            {"phrase": "Kore wa ikura desu ka?", "pronunciation": "ko-reh wah ee-koo-rah des kah", "meaning": "How much is this?"}
        ],
        "budget_allocation": {
            "accommodation": 35.0,
            "food": 30.0,
            "transport": 12.0,
            "activities": 13.0,
            "emergency_fund": 10.0
        }
    },
    "paris": {
        "trip_overview": {
            "weather_summary": "Cool breeze with average temperatures of 12°C to 19°C. Showers are common, so bring an umbrella.",
            "safety_level": "Moderate Safety (Exercise normal precautions)",
            "risk_score": 35,
            "currency_code": "EUR",
            "exchange_rate_vs_usd": 0.011, # 1 INR = 0.011 EUR
            "local_languages": ["French"]
        },
        "risk_scorecard": {
            "physical_safety": 82,
            "health_medical": 88,
            "scams_theft": 65,
            "solo_traveler": 80
        },
        "safety_recommendations": [
            {
                "category": "General Safety",
                "tips": [
                    "Be highly vigilant in crowded tourist spots like the Eiffel Tower, Louvre, and Montmartre.",
                    "Keep bags zipped and close to your body in the Metro (lines 1, 4, and RER B are notorious for pickpockets).",
                    "Do not leave your phone on tables in cafes where it can be easily grabbed."
                ]
            },
            {
                "category": "Local Scams",
                "tips": [
                    "The Friendship Bracelet Scam: Men near Sacré-Cœur will try to tie a string around your finger and demand payment.",
                    "The Petition Scam: Young kids pretending to be deaf/mute will ask you to sign a petition and then pocket your cash/distract you.",
                    "The Shell Game / Three Cards Game: Do not play or stand near streetside betters."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": "Embassy of India, Paris",
            "address": "15 Rue Alfred Dehodencq, 75016 Paris, France",
            "phone": "+33-1-40-50-70-70",
            "website": "https://www.eoiparis.gov.in/"
        },
        "emergency_contacts": {
            "police": "17",
            "fire_ambulance": "18",
            "tourist_helpline": "112"
        },
        "packing_list": [
            {"item": "Anti-Theft Crossbody Bag", "category": "Security", "reason": "Deters slash-and-grab pickpockets on public transit."},
            {"item": "Compact Umbrella", "category": "Clothing", "reason": "Parisian weather is notoriously unpredictable with sudden drizzles."},
            {"item": "Stylish Comfortable Shoes", "category": "Clothing", "reason": "Cobblestones around Paris require durable footwear; Parisians dress smart-casual."},
            {"item": "Universal EU Adapter (Type C/E)", "category": "Electronics", "reason": "Standard European plugs are required."},
            {"item": "Copy of Travel Insurance", "category": "Documents", "reason": "French hospitals require payment proof or insurance up front."}
        ],
        "pocket_phrases": [
            {"phrase": "Bonjour", "pronunciation": "bohn-zhoor", "meaning": "Hello / Good morning (always greet shopkeepers first)"},
            {"phrase": "S'il vous plaît", "pronunciation": "seel-voo-play", "meaning": "Please"},
            {"phrase": "Merci beaucoup", "pronunciation": "mair-see boh-koo", "meaning": "Thank you very much"},
            {"phrase": "Où sont les toilettes?", "pronunciation": "oo sohn lay twah-let", "meaning": "Where are the restrooms?"},
            {"phrase": "Aidez-moi, s'il vous plaît", "pronunciation": "ay-day mwah seel-voo-play", "meaning": "Please help me (emergency)"}
        ],
        "budget_allocation": {
            "accommodation": 40.0,
            "food": 25.0,
            "transport": 10.0,
            "activities": 15.0,
            "emergency_fund": 10.0
        }
    }
}


COUNTRY_LANG_MAP = {
    "japan": {
        "lang": "Japanese",
        "phrases": [
            {"local_phrase": "こんにちは", "english_meaning": "Hello / Namaste", "pronunciation": "Konnichiwa", "category": "Greeting"},
            {"local_phrase": "ありがとう", "english_meaning": "Thank you", "pronunciation": "Arigatou", "category": "Courtesy"},
            {"local_phrase": "さようなら", "english_meaning": "Goodbye", "pronunciation": "Sayounara", "category": "Greeting"},
            {"local_phrase": "助けて！", "english_meaning": "Help!", "pronunciation": "Tasukete!", "category": "Emergency"},
            {"local_phrase": "警察を呼んでください", "english_meaning": "Call the police", "pronunciation": "Keisatsu o yonde kudasai", "category": "Emergency"},
            {"local_phrase": "救急車を呼んでください", "english_meaning": "Call an ambulance", "pronunciation": "Kyūkyūsha o yonde kudasai", "category": "Emergency"},
            {"local_phrase": "病院はどこですか？", "english_meaning": "Where is the hospital?", "pronunciation": "Byōin wa doko desu ka?", "category": "Emergency"},
            {"local_phrase": "道に迷いました", "english_meaning": "I am lost", "pronunciation": "Michi ni mayoimashita", "category": "Navigation"},
            {"local_phrase": "英語を話せますか？", "english_meaning": "Do you speak English?", "pronunciation": "Eigo o hanasemasu ka?", "category": "Communication"},
            {"local_phrase": "これはいくらですか？", "english_meaning": "How much does this cost?", "pronunciation": "Kore wa ikura desu ka?", "category": "Shopping"}
        ]
    },
    "france": {
        "lang": "French",
        "phrases": [
            {"local_phrase": "Bonjour", "english_meaning": "Hello / Namaste", "pronunciation": "Bonjour", "category": "Greeting"},
            {"local_phrase": "Merci", "english_meaning": "Thank you", "pronunciation": "Merci", "category": "Courtesy"},
            {"local_phrase": "Au revoir", "english_meaning": "Goodbye", "pronunciation": "Au revoir", "category": "Greeting"},
            {"local_phrase": "Au secours !", "english_meaning": "Help!", "pronunciation": "Au secours", "category": "Emergency"},
            {"local_phrase": "Appelez la police", "english_meaning": "Call the police", "pronunciation": "Appelez la police", "category": "Emergency"},
            {"local_phrase": "Appelez une ambulance", "english_meaning": "Call an ambulance", "pronunciation": "Appelez une ambulance", "category": "Emergency"},
            {"local_phrase": "Où est l'hôpital ?", "english_meaning": "Where is the hospital?", "pronunciation": "Ou est l'hopital", "category": "Emergency"},
            {"local_phrase": "Je suis perdu", "english_meaning": "I am lost", "pronunciation": "Je suis perdu", "category": "Navigation"},
            {"local_phrase": "Parlez-vous anglais ?", "english_meaning": "Do you speak English?", "pronunciation": "Parlez-vous anglais", "category": "Communication"},
            {"local_phrase": "Combien ça coûte ?", "english_meaning": "How much does this cost?", "pronunciation": "Combien ca coute", "category": "Shopping"}
        ]
    },
    "india": {
        "lang": "Hindi",
        "phrases": [
            {"local_phrase": "नमस्ते", "english_meaning": "Hello / Namaste", "pronunciation": "Namaste", "category": "Greeting"},
            {"local_phrase": "धन्यवाद", "english_meaning": "Thank you", "pronunciation": "Dhanyawaad", "category": "Courtesy"},
            {"local_phrase": "अलविदा", "english_meaning": "Goodbye", "pronunciation": "Alvida", "category": "Greeting"},
            {"local_phrase": "मदद!", "english_meaning": "Help!", "pronunciation": "Madad!", "category": "Emergency"},
            {"local_phrase": "पुलिस को बुलाओ", "english_meaning": "Call the police", "pronunciation": "Police ko bulao", "category": "Emergency"},
            {"local_phrase": "एम्बुलेंस बुलाओ", "english_meaning": "Call an ambulance", "pronunciation": "Ambulance bulao", "category": "Emergency"},
            {"local_phrase": "अस्पताल कहाँ है?", "english_meaning": "Where is the hospital?", "pronunciation": "Aspatal kahan hai?", "category": "Emergency"},
            {"local_phrase": "मैं खो गया हूँ", "english_meaning": "I am lost", "pronunciation": "Main kho gaya hoon", "category": "Navigation"},
            {"local_phrase": "क्या आप अंग्रेज़ी बोलते हैं?", "english_meaning": "Do you speak English?", "pronunciation": "Kya aap angrezi bolte hain?", "category": "Communication"},
            {"local_phrase": "यह कितने का है?", "english_meaning": "How much does this cost?", "pronunciation": "Yeh kitne ka hai?", "category": "Shopping"}
        ]
    },
    "germany": {
        "lang": "German",
        "phrases": [
            {"local_phrase": "Guten Tag", "english_meaning": "Hello / Namaste", "pronunciation": "Guten Tag", "category": "Greeting"},
            {"local_phrase": "Vielen Dank", "english_meaning": "Thank you", "pronunciation": "Vielen Dank", "category": "Courtesy"},
            {"local_phrase": "Auf Wiedersehen", "english_meaning": "Goodbye", "pronunciation": "Auf Wiedersehen", "category": "Greeting"},
            {"local_phrase": "Hilfe!", "english_meaning": "Help!", "pronunciation": "Hilfe", "category": "Emergency"},
            {"local_phrase": "Rufen Sie die Polizei", "english_meaning": "Call the police", "pronunciation": "Rufen Sie die Polizei", "category": "Emergency"},
            {"local_phrase": "Rufen Sie einen Krankenwagen", "english_meaning": "Call an ambulance", "pronunciation": "Rufen Sie einen Krankenwagen", "category": "Emergency"},
            {"local_phrase": "Wo ist das Krankenhaus?", "english_meaning": "Where is the hospital?", "pronunciation": "Wo ist das Krankenhaus", "category": "Emergency"},
            {"local_phrase": "Ich habe mich verlaufen", "english_meaning": "I am lost", "pronunciation": "Ich habe mich verlaufen", "category": "Navigation"},
            {"local_phrase": "Sprechen Sie Englisch?", "english_meaning": "Do you speak English?", "pronunciation": "Sprechen Sie Englisch", "category": "Communication"},
            {"local_phrase": "Wie viel kostet das?", "english_meaning": "How much does this cost?", "pronunciation": "Wie viel kostet das", "category": "Shopping"}
        ]
    },
    "spain": {
        "lang": "Spanish",
        "phrases": [
            {"local_phrase": "Hola", "english_meaning": "Hello / Namaste", "pronunciation": "Hola", "category": "Greeting"},
            {"local_phrase": "Muchas gracias", "english_meaning": "Thank you", "pronunciation": "Muchas gracias", "category": "Courtesy"},
            {"local_phrase": "Adiós", "english_meaning": "Goodbye", "pronunciation": "Adios", "category": "Greeting"},
            {"local_phrase": "¡Ayuda!", "english_meaning": "Help!", "pronunciation": "Ayuda", "category": "Emergency"},
            {"local_phrase": "Llame a la policía", "english_meaning": "Call the police", "pronunciation": "Llame a la policia", "category": "Emergency"},
            {"local_phrase": "Llame a una ambulancia", "english_meaning": "Call an ambulance", "pronunciation": "Llame a una ambulancia", "category": "Emergency"},
            {"local_phrase": "¿Dónde está el hospital?", "english_meaning": "Where is the hospital?", "pronunciation": "Donde esta el hospital", "category": "Emergency"},
            {"local_phrase": "Estoy perdido", "english_meaning": "I am lost", "pronunciation": "Estoy perdido", "category": "Navigation"},
            {"local_phrase": "¿Habla inglés?", "english_meaning": "Do you speak English?", "pronunciation": "Habla ingles", "category": "Communication"},
            {"local_phrase": "¿Cuánto cuesta esto?", "english_meaning": "How much does this cost?", "pronunciation": "Cuanto cuesta esto", "category": "Shopping"}
        ]
    },
    "italy": {
        "lang": "Italian",
        "phrases": [
            {"local_phrase": "Buongiorno", "english_meaning": "Hello / Namaste", "pronunciation": "Buongiorno", "category": "Greeting"},
            {"local_phrase": "Grazie mille", "english_meaning": "Thank you", "pronunciation": "Grazie mille", "category": "Courtesy"},
            {"local_phrase": "Arrivederci", "english_meaning": "Goodbye", "pronunciation": "Arrivederci", "category": "Greeting"},
            {"local_phrase": "Aiuto!", "english_meaning": "Help!", "pronunciation": "Aiuto", "category": "Emergency"},
            {"local_phrase": "Chiami la polizia", "english_meaning": "Call the police", "pronunciation": "Chiami la polizia", "category": "Emergency"},
            {"local_phrase": "Chiami un'ambulanza", "english_meaning": "Call an ambulance", "pronunciation": "Chiami un'ambulanza", "category": "Emergency"},
            {"local_phrase": "Dov'è l'ospedale?", "english_meaning": "Where is the hospital?", "pronunciation": "Dov'e l'ospedale", "category": "Emergency"},
            {"local_phrase": "Mi sono perso", "english_meaning": "I am lost", "pronunciation": "Mi sono perso", "category": "Navigation"},
            {"local_phrase": "Parla inglese?", "english_meaning": "Do you speak English?", "pronunciation": "Parla inglese", "category": "Communication"},
            {"local_phrase": "Quanto costa questo?", "english_meaning": "How much does this cost?", "pronunciation": "Quanto costa questo", "category": "Shopping"}
        ]
    },
    "thailand": {
        "lang": "Thai",
        "phrases": [
            {"local_phrase": "สวัสดี", "english_meaning": "Hello / Namaste", "pronunciation": "Sawasdee", "category": "Greeting"},
            {"local_phrase": "ขอบคุณ", "english_meaning": "Thank you", "pronunciation": "Khob khun", "category": "Courtesy"},
            {"local_phrase": "ลาก่อน", "english_meaning": "Goodbye", "pronunciation": "La-gorn", "category": "Greeting"},
            {"local_phrase": "ช่วยด้วย!", "english_meaning": "Help!", "pronunciation": "Chuay duay!", "category": "Emergency"},
            {"local_phrase": "โทรเรียกตำรวจ", "english_meaning": "Call the police", "pronunciation": "Tho riak tam-ruat", "category": "Emergency"},
            {"local_phrase": "โทรเรียกรถพยาบาล", "english_meaning": "Call an ambulance", "pronunciation": "Tho riak rot pha-ya-ban", "category": "Emergency"},
            {"local_phrase": "โรงพยาบาลอยู่ที่ไหน?", "english_meaning": "Where is the hospital?", "pronunciation": "Rong pha-ya-ban yoo tee-nai?", "category": "Emergency"},
            {"local_phrase": "ฉันหลงทาง", "english_meaning": "I am lost", "pronunciation": "Chan long thang", "category": "Navigation"},
            {"local_phrase": "คุณพูดภาษาอังกฤษได้ไหม?", "english_meaning": "Do you speak English?", "pronunciation": "Khun poot pah-sah ahng-grit dai-mai?", "category": "Communication"},
            {"local_phrase": "ราคาเท่าไหร่?", "english_meaning": "How much does this cost?", "pronunciation": "Ra-kha tao-hrai?", "category": "Shopping"}
        ]
    },
    "egypt": {
        "lang": "Arabic",
        "phrases": [
            {"local_phrase": "مرحباً", "english_meaning": "Hello / Namaste", "pronunciation": "Marhaban", "category": "Greeting"},
            {"local_phrase": "شكراً", "english_meaning": "Thank you", "pronunciation": "Shukran", "category": "Courtesy"},
            {"local_phrase": "مع السلامة", "english_meaning": "Goodbye", "pronunciation": "Ma'as salama", "category": "Greeting"},
            {"local_phrase": "النجدة!", "english_meaning": "Help!", "pronunciation": "An-najda!", "category": "Emergency"},
            {"local_phrase": "اتصل بالشرطة", "english_meaning": "Call the police", "pronunciation": "Ittasil bish-shorta", "category": "Emergency"},
            {"local_phrase": "اتصل بالإسعاف", "english_meaning": "Call an ambulance", "pronunciation": "Ittasil bil-is'aaf", "category": "Emergency"},
            {"local_phrase": "أين المستشفى؟", "english_meaning": "Where is the hospital?", "pronunciation": "Ayna al-mustashfa?", "category": "Emergency"},
            {"local_phrase": "أنا تائه", "english_meaning": "I am lost", "pronunciation": "Ana ta'eh", "category": "Navigation"},
            {"local_phrase": "هل تتحدث الإنجليزية؟", "english_meaning": "Do you speak English?", "pronunciation": "Hal tatahaddath al-ingliziya?", "category": "Communication"},
            {"local_phrase": "بكم هذا؟", "english_meaning": "How much does this cost?", "pronunciation": "Bikam hadha?", "category": "Shopping"}
        ]
    },
    "united kingdom": {
        "lang": "English",
        "phrases": [
            {"local_phrase": "Hello", "english_meaning": "Hello / Namaste", "pronunciation": "Hello", "category": "Greeting"},
            {"local_phrase": "Thank you", "english_meaning": "Thank you", "pronunciation": "Thank you", "category": "Courtesy"},
            {"local_phrase": "Goodbye", "english_meaning": "Goodbye", "pronunciation": "Goodbye", "category": "Greeting"},
            {"local_phrase": "Help!", "english_meaning": "Help!", "pronunciation": "Help", "category": "Emergency"},
            {"local_phrase": "Call the police", "english_meaning": "Call the police", "pronunciation": "Call the police", "category": "Emergency"},
            {"local_phrase": "Call an ambulance", "english_meaning": "Call an ambulance", "pronunciation": "Call an ambulance", "category": "Emergency"},
            {"local_phrase": "Where is the hospital?", "english_meaning": "Where is the hospital?", "pronunciation": "Where is the hospital", "category": "Emergency"},
            {"local_phrase": "I am lost", "english_meaning": "I am lost", "pronunciation": "I am lost", "category": "Navigation"},
            {"local_phrase": "Do you speak English?", "english_meaning": "Do you speak English?", "pronunciation": "Do you speak English", "category": "Communication"},
            {"local_phrase": "How much does this cost?", "english_meaning": "How much does this cost?", "pronunciation": "How much does this cost", "category": "Shopping"}
        ]
    }
}


@st.cache_data(show_spinner=False)
def translate_pocket_phrases(destination, api_key=None):
    """
    Translates and transliterates 10 standard phrases using Gemini or cached local data.
    """
    dest_lower = destination.lower()
    
    # 1. Match local mock databases
    matched_country = None
    for country in COUNTRY_LANG_MAP.keys():
        if country in dest_lower:
            matched_country = country
            break
            
    if not matched_country:
        if any(x in dest_lower for x in ["london", "england", "uk", "us", "usa", "america", "canada", "australia", "singapore", "new zealand"]):
            matched_country = "united kingdom"
            
    if matched_country:
        return COUNTRY_LANG_MAP[matched_country]["phrases"]
        
    # 2. Call Gemini API if key is present
    if api_key and api_key.strip():
        try:
            genai.configure(api_key=api_key.strip())
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Identify the primary local language of {destination}.
            Translate and transliterate (provide Romanized pronunciation) the following 10 English phrases into that local language script.
            
            Phrases to translate:
            1. "Hello" -> Meaning: "Hello / Namaste", Category: "Greeting"
            2. "Thank you" -> Meaning: "Thank you", Category: "Courtesy"
            3. "Goodbye" -> Meaning: "Goodbye", Category: "Greeting"
            4. "Help!" -> Meaning: "Help!", Category: "Emergency"
            5. "Call the police" -> Meaning: "Call the police", Category: "Emergency"
            6. "Call an ambulance" -> Meaning: "Call an ambulance", Category: "Emergency"
            7. "Where is the hospital?" -> Meaning: "Where is the hospital?", Category: "Emergency"
            8. "I am lost" -> Meaning: "I am lost", Category: "Navigation"
            9. "Do you speak English?" -> Meaning: "Do you speak English?", Category: "Communication"
            10. "How much does this cost?" -> Meaning: "How much does this cost?", Category: "Shopping"

            You MUST respond with a valid JSON array only. Do not write markdown, code blocks (other than ```json), or explanations. The JSON array must contain exactly 10 objects, each matching the following schema:
            [
              {{
                "local_phrase": "translated phrase in the local native script (e.g. Kanji/Devanagari/Arabic/Latin)",
                "english_meaning": "the English meaning/phrase (exactly as requested above)",
                "pronunciation": "the Romanized pronunciation/transliteration of the local phrase",
                "category": "the phrase category (exactly as requested above)"
              }}
            ]
            """
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            phrases_list = json.loads(response.text)
            if isinstance(phrases_list, list) and len(phrases_list) == 10:
                return phrases_list
        except Exception as e:
            print(f"Gemini translation failed for {destination}: {e}. Falling back to default Spanish.")
            
    # 3. Default fallback to Spanish
    return [
        {"local_phrase": "Hola", "english_meaning": "Hello / Namaste", "pronunciation": "Hola", "category": "Greeting"},
        {"local_phrase": "Gracias", "english_meaning": "Thank you", "pronunciation": "Gracias", "category": "Courtesy"},
        {"local_phrase": "Adiós", "english_meaning": "Goodbye", "pronunciation": "Adios", "category": "Greeting"},
        {"local_phrase": "¡Ayuda!", "english_meaning": "Help!", "pronunciation": "Ayuda", "category": "Emergency"},
        {"local_phrase": "Llame a la policía", "english_meaning": "Call the police", "pronunciation": "Llame a la policia", "category": "Emergency"},
        {"local_phrase": "Llame a una ambulancia", "english_meaning": "Call an ambulance", "pronunciation": "Llame a una ambulancia", "category": "Emergency"},
        {"local_phrase": "¿Dónde está el hospital?", "english_meaning": "Where is the hospital?", "pronunciation": "Donde esta el hospital", "category": "Emergency"},
        {"local_phrase": "Estoy perdido", "english_meaning": "I am lost", "pronunciation": "Estoy perdido", "category": "Navigation"},
        {"local_phrase": "¿Habla inglés?", "english_meaning": "Do you speak English?", "pronunciation": "Habla ingles", "category": "Communication"},
        {"local_phrase": "¿Cuánto cuesta esto?", "english_meaning": "How much does this cost?", "pronunciation": "Cuanto cuesta esto", "category": "Shopping"}
    ]


def _get_generic_fallback(destination, days, budget, travel_type, citizenship):
    """Generates a highly-accurate generic plan if the destination isn't cached."""
    dest_name = destination.title()
    currency = "INR" if "india" in destination.lower() else "USD"
    rate = 1.0 if currency == "INR" else 0.012
    
    # Resolve local language dynamically based on destination
    dest_lower = destination.lower()
    matched_country = None
    for country in COUNTRY_LANG_MAP.keys():
        if country in dest_lower:
            matched_country = country
            break
    if not matched_country:
        if any(x in dest_lower for x in ["london", "england", "uk", "us", "usa", "america", "canada", "australia", "singapore", "new zealand"]):
            matched_country = "united kingdom"
        else:
            matched_country = "spain" # Default fallback
            
    lang_info = COUNTRY_LANG_MAP[matched_country]
    local_lang = lang_info["lang"]
    phrases = lang_info["phrases"]
    
    # Generic template customizer based on budget and type
    packing = [
        {"item": "Passport & Copies", "category": "Documents", "reason": "Crucial travel document. Always keep digital backups."},
        {"item": "Comfortable Shoes", "category": "Clothing", "reason": "Sightseeing requires extensive walking."},
        {"item": "Universal Power Adapter", "category": "Electronics", "reason": "Standard necessity for international wall outlets."},
        {"item": "Emergency First-Aid Kit", "category": "Health", "reason": f"Crucial for safety, especially on a {travel_type.lower()} trip."}
    ]
    if budget < 10000:
        packing.append({"item": "Reusable Water Bottle & Snacks", "category": "Food", "reason": "Saves daily expenses in city centers."})
    else:
        packing.append({"item": "Credit Card with No Foreign Fees", "category": "Financial", "reason": "Safest way to transact high budgets without carrying heavy cash."})

    itinerary = []
    for day in range(1, min(days + 1, 11)):
        itinerary.append({
            "day": day,
            "date": f"Day {day}",
            "theme": f"Explore {dest_name} Culture & Landmarks",
            "morning": f"Start the day at a highly rated local cafe. Head to {dest_name}'s historic central plaza or main museum.",
            "afternoon": f"Lunch nearby. Embark on a guided walking tour of the local districts to learn safety rules and orientation.",
            "evening": "Enjoy dinner featuring local delicacies, followed by a quiet stroll in a well-lit public area.",
            "dining": f"Highly-rated local restaurant specializing in {dest_name} cuisine."
        })

    fallback_data = {
        "trip_overview": {
            "weather_summary": "Varies. Expect average seasonal temperatures, mild winds. Check local forecasts closer to departure.",
            "safety_level": "Generally Safe (Standard vigilance)",
            "risk_score": 28,
            "currency_code": currency,
            "exchange_rate_vs_usd": rate, # Acts as rate_vs_inr
            "local_languages": [local_lang]
        },
        "risk_scorecard": {
            "physical_safety": 85,
            "health_medical": 80,
            "scams_theft": 70,
            "solo_traveler": 82
        },
        "safety_recommendations": [
            {
                "category": "General Safety Rules",
                "tips": [
                    f"Research dangerous neighbourhoods in {dest_name} before departure.",
                    "Avoid display of flashy jewelry, high-end cameras, or large bundles of cash.",
                    "Always use official, registered transport/cabs from transportation hubs."
                ]
            },
            {
                "category": "Theft & Scams Prevention",
                "tips": [
                    "Be alert in crowded street markets, train stations, and public plazas.",
                    "Be skeptical of over-friendly strangers offering unsolicited assistance or guides."
                ]
            }
        ],
        "embassy_info": {
            "embassy_name": f"Representative Office of {citizenship.title()} in {dest_name}",
            "address": f"Consular District, Central City Area, {dest_name}",
            "phone": "+91-11-2338-3418 (Indian Consular Support)",
            "website": f"https://www.embassy.gov.in/"
        },
        "emergency_contacts": {
            "police": "112",
            "fire_ambulance": "112",
            "tourist_helpline": "N/A"
        },
        "packing_list": packing,
        "pocket_phrases": phrases,
        "budget_allocation": {
            "accommodation": 35.0,
            "food": 25.0,
            "transport": 15.0,
            "activities": 15.0,
            "emergency_fund": 10.0
        }
    }
    return fallback_data


def generate_travel_plan(inputs, api_key=None):
    """
    Generates a personalized itinerary and safety outline.
    Toggles between a Live Gemini Client and a high-fidelity mock fallback model.
    """
    destination = inputs.get("destination", "").strip().lower()
    source = inputs.get("source", "").strip()
    start_date = inputs.get("start_date")
    end_date = inputs.get("end_date")
    budget = inputs.get("budget", 1000)
    travel_type = inputs.get("travel_type", "Solo")
    citizenship = inputs.get("citizenship", "India")
    interests = inputs.get("interests", [])
    activity_level = inputs.get("activity_level", "Moderate")

    # Calculate duration
    if start_date and end_date:
        days = (end_date - start_date).days + 1
    else:
        days = 5
    days = max(1, min(days, 10))  # Cap at 10 days for token & visual health

    # 1. LIVE GEMINI MODE
    if api_key and api_key.strip():
        try:
            genai.configure(api_key=api_key.strip())
            # Initialize the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are a professional travel planner and security analyst expert. 
            Generate a detailed, custom travel itinerary and security report for an Indian traveler.
            
            Trip Parameters:
            - From: {source}
            - To: {destination}
            - Duration: {days} Days (from {start_date} to {end_date})
            - Budget: ₹{budget} INR
            - Travel Type: {travel_type}
            - Traveler Citizenship: {citizenship}
            - Interests: {", ".join(interests)}
            - Activity Level: {activity_level}

            You MUST respond with a valid JSON object ONLY. Do not write markdown, code wraps (other than ```json), or notes. The JSON object must strictly match the following schema:
            {{
              "trip_overview": {{
                "weather_summary": "brief summary of average weather conditions for these dates",
                "safety_level": "advisory statement (e.g. Low Risk, Moderate Risk)",
                "risk_score": 15, // Integer 0 to 100 representing safety risk (higher = more risk)
                "currency_code": "3-letter currency code of destination",
                "exchange_rate_vs_usd": 1.5, // TREAT THIS FIELD AS exchange_rate_vs_inr: 1 INR = X destination currency
                "local_languages": ["Primary Languages spoken"]
              }},
              "risk_scorecard": {{
                "physical_safety": 90, // Integer 0-100 (100 = extremely safe, 0 = active conflict)
                "health_medical": 85, // Integer 0-100 (100 = world-class health, 0 = high disease/poor water)
                "scams_theft": 80, // Integer 0-100 (100 = zero theft, 0 = rampant pocket-picking/scams)
                "solo_traveler": 90 // Integer 0-100 (100 = perfect for solo travelers, 0 = risky)
              }},
              "safety_recommendations": [
                {{
                  "category": "Category name (e.g., General Safety, Transportation, Neighborhoods)",
                  "tips": ["Specific safety tip 1", "Specific safety tip 2"]
                }}
              ],
              "embassy_info": {{
                "embassy_name": "Official embassy or consulate details of {citizenship} in {destination}",
                "address": "physical address of the embassy/consulate",
                "phone": "telephone contact number",
                "website": "URL website address"
              }},
              "emergency_contacts": {{
                "police": "local police number",
                "fire_ambulance": "local fire/medical emergency number",
                "tourist_helpline": "specific tourist helpline or N/A"
              }},
              "itinerary": [
                {{
                  "day": 1,
                  "date": "formatted date",
                  "theme": "daily highlight theme",
                  "morning": "morning detailed activity matching traveler interests: {", ".join(interests)}",
                  "afternoon": "afternoon detailed activity matching interests and activity level: {activity_level}",
                  "evening": "evening detailed activity, focusing on dining and safety",
                  "dining": "recommended local dishes or safe restaurants"
                }}
              ],
              "packing_list": [
                {{
                  "item": "specific item name",
                  "category": "Clothing/Electronics/Security/Health",
                  "reason": "why this item is needed based on weather or itinerary"
                }}
              ],
              "pocket_phrases": [
                {{
                  "phrase": "Essential local phrase",
                  "pronunciation": "how to pronounce it phonetically",
                  "meaning": "English translation"
                }}
              ],
              "budget_allocation": {{
                "accommodation": 35.0, // percentage (must sum to 100 total)
                "food": 25.0,
                "transport": 15.0,
                "activities": 15.0,
                "emergency_fund": 10.0
              }}
            }}
            
            Double check that the JSON is valid, fully closed, and complies with all keys. If the country has multiple safety concerns, outline them in the tips. Provide customized information for an Indian citizen (including visa status warnings if any, and Indian Embassy coordinates in the destination). Customize the itinerary activities to match the user's travel type ({travel_type}) and activity level ({activity_level}).
            """
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            
            # Post-processing: patch date string names for itinerary
            for idx, day_plan in enumerate(data.get("itinerary", [])):
                day_plan["day"] = idx + 1
            
            try:
                data["pocket_phrases"] = translate_pocket_phrases(destination, api_key)
            except Exception as e:
                print(f"Failed to dynamically translate pocket phrases in live mode: {e}")
            
            return data
            
        except Exception as e:
            # If the Gemini call fails, fall back gracefully
            print(f"Gemini API failure: {e}. Falling back to high-fidelity engine.")
            pass

    # 2. LOCAL ENGINE / DEMO FALLBACK MODE
    # Match short destination key
    matched_key = None
    for k in MOCK_DESTINATIONS.keys():
        if k in destination:
            matched_key = k
            break
            
    if matched_key:
        data = MOCK_DESTINATIONS[matched_key].copy()
    else:
        data = _get_generic_fallback(destination, days, budget, travel_type, citizenship)

    # Personalize mock data with start/end dates
    itinerary = []
    base_data = data.copy()
    
    # Adjust itinerary days
    raw_itinerary = base_data.get("itinerary", [])
    
    # If the pre-cached itinerary is shorter than the requested days, repeat or extend it
    for i in range(days):
        if i < len(raw_itinerary):
            day_plan = raw_itinerary[i].copy()
        else:
            # Generate additional standard day
            day_plan = {
                "day": i + 1,
                "theme": f"Exploration & Leisure",
                "morning": "Check out local markets and souvenir shopping.",
                "afternoon": "Visit a scenic local park, garden, or modern museum district.",
                "evening": "Wind down with a fine-dining experience and night view.",
                "dining": "Recommended central bistro or family restaurant."
            }
        
        # Format actual dates if possible
        if start_date:
            try:
                import datetime
                current_date = start_date + datetime.timedelta(days=i)
                day_plan["date"] = current_date.strftime("%A, %b %d, %Y")
            except Exception:
                day_plan["date"] = f"Day {i+1}"
        else:
            day_plan["date"] = f"Day {i+1}"
            
        day_plan["day"] = i + 1
        itinerary.append(day_plan)
        
    base_data["itinerary"] = itinerary
    
    # Customize the embassy based on the user's citizenship
    if "india" in citizenship.lower() and not destination.endswith("india") and matched_key in ["tokyo", "paris"]:
        # Handled in the profile dictionary
        pass
    else:
        base_data["embassy_info"]["embassy_name"] = f"Representative Office of {citizenship.title()} in {destination.title()}"
    
    try:
        base_data["pocket_phrases"] = translate_pocket_phrases(destination, api_key)
    except Exception as e:
        print(f"Failed to dynamically translate pocket phrases in fallback mode: {e}")
    
    return base_data
