import os
import io
import json
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image, ImageDraw, ImageFont

# ---------- Load environment variables ----------
load_dotenv()

# ---------- Initialize Google Sheets ----------
SHEET_ID = "1uHj7lwx-6vsWu48hn9vT-c3a3WW4GAhOsZDo4cbjoY8"

def get_gsheet():
    """Connect to Google Sheet - works with both local files and Streamlit secrets"""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        # Try credentials.json file (for local development)
        elif os.path.exists('credentials.json'):
            creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        else:
            st.error("❌ No Google Sheets credentials found.")
            return None
            
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Could not connect to Google Sheets: {str(e)}")
        return None

def append_to_sheet(data):
    """Append response data to Google Sheet"""
    try:
        sheet = get_gsheet()
        if sheet is None:
            return False
        # Get current time in Malaysia Time (MYT, UTC+8)
        myt = timezone(timedelta(hours=8))
        timestamp = datetime.now(myt).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            data["name"],
            data["email"],
            data.get("phone", ""),
            data["most_d"],
            data["most_i"],
            data["most_s"],
            data["most_c"],
            data["least_d"],
            data["least_i"],
            data["least_s"],
            data["least_c"],
            data["comp_d"],
            data["comp_i"],
            data["comp_s"],
            data["comp_c"]
        ]
        
        # Add individual question responses (MOST and LEAST for each of 24 questions)
        for i in range(24):
            row.append(data.get(f"q{i+1}_most", ""))
            row.append(data.get(f"q{i+1}_least", ""))
        
        sheet.append_row(row)
        return True
    except Exception as e:
        # Silently fail if sheets save doesn't work
        return False

# ---------- Chart generation ----------
disc_config = {
    "MOST": {
        "grey_zones": [
            (0.00, 0.231, "#e0e0e0"),  # light top (90% of white zone)
            (0.488, 0.533, "#bfbfbf"),  # dark upper mid (35% of white zone)
            (0.533, 0.578, "#bfbfbf"),  # dark lower mid (35% of white zone)
            (0.835, 1.00, "#e0e0e0"),  # light bottom (64% of white zone)
        ],
        "coords": {
            "D": {
                17: 0.03,
                16: 0.05,
                15: 0.07,
                14: 0.14,
                12: 0.235,
                11: 0.27,
                10: 0.32,
                9: 0.34,
                8: 0.38,
                7: 0.42,
                6: 0.46,
                5: 0.485,
                4: 0.515,
                3: 0.545,
                2: 0.58,
                1: 0.665,
                0: 0.775
                },

            "I": {
                17: 0.07,
                16: 0.1,
                15: 0.14,
                13: 0.21,
                12: 0.235,
                11: 0.32,
                10: 0.35,
                9: 0.375,
                8: 0.42,
                7: 0.47,
                6: 0.49,
                5: 0.51,
                4: 0.53,
                3: 0.55,
                2: 0.59,
                1: 0.675,
                0: 0.80
            },

            "S": {
                17: 0.07,
                16: 0.21,
                15: 0.27,
                14: 0.325,
                13: 0.37,
                12: 0.4,
                11: 0.445,
                10: 0.48,
                9: 0.505,
                8: 0.525,
                7: 0.545,
                6: 0.56,
                5: 0.58,
                4: 0.625,
                3: 0.68,
                2: 0.74,
                1: 0.79,
                0: 0.865

            },


            "C": {
                14:  0.07,
                13: 0.1,
                12: 0.14,
                11: 0.3,
                10: 0.34,
                9: 0.38,
                8: 0.44,
                7: 0.475,
                6: 0.515,
                5: 0.545,
                4: 0.56,
                3: 0.645,
                2: 0.72,
                1: 0.775,
                0: 0.92

            },
        },
        "offsets": {"D":0.0,"I":0.0,"S":0.0,"C":0.0},
    },

    "LEAST": {
        "grey_zones": [
            (0.00, 0.231, "#e0e0e0"),  # light top (90% of white zone)
            (0.488, 0.533, "#bfbfbf"),  # dark upper mid (35% of white zone)
            (0.533, 0.578, "#bfbfbf"),  # dark lower mid (35% of white zone)
            (0.835, 1.00, "#e0e0e0"),  # light bottom (64% of white zone)
        ],
        "coords": {
            "D": {
                0: 0.07,
                1: 0.12,
                2: 0.27,
                3: 0.33,
                4: 0.38,
                5: 0.43,
                6: 0.46,
                7: 0.49,
                8: 0.51,
                9: 0.53,
                10: 0.54,
                11: 0.56,
                12: 0.58,
                13: 0.63,
                14: 0.665,
                15: 0.73,
                16: 0.765,
                17: 0.8,
                18: 0.865,
                19:0.96
                },

            "I": {
                0: 0.07,
                1: 0.235,
                2: 0.34,
                3: 0.43,
                4: 0.48,
                5: 0.52,
                6: 0.54,
                7: 0.595,
                8: 0.645, 
                9: 0.685,
                10: 0.75,
                11: 0.775,
                12: 0.82,
                13: 0.84,
                14: 0.885,
                16: 0.96

            },

            "S": {
                0:  0.07,
                1: 0.395,
                2: 0.46,
                3: 0.52,
                4: 0.54,
                5: 0.59,
                6: 0.63,
                7: 0.68,
                8: 0.74,
                9: 0.775,
                10: 0.795,
                11: 0.82,
                12: 0.885,
                14: 0.96
            },


            "C": {
                0:  0.07,
                1: 0.27,
                2: 0.395,
                3: 0.46,
                4: 0.49,
                5: 0.52,
                6: 0.54,
                7: 0.56,
                8: 0.575,
                9: 0.62,
                10: 0.68,
                11: 0.75,
                12: 0.775,
                13: 0.825,
                14: 0.855,
                15: 0.92,
                16: 0.96


            },
        },
        "offsets": {"D":0.0,"I":0.0,"S":0.0,"C":0.0},
    },

    "COMPOSITE": {
        "grey_zones": [
            (0.00, 0.231, "#e0e0e0"),  # light top (90% of white zone)
            (0.488, 0.533, "#bfbfbf"),  # dark upper mid (35% of white zone)
            (0.533, 0.578, "#bfbfbf"),  # dark lower mid (35% of white zone)
            (0.835, 1.00, "#e0e0e0"),  # light bottom (64% of white zone)
        ],
        "coords": {
            "D": {
                15: 0.04,
                14: 0.09,
                13: 0.115,
                12: 0.21,
                11: 0.235,
                9: 0.27,
                7: 0.33,
                5: 0.36,
                3: 0.40,
                1: 0.43,
                0: 0.46,
                -1: 0.48,
                -3: 0.50,
                -5: 0.525,
                -6: 0.54,
                -8: 0.56,
                -9: 0.58,
                -11: 0.62,
                -12: 0.65,
                -13: 0.68,
                -14: 0.72,
                -15: 0.75,
                -16: 0.8,
                },

            "I": {
                18:  0.09,
                16:  0.115,
                14:  0.16,
                12:  0.21,
                11:  0.235,
                9:  0.275,
                8:  0.34,
                7:  0.365,
                6:  0.405,
                4:  0.435,
                2:  0.49,
                0:  0.51,
                -1:  0.53,
                -3:  0.545,
                -4:  0.57,
                -5:  0.61,
                -6:  0.635,
                -7:  0.685,
                -8:  0.735,
                -9:  0.775,
                -11:  0.81,
                -12:  0.84,
                -13:  0.89,
                -14:  0.915,
                -16:  0.96,
            },

            "S": {
                17:  0.09,
                16:  0.17,
                15:  0.235,
                14:  0.275,
                13: 0.353,
                12: 0.39,
                10: 0.42,
                9: 0.46,
                7: 0.505,
                5: 0.53,
                3: 0.54,
                1: 0.565,
                0: 0.59,
                -1: 0.615,
                -2: 0.64,
                -4: 0.67,
                -5: 0.72,
                -6: 0.745,
                -8: 0.775,
                -9: 0.81,
                -10: 0.89,
                -12: 0.915,
                -13: 0.96
            },


            "C": {
                13:  0.09,
                12: 0.115,
                11: 0.21,
                10: 0.275,
                9: 0.34,
                8: 0.365,
                7: 0.39,
                6: 0.42,
                5: 0.44,
                4: 0.46,
                3: 0.48,
                2: 0.50,
                1: 0.52,
                0: 0.54,
                -1: 0.56,
                -3: 0.575,
                -4: 0.60,
                -5: 0.625,
                -6: 0.65,
                -7: 0.67,
                -8: 0.72,
                -9: 0.755,
                -10: 0.775,
                -11: 0.8,
                -12: 0.84,
                -13: 0.87,
                -14: 0.92,
                -15: 0.96
            },
        },
        "offsets": {
            "D": 0.0,
            "I": 0.0,
            "S": 0.0,
            "C": 0.0,
        },
    }   
}


