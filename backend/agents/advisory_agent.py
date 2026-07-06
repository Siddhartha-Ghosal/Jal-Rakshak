def generate_advisory(contamination_signs: list, risk_level: str) -> dict:
    """
    Generates plain-language safety recommendations in English and Hindi
    based on the risk level and specific contamination signs found.
    """
    english_points = []
    hindi_points = []
    
    # Check individual signs and fetch corresponding advisories
    if not contamination_signs:
        english_points.append(
            "✅ <strong>No visible contamination:</strong> Water appears clear. However, micro-bacterial pathogens "
            "may still exist. Standard filtration and boiling are recommended before drinking."
        )
        hindi_points.append(
            "✅ <strong>कोई स्पष्ट प्रदूषण नहीं:</strong> पानी साफ दिख रहा है। हालांकि, अदृश्य बैक्टीरिया फिर भी हो सकते हैं। "
            "पीने से पहले छानना और उबालना हमेशा सुरक्षित रहता है।"
        )
    
    if "algae" in contamination_signs:
        english_points.append(
            "⚠️ <strong>Algae Scum:</strong> May contain toxic cyanobacteria. <strong>DO NOT drink, cook, or bathe.</strong> "
            "Boiling does NOT destroy these toxins. Keep livestock and pets away."
        )
        hindi_points.append(
            "⚠️ <strong>शैवाल (काई):</strong> इसमें विषैले पदार्थ हो सकते हैं। <strong>पीने, खाना पकाने या नहाने के लिए उपयोग न करें।</strong> "
            "उबालने से ये विषैले पदार्थ नष्ट नहीं होते। पशुओं को दूर रखें।"
        )
        
    if "discoloration" in contamination_signs:
        english_points.append(
            "⚠️ <strong>Discolored/Turbid Water:</strong> Suggests heavy mud or chemical runoff. Avoid direct use. "
            "Use a sand/cloth filter to clear, then boil vigorously for 2+ minutes."
        )
        hindi_points.append(
            "⚠️ <strong>गंदा/मटमैला पानी:</strong> मिट्टी या रसायनों के बहाव को दर्शाता है। सीधे पीने से बचें। "
            "रेत या साफ कपड़े से छानें, फिर 2+ मिनट तक अच्छी तरह उबालें।"
        )
        
    if "foam" in contamination_signs:
        english_points.append(
            "⚠️ <strong>Foam/Froth:</strong> Indicates chemical detergents or industrial discharge. <strong>Highly unsafe.</strong> "
            "Do not use for drinking, cooking, washing, or livestock."
        )
        hindi_points.append(
            "⚠️ <strong>झाग/फेन:</strong> रासायनिक डिटर्जेंट या औद्योगिक कचरा दर्शाता है। <strong>अत्यंत असुरक्षित।</strong> "
            "पीने, खाना पकाने, कपड़ा धोने या पशुओं के लिए उपयोग न करें।"
        )
        
    if "debris" in contamination_signs:
        english_points.append(
            "⚠️ <strong>Floating Debris:</strong> Trash, plastics, or organic matter can harbor severe pathogens. "
            "Physically remove debris and filter. Treat with chlorine tablets if boiling is unavailable."
        )
        hindi_points.append(
            "⚠️ <strong>तैरता हुआ कचरा:</strong> प्लास्टिक या जैविक कचरा हानिकारक कीटाणुओं को बढ़ावा देता है। "
            "कचरा बाहर निकालें और छानें। उबालना संभव न हो तो क्लोरीन की गोली डालें।"
        )

    # General risk level headers
    if risk_level == "High":
        english_header = "🚨 <strong>CRITICAL ALERT:</strong> Highly contaminated source. Do not consume."
        hindi_header = "🚨 <strong>गंभीर चेतावनी:</strong> अत्यधिक प्रदूषित जल स्रोत। बिल्कुल सेवन न करें।"
    elif risk_level == "Medium":
        english_header = "⚠️ <strong>WARNING:</strong> Moderate contamination signs present. Use caution."
        hindi_header = "⚠️ <strong>चेतावनी:</strong> सामान्य प्रदूषण के लक्षण मौजूद हैं। सावधानी बरतें।"
    else:
        english_header = "✅ <strong>GENERAL ADVISORY:</strong> Water appears clear."
        hindi_header = "✅ <strong>सामान्य सलाह:</strong> पानी साफ दिखाई दे रहा है।"

    # Generate HTML content for front-end rendering
    english_html = f"<h4>{english_header}</h4><ul>" + "".join([f"<li>{pt}</li>" for pt in english_points]) + "</ul>"
    hindi_html = f"<h4>{hindi_header}</h4><ul>" + "".join([f"<li>{pt}</li>" for pt in hindi_points]) + "</ul>"

    # Add escalation notice if risk is High
    if risk_level == "High":
        english_html += "<p style='color: #ef4444; font-weight: bold;'>Escalation trigger is active. Authorities are being notified.</p>"
        hindi_html += "<p style='color: #ef4444; font-weight: bold;'>अधिकारियों को सूचित करने की प्रक्रिया शुरू कर दी गई है।</p>"

    return {
        "status": "success",
        "risk_level": risk_level,
        "advisory_en": english_html,
        "advisory_hi": hindi_html,
        "raw_points_en": [p.replace("<strong>", "").replace("</strong>", "") for p in english_points],
        "raw_points_hi": [p.replace("<strong>", "").replace("</strong>", "") for p in hindi_points]
    }