# -------------------------------------------------------
# DRAW FUNCTION
# -------------------------------------------------------
def draw_disc_chart(most, least, comp, config):
    def clamp(v, lo, hi): return max(lo, min(hi, v))

    def grid_and_plot(ax, title, chart_type, values_dict):
        cfg = config[chart_type]

        # Draw grey zones
        for lo, hi, color in cfg["grey_zones"]:
            ax.axhspan(lo, hi, facecolor=color, alpha=1.0, zorder=0)

        # Add light black line in the middle
        ax.axhline(y=0.533, color="black", lw=1, alpha=0.4, zorder=1)

        labels = ["D", "I", "S", "C"]
        x = np.arange(len(labels))
        ypos_map = {}

        # Draw numbers for each column
        for col_idx, col in enumerate(labels):
            tick_map = cfg["coords"][col]
            ypos_map[col] = tick_map
            for v, y in tick_map.items():
                ax.text(col_idx, y, f"{v}", color="black", fontsize=18,
                        ha="center", va="center", zorder=1)

        # Plot red values
        xs, ys = [], []
        for col_idx, col in enumerate(labels):
            tick_map = ypos_map[col]
            v_in = values_dict[col]
            nearest = min(tick_map.keys(), key=lambda t: abs(t - v_in))
            xs.append(col_idx)
            ys.append(tick_map[nearest])

        ax.plot(xs, ys, color="red", lw=2, zorder=3)
        ax.scatter(xs, ys, color="red", s=50, zorder=4)
        for col_idx, y in zip(xs, ys):
            v = values_dict[labels[col_idx]]
            ax.text(col_idx + 0.15, y, f"{v}", color="red", fontsize=10,
                    fontweight="bold", ha="left", va="center", zorder=5)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=12, fontweight="bold")
        ax.set_xlim(-0.5, len(labels) - 0.2)
        ax.set_ylim(1, 0)
        ax.set_yticks([])
        ax.set_title(title, fontsize=12, fontweight="bold", pad=18)
        for s in ax.spines.values():
            s.set_linewidth(1.2)

    # Create 3 charts
    fig, axes = plt.subplots(1, 3, figsize=(12, 12))
    plt.subplots_adjust(wspace=0.08)
    fig.suptitle("DISC Graphs", fontsize=16, fontweight="bold")

    grid_and_plot(axes[0], "MOST\n(Projected Concept)", "MOST", most)
    grid_and_plot(axes[1], "LEAST\n(Private Concept)", "LEAST", least)
    grid_and_plot(axes[2], "COMPOSITE\n(Public Concept)", "COMPOSITE", comp)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=240, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# ---------------------------------------------
# Helper to visualize spacing tables
# ---------------------------------------------

# ---------- Google Sheets Integration ----------
def save_to_google_sheet(data):
    """Save form response data to Google Sheet including individual question responses"""
    try:
        # Get credentials from environment or service account file
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Try to use service account credentials from environment variable
        import json
        creds_dict = None
        
        # Check if credentials are in environment variable
        if os.getenv("GOOGLE_SHEETS_CREDENTIALS"):
            creds_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Fall back to file-based credentials
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        
        client = gspread.authorize(creds)
        
        # Open the specific Google Sheet by ID
        sheet_id = "1uHj7lwx-6vsWu48hn9vT-c3a3WW4GAhOsZDo4cbjoY8"
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1  # Use first sheet
        
        # Prepare row data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [
            timestamp,
            data.get("name", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("most_d", 0),
            data.get("most_i", 0),
            data.get("most_s", 0),
            data.get("most_c", 0),
            data.get("least_d", 0),
            data.get("least_i", 0),
            data.get("least_s", 0),
            data.get("least_c", 0),
            data.get("comp_d", 0),
            data.get("comp_i", 0),
            data.get("comp_s", 0),
            data.get("comp_c", 0),
        ]
        
        # Add individual question responses (MOST and LEAST for each of 24 questions)
        for i in range(24):
            row_data.append(data.get(f"q{i+1}_most", ""))
            row_data.append(data.get(f"q{i+1}_least", ""))
        
        # Append the row to the sheet
        worksheet.append_row(row_data)
        return True, "Data saved to Google Sheet successfully!"
        
    except Exception as e:
        return False, f"Failed to save to Google Sheet: {str(e)}"


# ---------- Email Sending Function ----------
def create_scores_image(name, most_scores, least_scores, comp_scores):
    """Create an image of the DISC scores table"""
    # Create image
    img_width = 800
    img_height = 400
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        score_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        score_font = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 30), "Your DISC Scores", font=title_font, fill='black')
    
    # Column headers
    y_pos = 120
    draw.text((50, y_pos), "MOST (Projected)", font=header_font, fill='black')
    draw.text((300, y_pos), "LEAST (Private)", font=header_font, fill='black')
    draw.text((550, y_pos), "COMPOSITE (Public)", font=header_font, fill='black')
    
    # Draw scores
    y_start = 180
    spacing = 50
    for i, letter in enumerate(['D', 'I', 'S', 'C']):
        y = y_start + (i * spacing)
        draw.text((50, y), f"{letter}: {most_scores[letter]}", font=score_font, fill='black')
        draw.text((300, y), f"{letter}: {least_scores[letter]}", font=score_font, fill='black')
        comp_val = comp_scores[letter]
        draw.text((550, y), f"{letter}: {comp_val:+d}", font=score_font, fill='black')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


def send_email_with_results(recipient_email, name, most_scores, least_scores, comp_scores, chart_bytes):
    """Send email with DISC scores and chart - works with both .env and Streamlit secrets"""
    try:
        # Get email credentials - try Streamlit secrets first, then environment variables
        if hasattr(st, 'secrets') and 'SENDER_EMAIL' in st.secrets:
            sender_email = st.secrets['SENDER_EMAIL']
            sender_password = st.secrets['SENDER_PASSWORD']
        else:
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            return False, "Email credentials not configured"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Your DISC Assessment Results - {name}"
        
        # Email body (HTML format for better styling)
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Hello {name},</h2>
    
    <p>Thank you for completing the DISC Personality Assessment!</p>
    
    <p>Please find your results attached:</p>
    <ol>
        <li>Your DISC Scores Summary</li>
        <li>Your Complete DISC Profile Chart</li>
    </ol>
    
    <h3 style="margin-top: 30px;">Your scores are:</h3>
    
    <div style="margin: 20px 0;">
        <p><strong>MOST (Projected Concept):</strong></p>
        <ul style="list-style: none; padding-left: 20px;">
            <li><strong>D:</strong> {most_scores['D']}</li>
            <li><strong>I:</strong> {most_scores['I']}</li>
            <li><strong>S:</strong> {most_scores['S']}</li>
            <li><strong>C:</strong> {most_scores['C']}</li>
        </ul>
    </div>
    
    <div style="margin: 20px 0;">
        <p><strong>LEAST (Private Concept):</strong></p>
        <ul style="list-style: none; padding-left: 20px;">
            <li><strong>D:</strong> {least_scores['D']}</li>
            <li><strong>I:</strong> {least_scores['I']}</li>
            <li><strong>S:</strong> {least_scores['S']}</li>
            <li><strong>C:</strong> {least_scores['C']}</li>
        </ul>
    </div>
    
    <div style="margin: 20px 0;">
        <p><strong>COMPOSITE (Public Concept):</strong></p>
        <ul style="list-style: none; padding-left: 20px;">
            <li><strong>D:</strong> {comp_scores['D']:+d}</li>
            <li><strong>I:</strong> {comp_scores['I']:+d}</li>
            <li><strong>S:</strong> {comp_scores['S']:+d}</li>
            <li><strong>C:</strong> {comp_scores['C']:+d}</li>
        </ul>
    </div>
    
    <p style="margin-top: 30px;">Best regards,<br>
    <strong>Mira!</strong></p>
</body>
</html>
"""
        msg.attach(MIMEText(body, 'html'))
        
        # Attach scores image
        scores_img = create_scores_image(name, most_scores, least_scores, comp_scores)
        scores_attachment = MIMEImage(scores_img)
        scores_attachment.add_header('Content-Disposition', 'attachment', filename='disc_scores.png')
        msg.attach(scores_attachment)
        
        # Attach chart
        chart_attachment = MIMEImage(chart_bytes)
        chart_attachment.add_header('Content-Disposition', 'attachment', filename='disc_chart.png')
        msg.attach(chart_attachment)
        
        # Send email via Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Email sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


# ---------- DISC Questions Mapping ----------
# Trait descriptions from spreadsheet
trait_descriptions = {
    "EXPRESSIVE": "I share my thoughts and feelings openly",
    "COMPLIANT": "I'm comfortable following rules and agreed decisions",
    "FORCEFUL": "I take charge and push things forward",
    "RESTRAINED": "I'm calm, measured, and don't rush to speak",
    "STRONG MINDED": "I stand firm in my views and don't change my mind easily",
    "CAREFUL": "I think things through carefully before acting",
    "EMOTIONAL": "I feel things deeply and express my emotions",
    "SATISFIED": "I'm generally content and at peace with how things are",
    "CORRECT": "I like to do things correctly and follow standards",
    "PIONEERING": "I like to try new things and take the lead",
    "CALM": "I stay calm and steady in most situations",
    "INFLUENTIAL": "I influence others and enjoy being persuasive",
    "PRECISE": "I pay close attention to details and like accuracy",
    "DOMINEERING": "I assert myself and take control when needed",
    "WILLING": "I am willing to support others and go along with the plan",
    "ATTRACTIVE": "I attract attention naturally and people notice me",
    "EVEN-TEMPERED": "I remain balanced and don't get upset easily",
    "STIMULATING": "I energize and excite those around me",
    "METICULOUS": "I am careful and precise in how I handle tasks",
    "DETERMINED": "I push forward to achieve my goals",
    "TIMID": "I prefer to stay in the background and avoid attention",
    "DEMANDING": "I expect results and want things done efficiently",
    "PATIENT": "I stay calm and don't get frustrated easily",
    "CAPTIVATING": "I draw others in and easily gain their interest",
    "CONSCIENTIOUS": "I focus on doing the right thing and following rules",
    "COMPANIONABLE": "I enjoy being with others and forming connections",
    "KIND": "I am thoughtful and considerate of others",
    "SELF-RELIANT": "I handle tasks on my own and rely on myself",
    "AGREEABLE": "I get along with others and value harmony",
    "SELF-CONTROLLED": "I manage my impulses and stay controlled",
    "PLAYFUL": "I enjoy fun and playful interactions",
    "PERSISTENT": "I persist and keep going until I succeed",
    "HIGH-SPIRITED": "I am energetic and full of life",
    "TALKATIVE": "I talk freely and enjoy interacting with people",
    "GOOD-NATURED": "I am easy-going and pleasant with others",
    "CONSERVATIVE": "I follow traditions and prefer familiar ways",
    "CONTENTED": "I feel content and satisfied with life",
    "IMPATIENT": "I like to act quickly and take initiative",
    "CONVINCING": "I persuade and influence others easily",
    "RESIGNED": "I accept situations as they are",
    "RESPECTFUL": "I respect others and follow rules and expectations",
    "GOOD MIXER": "I enjoy socializing and connecting with groups",
    "AGGRESSIVE": "I take initiative and act assertively",
    "GENTLE": "I am gentle and considerate in my approach",
    "POISED": "I stay calm and composed in social situations",
    "CONVENTIONAL": "I follow established norms and guidelines",
    "TAKES RISKS": "I take chances and enjoy trying new things",
    "ACCOMMODATING": "I am easy to get along with and helpful to others",
    "CONFIDENT": "I am confident and self-assured",
    "COOPERATIVE": "I cooperate well and work smoothly with others",
    "ARGUMENTATIVE": "I challenge others and push for my perspective",
    "RELAXED": "I stay relaxed and easy-going",
    "RESTLESS": "I keep moving and like activity and change",
    "WELL-DISCIPLINED": "I follow plans and routines carefully",
    "INSPIRING": "I inspire and motivate others",
    "CONSIDERATE": "I am thoughtful and caring toward others",
    "DIPLOMATIC": "I handle situations tactfully and diplomatically",
    "COURAGEOUS": "I face challenges bravely",
    "SYMPATHETIC": "I show understanding and empathy toward others",
    "OPTIMISTIC": "I look on the bright side and stay hopeful",
    "CHARMING": "I charm and delight people easily",
    "POSITIVE": "I stay positive and full of energy",
    "LENIENT": "I go easy on others and don't push too hard",
    "EXACTING": "I demand high standards and are exacting in work",
    "ADVENTUROUS": "I enjoy adventure and trying new experiences",
    "ENTHUSIASTIC": "I am enthusiastic and excited about life",
    "GOES-BY-THE-BOOK": "I follow rules and procedures closely",
    "LOYAL": "I remain loyal and dependable to people and causes",
    "HUMBLE": "I stay humble and don't seek attention",
    "GOOD LISTENER": "I listen carefully and pay attention to others",
    "ENTERTAINING": "I entertain and amuse people easily",
    "WILL POWER": "I have strong determination and willpower",
    "FUN-LOVING": "I enjoy having fun and making things enjoyable",
    "OBEDIENT": "I follow instructions and do what's asked",
    "TACTFUL": "I act tactfully and handle situations carefully",
    "COMPETITIVE": "I like to compete and strive to win",
    "CAUTIOUS": "I am careful and cautious in my actions",
    "NEIGHBORLY": "I am thoughtful and considerate toward neighbors",
    "VIGOROUS": "I am energetic and vigorous in what I do",
    "PERSUASIVE": "I persuade and convince others easily",
    "RESERVED": "I keep to myself and stay reserved",
    "OUTSPOKEN": "I speak directly and share my opinions openly",
    "STRICT": "I follow rules strictly and expect others to do the same",
    "ELOQUENT": "I speak clearly and expressively",
    "OBLIGING": "I am willing to help and accommodate others",
    "ANIMATED": "I are lively and full of energy",
    "DECISIVE": "I make decisions quickly and confidently",
    "ACCURATE": "I check details and make sure things are correct",
    "ASSERTIVE": "I take initiative and assert myself",
    "SOCIABLE": "I enjoy being social and spending time with others",
    "STEADY": "I am consistent and dependable",
    "ORDERLY": "I keep things organized and orderly",
    "OUTGOING": "I am outgoing and friendly",
    "BOLD": "I take risks and act boldly",
    "MODERATE": "I stay balanced and moderate in actions",
    "PERFECTIONIST": "I aim for perfection and want things done right"
}

# Situational contexts for each question with trait-specific actions
question_contexts = [
    {
        "situation": "You are in a group discussion (class, meeting, family planning) where ideas are being shared.",
        "actions": {
            "EXPRESSIVE": "I openly share my thoughts and feelings with the group.",
            "COMPLIANT": "I follow the agreed rules and decisions of the group.",
            "FORCEFUL": "I take charge and push the discussion forward.",
            "RESTRAINED": "I stay calm and speak only when necessary."
        }
    },
    {
        "situation": "Someone challenges your opinion on an issue you care about.",
        "actions": {
            "STRONG MINDED": "I stand firm and do not change my view easily.",
            "CAREFUL": "I think through the issue before responding.",
            "EMOTIONAL": "I react based on how strongly I feel.",
            "SATISFIED": "I feel at peace and don't feel the need to argue."
        }
    },
    {
        "situation": "You are asked to help improve how something is done (school work, office task, event planning).",
        "actions": {
            "CORRECT": "I ensure everything is done properly and according to standards.",
            "PIONEERING": "I suggest a new or different way to do it.",
            "CALM": "I keep things steady and avoid unnecessary changes.",
            "INFLUENTIAL": "I persuade others to support my ideas."
        }
    },
    {
        "situation": "You are working in a team with different personalities.",
        "actions": {
            "PRECISE": "I focus on accuracy and details.",
            "DOMINEERING": "I take control to ensure progress.",
            "WILLING": "I support others and go along with the plan.",
            "ATTRACTIVE": "I naturally draw people in and keep the mood positive."
        }
    },
    {
        "situation": "A deadline is approaching and pressure is increasing.",
        "actions": {
            "EVEN-TEMPERED": "I stay balanced and calm.",
            "STIMULATING": "I energise others to keep spirits up.",
            "METICULOUS": "I double-check details carefully.",
            "DETERMINED": "I push hard to get things done."
        }
    },
    {
        "situation": "You are placed in a situation where expectations are unclear.",
        "actions": {
            "TIMID": "I prefer to stay in the background.",
            "DEMANDING": "I set clear expectations and want results.",
            "PATIENT": "I wait calmly and observe.",
            "CAPTIVATING": "I engage others and keep things lively."
        }
    },
    {
        "situation": "Someone in your group is struggling.",
        "actions": {
            "CONSCIENTIOUS": "I should focus on what needs to be done and make sure responsibilities don't fall through.",
            "COMPANIONABLE": "I should check in, talk with them, and stay connected rather than leave them alone.",
            "KIND": "This isn't the time to push — I should be patient and give them space to cope.",
            "SELF-RELIANT": "They may need to work through this on their own to really grow."
        }
    },
    {
        "situation": "You order something you want, but you're told it's sold out.",
        "actions": {
            "AGREEABLE": "It's okay — I can adapt and choose something else.",
            "SELF-CONTROLLED": "I'll pause, keep my reaction in check, and respond calmly.",
            "PLAYFUL": "Maybe this change could be fun — I'll try something different.",
            "PERSISTENT": "I'd rather find a way to get what I originally planned for."
        }
    },
    {
        "situation": "You are in a social gathering or group event.",
        "actions": {
            "HIGH-SPIRITED": "I bring energy and take initiative.",
            "TALKATIVE": "I enjoy chatting and engaging with many people.",
            "GOOD-NATURED": "I am friendly and easy-going.",
            "CONSERVATIVE": "I stick to familiar people and routines."
        }
    },
    {
        "situation": "Things are not going exactly as planned.",
        "actions": {
            "CONTENTED": "I stay satisfied and accept the situation.",
            "IMPATIENT": "I want quick action and change.",
            "CONVINCING": "I persuade others to try a different approach.",
            "RESIGNED": "I accept that this is how things are."
        }
    },
    {
        "situation": "A disagreement arises in a group.",
        "actions": {
            "RESPECTFUL": "We need to keep this respectful and stay within agreed boundaries.",
            "GOOD MIXER": "Let's find some common ground so everyone can move forward.",
            "AGGRESSIVE": "I need to state my position clearly and stand my ground.",
            "GENTLE": "Things are getting tense — we should calm this down first."
        }
    },
    {
        "situation": "You are asked to make a decision with limited information.",
        "actions": {
            "POISED": "I stay composed and confident.",
            "CONVENTIONAL": "I stick to proven methods.",
            "TAKES RISKS": "I'm willing to try something bold.",
            "ACCOMMODATING": "I adjust to others' preferences."
        }
    },
    {
        "situation": "You are leading or supporting a group task.",
        "actions": {
            "CONFIDENT": "I speak up, share my views, and trust my judgement.",
            "COOPERATIVE": "I focus on helping everyone work together smoothly.",
            "ARGUMENTATIVE": "I challenge ideas directly and push for stronger solutions.",
            "RELAXED": "I stay easy-going and don't feel the need to control how things unfold."
        }
    },
    {
        "situation": "You are involved in a long-term project.",
        "actions": {
            "RESTLESS": "I want movement and progress quickly.",
            "WELL-DISCIPLINED": "I stick closely to plans and routines.",
            "INSPIRING": "I motivate others along the way.",
            "CONSIDERATE": "I look out for others' well-being."
        }
    },
    {
        "situation": "Someone close to you shares that they are uncertain about an important life or career decision and asks for your thoughts.",
        "actions": {
            "DIPLOMATIC": "I need to choose my words carefully — what I say could influence their decision.",
            "COURAGEOUS": "They shouldn't stay stuck; it may be better to act, even if there's some risk.",
            "SYMPATHETIC": "Before anything else, I want to understand how this situation is affecting them.",
            "OPTIMISTIC": "There are still good possibilities ahead, even if the path isn't clear yet."
        }
    },
    {
        "situation": "You are running a debrief after an activity, project, or event.",
        "actions": {
            "CHARMING": "Let's keep people engaged and talking.",
            "POSITIVE": "What do we do next?",
            "LENIENT": "Let's protect morale first.",
            "EXACTING": "This didn't meet the standard."
        }
    },
    {
        "situation": "You are offered an opportunity outside your comfort zone.",
        "actions": {
            "ADVENTUROUS": "I'm eager to try it.",
            "ENTHUSIASTIC": "I feel excited and energised.",
            "GOES-BY-THE-BOOK": "I check rules and procedures first.",
            "LOYAL": "I consider commitments I already have."
        }
    },
    {
        "situation": "You are part of a team discussion.",
        "actions": {
            "HUMBLE": "I don't need to stand out here.",
            "GOOD LISTENER": "Let me really hear what everyone is saying.",
            "ENTERTAINING": "Let's keep this lively and engaging.",
            "WILL POWER": "We need to move toward a decision."
        }
    },
    {
        "situation": "You are taking part in an organised activity with clear expectations (for example, a school task, group event, training session, or volunteer activity).",
        "actions": {
            "FUN-LOVING": "Let's make this enjoyable for everyone.",
            "OBEDIENT": "I'll stick closely to what's expected of me.",
            "TACTFUL": "I should be careful how my actions affect others.",
            "COMPETITIVE": "I want to stand out by doing this better."
        }
    },
    {
        "situation": "You interact with people in your neighbourhood or community.",
        "actions": {
            "CAUTIOUS": "I am careful with my words and actions to avoid problems or misunderstandings.",
            "NEIGHBORLY": "I am warm, friendly, and considerate toward everyone.",
            "VIGOROUS": "I take initiative and step in to get things moving or settled.",
            "PERSUASIVE": "I try to influence others and get them to see my point of view."
        }
    },
    {
        "situation": "You are asked to share your opinion publicly.",
        "actions": {
            "RESERVED": "I prefer to stay quiet.",
            "OUTSPOKEN": "I speak directly.",
            "STRICT": "I stick to rules and facts.",
            "ELOQUENT": "I express myself clearly and confidently."
        }
    },
    {
        "situation": "A decision needs to be made quickly.",
        "actions": {
            "OBLIGING": "I adjust to others.",
            "ANIMATED": "I bring energy into the moment.",
            "DECISIVE": "I decide quickly.",
            "ACCURATE": "I ensure correctness."
        }
    },
    {
        "situation": "You are working in a team with shared responsibility.",
        "actions": {
            "ASSERTIVE": "I take initiative.",
            "SOCIABLE": "I enjoy teamwork and interaction.",
            "STEADY": "I provide consistency.",
            "ORDERLY": "I keep things organised."
        }
    },
    {
        "situation": "You are given freedom to approach a task your own way.",
        "actions": {
            "OUTGOING": "I involve others enthusiastically.",
            "BOLD": "I take strong action.",
            "MODERATE": "I keep a balanced approach.",
            "PERFECTIONIST": "I aim to get everything right."
        }
    }
]

# Each option maps to D, I, S, or C
questions = [
    {"most": ["EXPRESSIVE", "COMPLIANT", "FORCEFUL", "RESTRAINED"], 
     "least": ["EXPRESSIVE", "COMPLIANT", "FORCEFUL", "RESTRAINED"],
     "mapping": ["I", "C", "D", "S"]},
    {"most": ["STRONG MINDED", "CAREFUL", "EMOTIONAL", "SATISFIED"],
     "least": ["STRONG MINDED", "CAREFUL", "EMOTIONAL", "SATISFIED"],
     "mapping": ["D", "C", "I", "S"]},
    {"most": ["CORRECT", "PIONEERING", "CALM", "INFLUENTIAL"],
     "least": ["CORRECT", "PIONEERING", "CALM", "INFLUENTIAL"],
     "mapping": ["C", "D", "S", "I"]},
    {"most": ["PRECISE", "DOMINEERING", "WILLING", "ATTRACTIVE"],
     "least": ["PRECISE", "DOMINEERING", "WILLING", "ATTRACTIVE"],
     "mapping": ["C", "D", "S", "I"]},
    {"most": ["EVEN-TEMPERED", "STIMULATING", "METICULOUS", "DETERMINED"],
     "least": ["EVEN-TEMPERED", "STIMULATING", "METICULOUS", "DETERMINED"],
     "mapping": ["S", "I", "C", "D"]},
    {"most": ["TIMID", "DEMANDING", "PATIENT", "CAPTIVATING"],
     "least": ["TIMID", "DEMANDING", "PATIENT", "CAPTIVATING"],
     "mapping": ["C", "D", "S", "I"]},
    {"most": ["CONSCIENTIOUS", "COMPANIONABLE", "KIND", "SELF-RELIANT"],
     "least": ["CONSCIENTIOUS", "COMPANIONABLE", "KIND", "SELF-RELIANT"],
     "mapping": ["C", "I", "S", "D"]},
    {"most": ["AGREEABLE", "SELF-CONTROLLED", "PLAYFUL", "PERSISTENT"],
     "least": ["AGREEABLE", "SELF-CONTROLLED", "PLAYFUL", "PERSISTENT"],
     "mapping": ["C", "S", "I", "D"]},
    {"most": ["HIGH-SPIRITED", "TALKATIVE", "GOOD-NATURED", "CONSERVATIVE"],
     "least": ["HIGH-SPIRITED", "TALKATIVE", "GOOD-NATURED", "CONSERVATIVE"],
     "mapping": ["D", "I", "S", "C"]},
    {"most": ["CONTENTED", "IMPATIENT", "CONVINCING", "RESIGNED"],
     "least": ["CONTENTED", "IMPATIENT", "CONVINCING", "RESIGNED"],
     "mapping": ["S", "D", "I", "C"]},
    {"most": ["RESPECTFUL", "GOOD MIXER", "AGGRESSIVE", "GENTLE"],
     "least": ["RESPECTFUL", "GOOD MIXER", "AGGRESSIVE", "GENTLE"],
     "mapping": ["C", "I", "D", "S"]},
    {"most": ["POISED", "CONVENTIONAL", "TAKES RISKS", "ACCOMMODATING"],
     "least": ["POISED", "CONVENTIONAL", "TAKES RISKS", "ACCOMMODATING"],
     "mapping": ["I", "C", "D", "S"]},
    {"most": ["CONFIDENT", "COOPERATIVE", "ARGUMENTATIVE", "RELAXED"],
     "least": ["CONFIDENT", "COOPERATIVE", "ARGUMENTATIVE", "RELAXED"],
     "mapping": ["I", "C", "D", "S"]},
    {"most": ["RESTLESS", "WELL-DISCIPLINED", "INSPIRING", "CONSIDERATE"],
     "least": ["RESTLESS", "WELL-DISCIPLINED", "INSPIRING", "CONSIDERATE"],
     "mapping": ["D", "C", "I", "S"]},
    {"most": ["DIPLOMATIC", "COURAGEOUS", "SYMPATHETIC", "OPTIMISTIC"],
     "least": ["DIPLOMATIC", "COURAGEOUS", "SYMPATHETIC", "OPTIMISTIC"],
     "mapping": ["C", "D", "S", "I"]},
    {"most": ["CHARMING", "POSITIVE", "LENIENT", "EXACTING"],
     "least": ["CHARMING", "POSITIVE", "LENIENT", "EXACTING"],
     "mapping": ["I", "D", "S", "C"]},
    {"most": ["ADVENTUROUS", "ENTHUSIASTIC", "GOES-BY-THE-BOOK", "LOYAL"],
     "least": ["ADVENTUROUS", "ENTHUSIASTIC", "GOES-BY-THE-BOOK", "LOYAL"],
     "mapping": ["D", "I", "C", "S"]},
    {"most": ["HUMBLE", "GOOD LISTENER", "ENTERTAINING", "WILL POWER"],
     "least": ["HUMBLE", "GOOD LISTENER", "ENTERTAINING", "WILL POWER"],
     "mapping": ["C", "S", "I", "D"]},
    {"most": ["FUN-LOVING", "OBEDIENT", "TACTFUL", "COMPETITIVE"],
     "least": ["FUN-LOVING", "OBEDIENT", "TACTFUL", "COMPETITIVE"],
     "mapping": ["I", "S", "C", "D"]},
    {"most": ["CAUTIOUS", "NEIGHBORLY", "VIGOROUS", "PERSUASIVE"],
     "least": ["CAUTIOUS", "NEIGHBORLY", "VIGOROUS", "PERSUASIVE"],
     "mapping": ["C", "S", "D", "I"]},
    {"most": ["RESERVED", "OUTSPOKEN", "STRICT", "ELOQUENT"],
     "least": ["RESERVED", "OUTSPOKEN", "STRICT", "ELOQUENT"],
     "mapping": ["S", "D", "C", "I"]},
    {"most": ["OBLIGING", "ANIMATED", "DECISIVE", "ACCURATE"],
     "least": ["OBLIGING", "ANIMATED", "DECISIVE", "ACCURATE"],
     "mapping": ["S", "I", "D", "C"]},
    {"most": ["ASSERTIVE", "SOCIABLE", "STEADY", "ORDERLY"],
     "least": ["ASSERTIVE", "SOCIABLE", "STEADY", "ORDERLY"],
     "mapping": ["D", "I", "S", "C"]},
    {"most": ["OUTGOING", "BOLD", "MODERATE", "PERFECTIONIST"],
     "least": ["OUTGOING", "BOLD", "MODERATE", "PERFECTIONIST"],
     "mapping": ["I", "D", "S", "C"]}
]

# ---------- Streamlit page setup ----------
st.set_page_config(page_title="DISC Assessment", page_icon="🧭", layout="centered")
st.title("🧭 DISC Personality Assessment")

# Create tabs
tab1, tab2 = st.tabs(["📋 Questionnaire", "✍️ Manual Input"])

# ---------- TAB 1: QUESTIONNAIRE ----------
with tab1:
    st.markdown("### Complete the DISC Assessment")
    st.markdown("For each question, select the word that is **MOST** like you and **LEAST** like you.")
    
    # User info
    name = st.text_input("Full Name", key="q_name")
    email = st.text_input("Email Address", key="q_email")
    phone = st.text_input("WhatsApp Number (optional)", key="q_phone")
    
    # Troubleshooting: Save/Load responses
    with st.expander("🔧 Troubleshooting Mode"):
        st.markdown("**Save Current Responses**")
        if st.button("Save Current Progress"):
            if 'most_responses' in st.session_state and 'least_responses' in st.session_state:
                st.session_state.saved_most = st.session_state.most_responses.copy()
                st.session_state.saved_least = st.session_state.least_responses.copy()
                st.success("✅ Responses saved!")
            else:
                st.warning("No responses to save yet.")
        
        st.markdown("**Load Saved Responses**")
        if st.button("Load Saved Progress"):
            if 'saved_most' in st.session_state and 'saved_least' in st.session_state:
                st.session_state.most_responses = st.session_state.saved_most.copy()
                st.session_state.least_responses = st.session_state.saved_least.copy()
                st.success("✅ Saved responses loaded! Please scroll down to see them.")
                st.rerun()
            else:
                st.warning("No saved responses found.")
        
        if st.button("Clear All Responses"):
            st.session_state.most_responses = [None] * 24
            st.session_state.least_responses = [None] * 24
            st.success("✅ All responses cleared!")
            st.rerun()
    
    st.markdown("---")
    
    # Store responses
    if 'most_responses' not in st.session_state:
        st.session_state.most_responses = [None] * 24
    if 'least_responses' not in st.session_state:
        st.session_state.least_responses = [None] * 24
    
    # Callback function to update responses immediately
    def update_most_response(question_idx):
        def callback():
            widget_key = f"most_{question_idx}"
            if widget_key in st.session_state:
                st.session_state.most_responses[question_idx] = st.session_state[widget_key]
        return callback
    
    def update_least_response(question_idx):
        def callback():
            widget_key = f"least_{question_idx}"
            if widget_key in st.session_state:
                st.session_state.least_responses[question_idx] = st.session_state[widget_key]
        return callback
    
    # Calculate progress
    completed_questions = sum(1 for i in range(24) 
                            if st.session_state.most_responses[i] is not None 
                            and st.session_state.least_responses[i] is not None)
    progress_percent = completed_questions / 24
    
    # Add fixed progress bar at top using custom CSS
    st.markdown(
        f"""
        <style>
        .fixed-progress {{
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            background-color: white;
            z-index: 999;
            padding: 1rem;
            border-bottom: 2px solid #f0f2f6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .progress-text {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #262730;
            font-size: 14px;
        }}
        .progress-bar-container {{
            width: 100%;
            height: 10px;
            background-color: #f0f2f6;
            border-radius: 5px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1f77b4 0%, #4a9eff 100%);
            transition: width 0.3s ease;
            border-radius: 5px;
        }}
        .spacer {{
            height: 80px;
        }}
        </style>
        <div class="fixed-progress">
            <div class="progress-text">📝 Progress: {completed_questions}/24 questions completed ({int(progress_percent * 100)}%)</div>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: {progress_percent * 100}%"></div>
            </div>
        </div>
        <div class="spacer"></div>
        """,
        unsafe_allow_html=True
    )
    
    # Display all questions
    for i, q in enumerate(questions):
        st.markdown(f"### Question {i+1}")
        
        # Get the context for this question
        context = question_contexts[i]
        
        # Display situational context with specific actions in a collapsible expander
        with st.expander("Need help? Example here", expanded=False):
            st.markdown(f"**Situation:** *{context['situation']}*")
            st.markdown("")  # Add spacing
            
            # Show the contextual actions for each trait option
            for trait, action in context['actions'].items():
                st.markdown(f"• **{trait}**: *{action}*")
        
        col1, col2 = st.columns(2)
        
        # Get current widget values (these update immediately when user clicks)
        most_widget_key = f"most_{i}"
        least_widget_key = f"least_{i}"
        
        # Get current selections from widget keys or session state
        current_most = st.session_state.get(most_widget_key) or st.session_state.most_responses[i]
        current_least = st.session_state.get(least_widget_key) or st.session_state.least_responses[i]
        
        with col1:
            st.markdown("**MOST like you**")
            # Filter out the current LEAST choice from MOST options
            available_most = [opt for opt in q["most"] if opt != current_least] if current_least else q["most"]
            # Find the index of the saved choice if it exists in available options
            most_index = available_most.index(current_most) if current_most and current_most in available_most else None
            most_choice = st.radio(
                f"Select one:",
                options=available_most,
                key=most_widget_key,
                index=most_index,
                on_change=update_most_response(i)
            )
            # Update our tracking array
            if most_choice:
                st.session_state.most_responses[i] = most_choice
        
        with col2:
            st.markdown("**LEAST like you**")
            # Get the updated MOST choice from widget
            updated_most = st.session_state.get(most_widget_key) or current_most
            # Filter out the current MOST choice from LEAST options
            available_least = [opt for opt in q["least"] if opt != updated_most] if updated_most else q["least"]
            # Find the index of the saved choice if it exists in available options
            least_index = available_least.index(current_least) if current_least and current_least in available_least else None
            least_choice = st.radio(
                f"Select one: ",
                options=available_least,
                key=least_widget_key,
                index=least_index,
                on_change=update_least_response(i)
            )
            # Update our tracking array
            if least_choice:
                st.session_state.least_responses[i] = least_choice
        
        st.markdown("---")
    
    # Calculate scores and submit
    if st.button("Calculate My DISC Profile", type="primary", key="submit_questionnaire"):
        # Validate all questions answered
        if None in st.session_state.most_responses or None in st.session_state.least_responses:
            st.error("Please answer all questions before submitting.")
        elif not name or not email:
            st.error("Please fill in your name and email.")
        else:
            # Calculate DISC scores
            most_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
            least_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
            
            for i, q in enumerate(questions):
                # Get the selected options
                most_selected = st.session_state.most_responses[i]
                least_selected = st.session_state.least_responses[i]
                
                # Find which index was selected
                most_idx = q["most"].index(most_selected)
                least_idx = q["least"].index(least_selected)
                
                # Map to DISC
                most_trait = q["mapping"][most_idx]
                least_trait = q["mapping"][least_idx]
                
                most_scores[most_trait] += 1
                least_scores[least_trait] += 1
            
            # Calculate composite (MOST - LEAST)
            comp_scores = {
                "D": most_scores["D"] - least_scores["D"],
                "I": most_scores["I"] - least_scores["I"],
                "S": most_scores["S"] - least_scores["S"],
                "C": most_scores["C"] - least_scores["C"]
            }
            
            # Display scores
            st.success("✅ Assessment completed!")
            st.markdown("### Your DISC Scores")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**MOST (Projected)**")
                st.write(f"D: {most_scores['D']}")
                st.write(f"I: {most_scores['I']}")
                st.write(f"S: {most_scores['S']}")
                st.write(f"C: {most_scores['C']}")
            
            with col2:
                st.markdown("**LEAST (Private)**")
                st.write(f"D: {least_scores['D']}")
                st.write(f"I: {least_scores['I']}")
                st.write(f"S: {least_scores['S']}")
                st.write(f"C: {least_scores['C']}")
            
            with col3:
                st.markdown("**COMPOSITE (Public)**")
                st.write(f"D: {comp_scores['D']:+d}")
                st.write(f"I: {comp_scores['I']:+d}")
                st.write(f"S: {comp_scores['S']:+d}")
                st.write(f"C: {comp_scores['C']:+d}")
            
            # Save to database
            data = {
                "name": name,
                "email": email,
                "phone": phone,
                "most_d": most_scores["D"],
                "most_i": most_scores["I"],
                "most_s": most_scores["S"],
                "most_c": most_scores["C"],
                "least_d": least_scores["D"],
                "least_i": least_scores["I"],
                "least_s": least_scores["S"],
                "least_c": least_scores["C"],
                "comp_d": comp_scores["D"],
                "comp_i": comp_scores["I"],
                "comp_s": comp_scores["S"],
                "comp_c": comp_scores["C"]
            }
            
            # Add individual question responses
            for i in range(24):
                data[f"q{i+1}_most"] = st.session_state.most_responses[i]
                data[f"q{i+1}_least"] = st.session_state.least_responses[i]
            
            # Save to Google Sheets
            append_to_sheet(data)
            
            # Generate chart
            img_bytes = draw_disc_chart(most_scores, least_scores, comp_scores, disc_config)
            
            # Send email with results
            email_success, email_message = send_email_with_results(
                email, name, most_scores, least_scores, comp_scores, img_bytes
            )
            if email_success:
                st.success(f"✅ Results sent to {email}")
            else:
                st.warning(f"⚠️ Could not send email: {email_message}")
            
            st.image(img_bytes, caption=f"{name}'s DISC Profile Chart")
            
            # Show detailed breakdown for troubleshooting
            with st.expander("📊 View Detailed Question Breakdown"):
                st.markdown("### Question-by-Question DISC Mapping")
                for i, q in enumerate(questions):
                    most_selected = st.session_state.most_responses[i]
                    least_selected = st.session_state.least_responses[i]
                    
                    most_idx = q["most"].index(most_selected)
                    least_idx = q["least"].index(least_selected)
                    
                    most_trait = q["mapping"][most_idx]
                    least_trait = q["mapping"][least_idx]
                    
                    st.markdown(f"**Question {i+1}:**")
                    st.write(f"MOST: {most_selected} → **{most_trait}**")
                    st.write(f"LEAST: {least_selected} → **{least_trait}**")
                    st.markdown("---")

# ---------- TAB 2: MANUAL INPUT ----------
with tab2:
    st.markdown("### Manual Score Input")
    st.markdown("Enter your pre-calculated DISC scores manually.")
    
    name_manual = st.text_input("Full Name", key="m_name")
    email_manual = st.text_input("Email Address", key="m_email")
    phone_manual = st.text_input("WhatsApp Number (optional)", key="m_phone")
    
    st.markdown("### MOST (Projected Concept)")
    col1, col2, col3, col4 = st.columns(4)
    with col1: most_d = st.number_input("D", step=1, key="m_most_d")
    with col2: most_i = st.number_input("I", step=1, key="m_most_i")
    with col3: most_s = st.number_input("S", step=1, key="m_most_s")
    with col4: most_c = st.number_input("C", step=1, key="m_most_c")
    
    st.markdown("### LEAST (Private Concept)")
    col5, col6, col7, col8 = st.columns(4)
    with col5: least_d = st.number_input("D ", step=1, key="m_least_d")
    with col6: least_i = st.number_input("I ", step=1, key="m_least_i")
    with col7: least_s = st.number_input("S ", step=1, key="m_least_s")
    with col8: least_c = st.number_input("C ", step=1, key="m_least_c")
    
    st.markdown("### COMPOSITE (Public Concept)")
    col9, col10, col11, col12 = st.columns(4)
    with col9: comp_d = st.number_input("D  ", step=1, key="m_comp_d")
    with col10: comp_i = st.number_input("I  ", step=1, key="m_comp_i")
    with col11: comp_s = st.number_input("S  ", step=1, key="m_comp_s")
    with col12: comp_c = st.number_input("C  ", step=1, key="m_comp_c")
    
    if st.button("Submit Manual Scores", type="primary"):
        if not name_manual or not email_manual:
            st.error("Please fill in at least your name and email.")
        else:
            data = {
                "name": name_manual,
                "email": email_manual,
                "phone": phone_manual,
                "most_d": int(most_d),
                "most_i": int(most_i),
                "most_s": int(most_s),
                "most_c": int(most_c),
                "least_d": int(least_d),
                "least_i": int(least_i),
                "least_s": int(least_s),
                "least_c": int(least_c),
                "comp_d": int(comp_d),
                "comp_i": int(comp_i),
                "comp_s": int(comp_s),
                "comp_c": int(comp_c)
            }
            
            # Save to Google Sheets
            append_to_sheet(data)
            
            most = {"D": most_d, "I": most_i, "S": most_s, "C": most_c}
            least = {"D": least_d, "I": least_i, "S": least_s, "C": least_c}
            comp = {"D": comp_d, "I": comp_i, "S": comp_s, "C": comp_c}
            
            img_bytes = draw_disc_chart(most, least, comp, disc_config)
            
            # Send email with results
            email_success, email_message = send_email_with_results(
                email_manual, name_manual, most, least, comp, img_bytes
            )
            if email_success:
                st.success(f"✅ Results sent to {email_manual}")
            else:
                st.warning(f"⚠️ Could not send email: {email_message}")
            
            st.image(img_bytes, caption=f"{name_manual}'s DISC Chart")
