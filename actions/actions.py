from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActionExecutionRejected  # ✅ ADD THIS
import psycopg2
import re
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from datetime import datetime
import random
from rasa_sdk.events import ConversationPaused, ConversationResumed
from rasa_sdk.events import AllSlotsReset, Form
from rasa_sdk.events import SessionStarted, ActionExecuted


DB_CONFIG = {
    "host": "localhost",
    "database": "rasa_db",
    "user": "postgres",
    "password": "5227728",
    "port": "5432"
}


class ActionCheckTermsBeforeService(Action):
    """Check terms before showing any service response"""
    def name(self) -> str:
        return "action_check_terms_before_service"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # Block service - show terms and STOP execution
            dispatcher.utter_message(response="utter_greet")
            # Return empty list to prevent subsequent actions
            from rasa_sdk.events import UserUtteranceReverted 
            return [UserUtteranceReverted()]
        
        # Terms accepted - continue to next action in rule
        return []

class ActionCheckTermsBeforeCarousel(Action):
    """Check if user has agreed to terms before showing carousel"""
    def name(self) -> str:
        return "action_check_terms_before_carousel"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # User hasn't agreed to terms yet
            dispatcher.utter_message(
                text=(
                    "⚠️ Please accept our Terms of Use and Privacy Policy first.\n\n"
                    "Click 'I Agree' to continue."
                ),
                buttons=[
                    {
                        "title": "I Agree",
                        "payload": "/accept_terms"
                    }
                ]
            )
            return []
        
        # If terms agreed, show the carousel
        return [FollowupAction("action_show_carousel")]


class ActionShowCarouselMain(Action):
    def name(self) -> str:
        return "action_show_carousel"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        elements = [
            {
                "title": "Report Power Outage",
                "subtitle": "Report power interruptions in your area",
                "image_url": "https://i.postimg.cc/hP14f5Gz/Power-Outage.jpg",
                "buttons": [
                    {"type": "web_url", "title": "Report Power Interruption", "url": "http://127.0.0.1:5000/report_outage"},
                    {"type": "postback", "title": "Scheduled Power Outage", "payload": "/schedule_outage"},
                    {"type": "postback", "title": "Follow-Up Report", "payload": "/follow_up_report"}
                ]
            },
            {
                "title": "Billing & Payment",
                "subtitle": "Manage your billing and payment concerns",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Online Billing", "payload": "/online_billing"},
                    {"type": "postback", "title": "Payment Option", "payload": "/payment_option"}
                ]
            },
            {
                "title": "New Connection",
                "subtitle": "Apply for a new electric service connection",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Requirements", "payload": "/requirements_checklist"},
                    {"type": "postback", "title": "Schedule of PMOS", "payload": "/schedule_pmos"},
                    {"type": "postback", "title": "Application Forms", "payload": "/download_forms"}
                ]
            },
            {
                "title": "Technical Support",
                "subtitle": "Request meter and technical service assistance",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "web_url", "title": "Meter Concern", "url": "http://127.0.0.1:5000/meter_concern"},
                    {"type": "postback", "title": "Transfer of Meter", "payload": "/transfer_of_meter"},
                    {"type": "postback", "title": "Meter Follow-Up", "payload": "/meter_concern_followup"}
                ]
            },
            {
                "title": "Information",
                "subtitle": "Learn more about ILECO services",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Contact Information", "payload": "/contact_information"},
                    {"type": "postback", "title": "Rates", "payload": "/rates"},
                    {"type": "postback", "title": "Office Location", "payload": "/office_location"}
                ]
            },
            {
                "title": "Chat with Agent",
                "subtitle": "Get assistance from a customer service representative",
                "image_url": "https://i.postimg.cc/02qJQ0F6/agentwew.jpg",
                "buttons": [
                    {"type": "postback", "title": "Talk to Agent", "payload": "/talk_to_agent"}
                ]
            }
        ]

        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }

        dispatcher.utter_message(json_message=message)
        return []



class ActionAcceptTerms(Action):
    """Set terms_agreed slot when user clicks 'I Agree'"""
    def name(self) -> str:
        return "action_accept_terms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        # Just set the slot - let the rule handle the rest
        return [SlotSet("terms_agreed", True)]

class ActionValidateTermsAccess(Action):
    """Generic action to validate terms before accessing any feature"""
    def name(self) -> str:
        return "action_validate_terms_access"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            dispatcher.utter_message(
                text=(
                    "⚠️ **Access Denied**\n\n"
                    "You must accept our Terms of Use and Privacy Policy before using this service.\n\n"
                    "Please click 'I Agree' below to continue."
                ),
                buttons=[
                    {
                        "title": "I Agree",
                        "payload": "/accept_terms"
                    }
                ]
            )
            return [SlotSet("terms_agreed", False)]
        
        return []


class ActionSessionStart(Action):
    def name(self) -> str:
        return "action_session_start"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        # ❗ DO NOT touch slots here
        # ❗ DO NOT send messages here

        return [
            SessionStarted(),
            ActionExecuted("action_listen"),
        ]


class ActionSubmitPowerOutageFormEnhanced(Action):
    def name(self) -> Text:
        return "action_submit_power_outage_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Get data from slots
        full_name = tracker.get_slot("po_full_name")
        address = tracker.get_slot("po_address")
        contact_number = tracker.get_slot("po_contact_number")
        user_id = tracker.sender_id

        try:
            conn = psycopg2.connect(
                host="localhost",
                database="rasa_db",
                user="postgres",
                password="5227728"
            )
            cursor = conn.cursor()

            # Check for existing report today
            cursor.execute("""
                SELECT job_order_id, timestamp, status
                FROM power_outage_reports
                WHERE address = %s AND timestamp::date = CURRENT_DATE
                ORDER BY timestamp DESC
                LIMIT 1
            """, (address,))
            existing = cursor.fetchone()

            if existing and existing[2] not in ['RESOLVED', 'FINISHED']:
                job_order_id = existing[0]
                message = (
                    f"⚠️ Hello {full_name}, your outage was already reported today.\n"
                    f"🧾 *Job Order ID:* `{job_order_id}`\n"
                    f"✅ Our team is already working on it."
                )
                
            else:
                job_order_id = f"JO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                # Insert new report with correct field names
                cursor.execute("""
                    INSERT INTO power_outage_reports (
                        user_id, 
                        full_name, 
                        address, 
                        contact_number, 
                        job_order_id, 
                        issue_type, 
                        priority, 
                        status, 
                        source, 
                        timestamp,
                        description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, 
                    full_name, 
                    address, 
                    contact_number, 
                    "POWER OUTAGE",  # Match dashboard filter
                    "HIGH", 
                    "NEW",  # Match dashboard status options
                    "Chatbot", 
                    datetime.now(),
                    f"Power outage reported at {address}"
                ))

                message = (
                    f"✅ Thank you {full_name}! Your outage report has been logged.\n"
                    f"📍 *Location:* {address}\n"
                    f"📱 *Contact:* {contact_number}\n"
                    f"Our crew is on the way to check and determine the cause of the power outage. Thank you for your patience."
                )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            dispatcher.utter_message(text=f"❌ Error saving report: {str(e)}")
            print(f"Database error: {str(e)}")  # Debug logging
            return []

        dispatcher.utter_message(text=message)

        return [
            SlotSet("po_full_name", None),
            SlotSet("po_address", None),
            SlotSet("po_contact_number", None),
        ]

class ValidatePowerOutageForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_power_outage_form"

    def validate_po_full_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        name = slot_value.strip()
        # Require at least two words (e.g., "Juan Dela Cruz")
        if len(name.split()) >= 2 and all(part.isalpha() or part == '.' for part in name.replace(" ", "")):
            return {"po_full_name": name}
        else:
            dispatcher.utter_message(text="❌ Please enter a valid full name (e.g., Juan Dela Cruz).")
            return {"po_full_name": None}

    def validate_po_address(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        address = slot_value.strip().lower()

        # ✅ Allowed towns list
        allowed_towns = [
            "tubungan", "alimodian", "cabatuan", "guimbal", "igbaras",
            "leganes", "leon", "miag-ao", "miagao",  # both variations
            "oton", "pavia", "san joaquin", "san miguel", "sta. barbara", "sta barbara",
            "tigbauan"
        ]

        # ✅ Validation rules
        has_keywords = any(kw in address for kw in ["brgy", "purok", "street", "city", "blk"])
        contains_allowed_town = any(town in address for town in allowed_towns)

        if len(address) >= 10 and has_keywords and contains_allowed_town:
            return {"po_address": slot_value.strip()}
        else:
            dispatcher.utter_message(
                text="❌ Please provide a more detailed address with your barangay and town "
                     "(e.g., Brgy. Bacan, Cabatuan, Iloilo)."
            )
            return {"po_address": None}

    def validate_po_contact_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        # Accept only 11-digit numbers starting with 09
        if re.fullmatch(r"09\d{9}", slot_value):
            return {"po_contact_number": slot_value}
        else:
            dispatcher.utter_message(
                text=(
                    "❌ The contact number is invalid.\n"
                    "📌 It must be an 11-digit number starting with *09*.\n"
                    "🔄 Example: *09123456789*"
                )
            )
            return {"po_contact_number": None}
        
class ActionSubmitFollowUpReportForm(Action):

    def name(self) -> Text:
        return "action_submit_follow_up_report_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        fr_town = tracker.get_slot("fr_town")
        fr_barangay = tracker.get_slot("fr_barangay")

        if not fr_town or not fr_barangay:
            dispatcher.utter_message(
                text="❗ Please provide both your Town and Barangay."
            )
            return [
                SlotSet("fr_town", None),
                SlotSet("fr_barangay", None)
            ]

        try:
            # Connect to database
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # ✅ FIX: Normalize town and barangay for comparison
            normalized_town = fr_town.strip().lower()
            normalized_barangay = fr_barangay.strip().lower()

            # Fetch latest outage for the location
            cursor.execute("""
                SELECT 
                    incident_id,
                    town,
                    barangay,
                    incident_type,
                    status,
                    priority,
                    report_count,
                    first_report_time,
                    last_report_time,
                    remarks
                FROM outage_incidents
                WHERE LOWER(TRIM(town)) = %s
                  AND LOWER(TRIM(barangay)) = %s
                ORDER BY first_report_time DESC
                LIMIT 1
            """, (normalized_town, normalized_barangay))

            incident = cursor.fetchone()
            cursor.close()
            conn.close()

            if incident:
                (
                    incident_id,
                    town,
                    barangay,
                    incident_type,
                    status,
                    priority,
                    report_count,
                    first_report_time,
                    last_report_time,
                    remarks
                ) = incident

                incident_display = incident_type.replace("_", " ").title() if incident_type else "Power Outage"
                time_str = first_report_time.strftime('%b %d, %Y %I:%M %p') if first_report_time else "Unknown"
                status_upper = status.upper() if status else "NEW"

                # Compose message based on status
                if status_upper == "NEW":
                    message = (
                        f"⚠️ *Power Outage Reported*\n\n"
                        f"A power outage has been reported in *{town.title()} / {barangay.title()}*.\n"
                        f"• Type: {incident_display}\n"
                        f"• Priority: {priority}\n"
                        f"• Affected Reports: {report_count}\n"
                        f"• First Reported: {time_str}\n"
                    )
                    if remarks and remarks.strip():
                        message += f"\n💬 Update: {remarks}\n"

                    message += "\n✅ Our operations team is aware and a crew will be assigned shortly. Thank you for your patience. 🙏"

                elif status_upper == "ASSIGNED":
                    message = (
                        f"🚧 *Crew Dispatched*\n\n"
                        f"A repair crew has been dispatched to *{town.title()} / {barangay.title()}*.\n"
                        f"• Type: {incident_display}\n"
                        f"• Priority: {priority}\n"
                        f"• Affected Reports: {report_count}\n"
                        f"• First Reported: {time_str}\n"
                    )
                    if remarks and remarks.strip():
                        message += f"\n💬 Update: {remarks}\n"

                    message += "\n✅ The crew is on the way to restore power as soon as possible. Thank you for your patience. 🙏"

                elif status_upper == "RESTORED":
                    message = (
                        f"✅ *Power Restored*\n\n"
                        f"Good news! Power has been restored in *{town.title()} / {barangay.title()}*.\n\n"
                        "If you are still experiencing issues, please contact our hotline or click the Report Power Outage button.\n\n"
                        "📞 Hotline: 09989893028\n"
                        "💬 Chat: Click 'Report Power Outage' to submit a new report."
                    )

                else:
                    message = (
                        f"📊 *Outage Status Update*\n\n"
                        f"*Location:* {town.title()} / {barangay.title()}\n"
                        f"*Status:* {status}\n"
                        f"*Type:* {incident_display}\n"
                        f"*Priority:* {priority}\n"
                        f"*Affected Reports:* {report_count}\n"
                        f"*First Reported:* {time_str}\n\n"
                        "Thank you for your patience. 🙏"
                    )

            else:
                message = (
                    f"✅ *No Active Outages*\n\n"
                    f"There are currently no active power outage reports in *{fr_town.title()} / {fr_barangay.title()}*.\n\n"
                    "💡 Possible reasons:\n"
                    "• Scheduled maintenance\n"
                    "• Localized issue\n"
                    "• Power already restored\n\n"
                    "📞 Hotline: 09989893028\n"
                    "💬 Chat: Click 'Report Power Outage' to submit a new report."
                )

        except Exception as e:
            message = (
                f"❌ *System Error*\n\n"
                f"Unable to check outage status for *{fr_town.title()} / {fr_barangay.title()}*.\n"
                "Please try again later.\n\n"
                "📞 Hotline: 09989893028"
            )
            print(f"Error in follow-up action: {e}")
            import traceback
            traceback.print_exc()

        dispatcher.utter_message(text=message)

        # Reset slots after reporting
        return [
            SlotSet("fr_town", None),
            SlotSet("fr_barangay", None)
        ]

class ValidateFollowUpReportForm(FormValidationAction):
    """Validates the follow-up report form slots with flexible barangay matching"""
    
    def name(self) -> Text:
        return "validate_follow_up_report_form"
    
    # ✅ VALID TOWNS (lowercase for comparison)
    VALID_TOWNS = [
        "tubungan", "alimodian", "cabatuan", "guimbal", "igbaras",
        "leganes", "leon", "miag-ao", "miagao", "oton", "pavia",
        "san joaquin", "san miguel", "sta. barbara", "sta barbara",
        "tigbauan", "maasin"
    ]
    
    # ✅ TOWN ALIASES (handle different spellings)
    TOWN_ALIASES = {
        "miag-ao": "miagao",
        "sta barbara": "sta. barbara",
    }
    
    # ✅ VALID BARANGAYS BY TOWN (all lowercase for flexible matching)
    VALID_BARANGAYS = {
        "cabatuan": [
            "acao", "amerang", "amurao", "anuang", "ayaman", "ayong", "bacan", 
            "balabag", "baluyan", "banguit", "bulay", "cadoldolan", "cagban", 
            "calawagan", "calayo", "duyan-duyan", "gaub", "gines interior", 
            "gines patag", "guibuangan tigbauan", "inabasan", "inaca", "inaladan",
            "ingas", "ito norte", "ito sur", "janipaan central", "janipaan este", 
            "janipaan oeste", "janipaan olo", "jelicuon lusaya", "jelicuon montinola",
            "lag-an", "leong", "lutac", "manguna", "maraguit", "morubuan", 
            "pacatin", "pagotpot", "pamul-ogan", "pamuringao proper", 
            "pamuringao garrido", "pungtod", "puyas", "salacay", "sulanga",
            "tabucan", "tacdangan", "talanghauan", "tigbauan road", "tinio-an", 
            "tiring", "tupol central", "tupol este", "tupol oeste", "tuy-an",
            "zone i pob. (barangay 1)", "zone ii pob. (barangay 2)", 
            "zone iii pob. (barangay 3)", "zone iv pob. (barangay 4)", 
            "zone v pob. (barangay 5)", "zone vi pob. (barangay 6)",
            "zone vii pob. (barangay 7)", "zone viii pob. (barangay 8)",
            "zone ix pob. (barangay 9)", "zone x pob. (barangay 10)",
            "zone xi pob. (barangay 11)",
            # Aliases for zones
            "barangay 1", "barangay 2", "barangay 3", "barangay 4", "barangay 5",
            "barangay 6", "barangay 7", "barangay 8", "barangay 9", "barangay 10",
            "barangay 11", "zone 1", "zone 2", "zone 3", "zone 4", "zone 5",
            "zone 6", "zone 7", "zone 8", "zone 9", "zone 10", "zone 11",
            "poblacion"
        ],
        "alimodian": [
            "abang-abang", "agsing", "atabay", "ba-ong", "baguingin-lanot",
            "bagsakan", "bagumbayan-ilajas", "balabago", "ban-ag", "bancal",
            "binalud", "bugang", "buhay", "bulod", "cabacanan proper",
            "cabacanan rizal", "cagay", "coline", "coline-dalag", "cunsad",
            "cuyad", "dalid", "dao", "gines", "ginomoy", "ingwan", "laylayan",
            "lico", "luan-luan", "malamboy-bondolan", "malamhay", "mambawi",
            "manasa", "manduyog", "pajo", "pianda-an norte", "pianda-an sur",
            "poblacion", "punong", "quinaspan", "sinamay", "sulong",
            "taban-manguining", "tabug", "tarug", "tugaslon", "ubodan", "ugbo",
            "ulay-bugang", "ulay-hinablan", "umingan"
        ],
        "maasin": [
            "abay", "abilay", "agrocel pob.", "agrocel", "amerang", "bagacay east",
            "bagacay west", "bug-ot", "bolo", "bulay", "buntalan", "burak",
            "cabangcalan", "cabatac", "caigon", "cananghan", "canawili",
            "dagami", "daja", "dalusan", "delcar pob.", "delcar", "inabasan", "layog",
            "liñagan calsada", "liñagan tacas", "linagan calsada", "linagan tacas", "linab", "mari pob.", "mari",
            "magsaysay", "mandog", "miapa", "nagba", "nasaka", "naslo-bucao", "naslo bucao",
            "nasuli", "panalian", "piandaan east", "piandaan west", "pispis",
            "punong", "sinubsuban", "siwalo", "santa rita", "subog", "thtp pob.", "thtp",
            "tigbauan", "trangka", "tubang", "tulahong", "tuy-an east", "tuyan east",
            "tuy-an west", "tuyan west", "ubian",
            "poblacion"
        ],
        "sta. barbara": [
            "agusipan", "agutayan", "bagumbayan", "balabag", "balibagan este",
            "balibagan oeste", "ban-ag", "bantay", "barangay zone i (poblacion)",
            "barangay zone ii (poblacion)", "barangay zone iii (poblacion)",
            "barangay zone iv (poblacion)", "barangay zone v (poblacion)",
            "barangay zone vi (poblacion)", "barasan este", "barasan oeste",
            "binangkilan", "bitaog-taytay", "bitaog taytay", "bolong este", "bolong oeste",
            "buayahon", "buyo", "cabugao norte", "cabugao sur",
            "cadagmayan norte", "cadagmayan sur", "cafe", "calaboa este",
            "calaboa oeste", "camambugan", "canipayan", "conaynay", "daga",
            "dalid", "duyanduyan", "gen. martin t. delgado", "gen martin t delgado", "guno",
            "inangayan", "jibao-an", "jibao an", "lacadon", "lanag", "lupa", "magancina",
            "malawog", "mambuyo", "manhayang", "miraga-guibuangan", "miraga guibuangan", "nasugban",
            "omambog", "pal-agon", "pal agon", "pungsod", "san sebastian", "sangcate",
            "tagsing", "talanghauan", "talongadian", "tigtig", "tungay",
            "tuburan", "tugas",
            "zone 1", "zone 2", "zone 3", "zone 4", "zone 5", "zone 6",
            "poblacion"
        ],
        "leganes": [
            "m.v. hechanova (balabago)", "mv hechanova", "balabago", "bigke", "buntatala", "cagamutan norte",
            "cagamutan sur", "calaboa", "camangay", "cari mayor", "cari minor",
            "gua-an", "gua an", "guihaman", "guinobatan", "guintas", "lapayon",
            "nabitasan", "napnud", "poblacion", "san vicente"
        ],
        "pavia": [
            "aganan", "amparo", "anilao", "balabag", "purok i (poblacion)",
            "purok ii (poblacion)", "purok iii (poblacion)", "purok iv (poblacion)",
            "cabugao norte", "cabugao sur", "jibao-an", "jibao an", "mali-ao", "mali ao",
            "pagsanga-an", "pagsanga an", "pal-agon", "pal agon", "pandac", "tigum", "ungka i", "ungka ii",
            "purok 1", "purok 2", "purok 3", "purok 4", "poblacion"
        ],
        "oton": [
            "abilay norte", "abilay sur", "alegre", "batuan ilaud",
            "batuan ilaya", "bita norte", "bita sur", "botong", "buray",
            "cabanbanan", "cabolo-an norte", "cabolo-an sur", "cabolo an norte", "cabolo an sur", "cadinglian",
            "cagbang", "calam-isan", "calam isan", "galang", "lambuyao", "mambog", "pakiad",
            "poblacion east", "poblacion north", "poblacion south",
            "poblacion west", "pulo maestra vita", "rizal", "salngan",
            "sambaludan", "san antonio", "san nicolas", "santa clara",
            "santa monica", "santa rita", "tagbac norte", "tagbac sur",
            "trapiche", "tuburan", "turog-turog", "turog turog",
            "poblacion"
        ],
        "tigbauan": [
            "alupidian", "atabayan", "bagacay", "baguingin", "bagumbayan",
            "bangkal", "bantud", "barangay 1 (pob.)", "barangay 2 (pob.)",
            "barangay 3 (pob.)", "barangay 4 (pob.)", "barangay 5 (pob.)",
            "barangay 6 (pob.)", "barangay 7 (pob.)", "barangay 8 (pob.)",
            "barangay 9 (pob.)", "barosong", "barroc", "bayuco",
            "binaliuan mayor", "binaliuan menor", "bitas", "buenavista",
            "bugasongan", "buyu-an", "buyu an", "canabuan", "cansilayan", "cordova norte",
            "cordova sur", "danao", "dapdap", "dorong-an", "dorong an", "guisian", "isawan",
            "isian", "jamog", "lanag", "linobayan", "lubog", "nagba", "namocon",
            "napnapan norte", "napnapan sur", "olo barroc", "parara norte",
            "parara sur", "san rafael", "sermon", "sipitan", "supa", "tan pael",
            "taro",
            "barangay 1", "barangay 2", "barangay 3", "barangay 4", "barangay 5",
            "barangay 6", "barangay 7", "barangay 8", "barangay 9", "poblacion", "pob"
        ],
        "guimbal": [
            "anono-o", "anono o", "bacong", "bagumbayan poblacion", "balantad-carlos fruto", "balantad carlos fruto",
            "baras", "binanua-an", "binanua an", "bongol san miguel", "bongol san vicente",
            "bulad", "buluangan", "burgos-gengos", "burgos gengos", "cabasi", "cabubugan",
            "calampitao", "camangahan", "generosa-cristobal colon", "generosa cristobal colon",
            "gerona-gimeno", "gerona gimeno", "girado-magsaysay", "girado magsaysay", "gotera", "igcocolo", "iyasan",
            "libo-on gonzales", "libo on gonzales", "lubacan", "nahapay", "nalundan", "nanga",
            "nito-an lupsag", "nito an lupsag", "particion", "pescadores", "rizal-tuguisan", "rizal tuguisan",
            "sipitan-badiang", "sipitan badiang", "santa rosa-laguna", "santa rosa laguna", "torreblanca-blumentritt", "torreblanca blumentritt",
            "poblacion"
        ],
        "igbaras": [
            "alameda", "amorogtong", "anilawan", "bagacay", "bagacayan",
            "bagay", "balibagan", "barangay 1 poblacion", "barangay 2 poblacion",
            "barangay 3 poblacion", "barangay 4 poblacion", "barangay 5 poblacion",
            "barangay 6 poblacion", "barasan", "binanua-an", "binanua an", "boclod",
            "buenavista", "buga", "bugnay", "calampitao", "cale", "corucuan",
            "catiringan", "igcabugao", "igpigus", "igtalongon", "indaluyon",
            "jovellar", "kinagdan", "lab-on", "lab on", "lacay dol-dol", "lacay dol dol", "lumangan",
            "lutungan", "mantangon", "mulangan", "pasong", "passi",
            "pinaopawan", "riro-an", "riro an", "san ambrosio", "santa barbara", "signe",
            "tabiac", "talayatay", "taytay", "tigbanaba",
            "barangay 1", "barangay 2", "barangay 3", "barangay 4", "barangay 5",
            "barangay 6", "poblacion"
        ],
        "san joaquin": [
            "amboyu-an", "amboyu an", "andres bonifacio", "antalon", "bad-as", "bad as", "bagumbayan",
            "balabago", "baybay", "bayunan (panday oro)", "bayunan", "panday oro", "bolbogan", "bulho",
            "bucaya", "cadluman", "cadoldolan", "camia", "camaba-an", "camaba an", "cata-an", "cata an",
            "crossing dapuyan", "cubay", "cumarascas", "dacdacanan", "danawan",
            "doldol", "dongoc", "escalantera", "ginot-an", "ginot an", "guibongan bayunan",
            "huna", "igbaje", "igbangcal", "igbinangon", "igburi", "igcabutong",
            "igcadlum", "igcaphang", "igcaratong", "igcondao", "igcores",
            "igdagmay", "igdomingding", "iglilico", "igpayong", "jawod",
            "langca", "languanan", "lawigan", "lomboy", "lomboyan (santa ana)", "lomboyan", "santa ana",
            "lopez vito", "mabini norte", "mabini sur", "manhara", "maninila",
            "masagud", "matambog", "mayunoc", "montinola", "nagquirisan",
            "nadsadan", "nagsipit", "new gumawan", "panatan", "pitogo",
            "purok 1 (poblacion)", "purok 2 (poblacion)", "purok 3 (poblacion)",
            "purok 4 (poblacion)", "purok 5 (poblacion)", "qui-anan", "qui anan", "roma",
            "san luis", "san mateo norte", "san mateo sur", "santa rita",
            "santiago", "sinogbuhan", "siwaragan", "talagutac", "tapikan",
            "taslan", "tiglawa", "tiolas", "to-og", "to og", "torocadan", "ulay",
            "purok 1", "purok 2", "purok 3", "purok 4", "purok 5", "poblacion"
        ],
        "tubungan": [
            "adgao", "ago", "ambarihon", "ayubo", "bacan", "badiang",
            "bagunanay", "balicua", "bantayanan", "batga", "bato", "bikil",
            "boloc", "bondoc", "borong", "buenavista", "cadabdab", "daga-ay", "daga ay",
            "desposorio", "igdampog norte", "igdampog sur", "igpaho", "igtuble",
            "ingay", "isauan", "jolason", "jona", "la-ag", "la ag", "lanag norte",
            "lanag sur", "male", "mayang", "molina", "morcillas", "nagba",
            "navillan", "pinamacalan", "san jose", "sibucauan", "singon",
            "tabat", "tagpu-an", "tagpu an", "talento", "teniente benito", "victoria",
            "zone i pob.", "zone ii pob.", "zone iii pob.",
            "zone 1", "zone 2", "zone 3", "poblacion"
        ],
        "san miguel": [
            "barangay 1 poblacion", "barangay 2 poblacion", "barangay 3 poblacion",
            "barangay 4 poblacion", "barangay 5 poblacion", "barangay 6 poblacion",
            "barangay 7 poblacion", "barangay 8 poblacion", "barangay 9 poblacion",
            "barangay 10 poblacion", "barangay 11 poblacion", "barangay 12 poblacion",
            "barangay 13 poblacion", "barangay 14 poblacion", "barangay 15 poblacion",
            "barangay 16 poblacion", "consolacion", "igtambo", "san antonio",
            "san jose", "santa cruz", "santa teresa", "santo angel", "santo niño", "santo nino",
            "barangay 1", "barangay 2", "barangay 3", "barangay 4", "barangay 5",
            "barangay 6", "barangay 7", "barangay 8", "barangay 9", "barangay 10",
            "barangay 11", "barangay 12", "barangay 13", "barangay 14", "barangay 15",
            "barangay 16", "poblacion"
        ],
        "leon": [
            "agboy norte", "agboy sur", "agta", "ambulong", "anonang", "apian",
            "avanzada", "awis", "ayabang", "ayubo", "bacolod", "baje", "banagan",
            "barangbang", "barasan", "bayag norte", "bayag sur", "binolbog",
            "biri norte", "biri sur", "bobon", "bucari", "buenavista", "buga",
            "bulad", "bulwang", "cabolo-an", "cabolo an", "cabunga-an", "cabunga an", "cabutongan", "cagay",
            "camandag", "camando", "cananaman", "capt. fernando", "capt fernando", "carara-an", "carara an",
            "carolina", "cawilihan", "coyugan norte", "coyugan sur", "danao",
            "dorog", "dusacan", "gines", "gumboc", "igcadios", "ingay",
            "isian norte", "isian victoria", "jamog gines", "lanag", "lang-og", "lang og",
            "ligtos", "lonoc", "lampaya", "magcapay", "maliao", "malublub",
            "manampunay", "marirong", "mina", "mocol", "nagbangi", "nalbang",
            "odong-odong", "odong odong", "oluangan", "omambong", "paoy", "pandan", "panginman",
            "pepe", "poblacion", "paga", "salngan", "samlague", "siol norte",
            "siol sur", "tacuyong norte", "tacuyong sur", "tagsing", "talacuan",
            "ticuan", "tina-an norte", "tina-an sur", "tina an norte", "tina an sur", "tunguan", "tu-og", "tu og"
        ],
        "miagao": [
            "agdum", "aguiauan", "alimodias", "awang", "oya-oy", "oya oy", "bacauan",
            "bacolod", "bagumbayan", "banbanan", "banga", "bangladan", "banuyao",
            "baraclayan", "bariri", "baybay norte (poblacion)",
            "baybay sur (poblacion)", "belen", "bolho (poblacion)", "bolocaue",
            "buenavista norte", "buenavista sur", "bugtong lumangan",
            "bugtong naulid", "cabalaunan", "cabangcalan", "cabunotan",
            "cadoldolan", "cagbang", "caitib", "calagtangan", "calampitao",
            "cavite", "cawayanan", "cubay", "cubay ubos", "dalije", "damilisan",
            "dawog", "diday", "dingle", "durog", "frantilla", "fundacion",
            "gines", "guibongan", "igbita", "igbugo", "igcabidio", "igcabito-on", "igcabito on",
            "igcatambor", "igdalaquit", "igdulaca", "igpajo", "igpandan",
            "igpuro", "igpuro-bariri", "igpuro bariri", "igsoligue", "igtuba", "ilog-ilog", "ilog ilog",
            "indag-an", "indag an", "kirayan norte", "kirayan sur", "kirayan tacas",
            "la consolacion", "lacadon", "lanutan", "lumangan", "mabayan",
            "maduyo", "malagyan", "mambatad", "maninila", "maricolcol",
            "maringyan", "mat-y (poblacion)", "mat y", "matalngon", "naclub",
            "nam-o norte", "nam-o sur", "nam o norte", "nam o sur", "narat-an", "narat an", "narorogan", "naulid",
            "olango", "ongyod", "onop", "oyungan", "palaca", "paro-on", "paro on",
            "potrido", "pudpud", "pungtod monteclaro", "pungtod naulid",
            "sag-on", "sag on", "san fernando", "san jose", "san rafael", "sapa (miagao)", "sapa",
            "saring", "sibucao", "taal", "tabunacan", "tacas (poblacion)",
            "tambong", "tan-agan", "tan agan", "tatoy", "ticdalan", "tig-amaga", "tig amaga",
            "tig-apog-apog", "tig apog apog", "tigbagacay", "tiglawa", "tigmalapad", "tigmarabo",
            "to-og", "to og", "tugura-ao", "tugura ao", "tumagboc", "ubos ilawod (poblacion)",
            "ubos ilaya (poblacion)", "valencia", "wayang",
            "poblacion"
        ]
    }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for flexible matching"""
        if not text:
            return ""
        normalized = text.lower().strip()
        # Remove punctuation and normalize spaces
        normalized = normalized.replace(".", "").replace(",", "").replace("-", " ")
        normalized = normalized.replace("(", "").replace(")", "")
        normalized = " ".join(normalized.split())
        return normalized
    
    def find_closest_match(self, input_text: str, valid_list: list) -> tuple:
        """Find if input matches any item in valid_list"""
        normalized_input = self.normalize_text(input_text)
        
        for valid_item in valid_list:
            normalized_valid = self.normalize_text(valid_item)
            
            # Exact match
            if normalized_input == normalized_valid:
                return (True, valid_item)
            
            # Partial match (for zones/barangays)
            if normalized_input in normalized_valid or normalized_valid in normalized_input:
                return (True, valid_item)
        
        return (False, None)
    
    def validate_fr_town(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate town input"""
        
        if not slot_value or len(slot_value.strip()) < 2:
            dispatcher.utter_message(text=(
                "❗ *Invalid Town Name*\n\n"
                "Please provide a valid town/municipality name.\n\n"
                "📍 *ILECO-1 Service Area Towns:*\n"
                "• Tubungan • Alimodian • Cabatuan\n"
                "• Guimbal • Igbaras • Leganes\n"
                "• Leon • Miag-ao • Oton\n"
                "• Pavia • San Joaquin • San Miguel\n"
                "• Sta. Barbara • Tigbauan • Maasin\n\n"
                "🔄 *Example:* Type `Cabatuan` or `Leon`"
            ))
            return {"fr_town": None}
        
        # Normalize and check
        normalized_input = self.normalize_text(slot_value)
        
        # Check direct match
        if normalized_input in self.VALID_TOWNS:
            return {"fr_town": slot_value.strip().title()}
        
        # Check aliases
        if normalized_input in self.TOWN_ALIASES:
            canonical_town = self.TOWN_ALIASES[normalized_input]
            return {"fr_town": canonical_town.title()}
        
        # No match found
        dispatcher.utter_message(text=(
            f"❌ *'{slot_value}' is not in our service area.*\n\n"
            "📍 *ILECO-1 covers these towns only:*\n"
            "• Tubungan • Alimodian • Cabatuan\n"
            "• Guimbal • Igbaras • Leganes\n"
            "• Leon • Miag-ao • Oton\n"
            "• Pavia • San Joaquin • San Miguel\n"
            "• Sta. Barbara • Tigbauan • Maasin\n\n"
            "💡 *Tip:* Check your spelling.\n"
            "📞 *Need help?* Call: *09989893028*"
        ))
        return {"fr_town": None}
    
    def validate_fr_barangay(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate barangay input with flexible matching"""
        
        if not slot_value or len(slot_value.strip()) < 2:
            dispatcher.utter_message(text=(
                "❗ *Invalid Barangay Name*\n\n"
                "Please provide a complete barangay name.\n\n"
                "🔄 *Examples:*\n"
                "• `Bacan`\n"
                "• `Poblacion`\n"
                "• `Zone 1` or `Barangay 1`"
            ))
            return {"fr_barangay": None}
        
        # Get the previously validated town
        fr_town = tracker.get_slot("fr_town")
        
        if not fr_town:
            # Town not yet provided - accept barangay temporarily
            return {"fr_barangay": slot_value.strip().title()}
        
        # Normalize town name for lookup
        town_key = self.normalize_text(fr_town)
        
        # Handle town aliases
        if town_key in self.TOWN_ALIASES:
            town_key = self.TOWN_ALIASES[town_key]
        
        # Check if town exists in our database
        if town_key not in self.VALID_BARANGAYS:
            # Town not in our list but was validated earlier
            return {"fr_barangay": slot_value.strip().title()}
        
        # Get valid barangays for this town
        valid_barangays = self.VALID_BARANGAYS[town_key]
        
        # Try to find a match (flexible)
        is_valid, matched_barangay = self.find_closest_match(slot_value, valid_barangays)
        
        if is_valid:
            # Use the properly formatted version from database
            return {"fr_barangay": matched_barangay.title()}
        
        # No match found - show error with suggestions
        sample_barangays = [b.title() for b in valid_barangays[:5]]
        
        dispatcher.utter_message(text=(
            f"❌ *'{slot_value}' not found in {fr_town}*\n\n"
            f"💡 Please verify the correct barangay name.\n\n"
            f"🔍 *Some barangays in {fr_town}:*\n"
            f"• {sample_barangays[0]}\n"
            f"• {sample_barangays[1]}\n"
            f"• {sample_barangays[2]}\n"
            f"• {sample_barangays[3]}\n"
            f"• {sample_barangays[4] if len(sample_barangays) > 4 else '...'}\n\n"
            f"🔄 *Tip:* Check spelling or use official name.\n"
        ))
        return {"fr_barangay": None}



class ActionCheckTerms(Action):
    def name(self) -> Text:
        return "action_check_terms"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(
            text=(
                "⚠️ Before proceeding, please accept our "
                "Terms of Use and Privacy Policy."
            ),
            buttons=[
                {
                    "title": "I Agree",
                    "payload": "/accept_terms"
                }
            ]
        )
        return []


class ActionShowCarousel(Action):
    def name(self) -> str:
        return "action_show_carousel_extra"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        elements = [
            {
                "title": "Report of Power Outage",
                "subtitle": "Submit power outage reports and follow-ups",
                "image_url": "https://i.postimg.cc/hP14f5Gz/Power-Outage.jpg",
                "buttons": [
                    {"type": "web_url", "title": "Report Power Interruption", "url": "http://127.0.0.1:5000/report_outage"},
                    {"type": "postback", "title": "Schedule Power Outage", "payload": "/schedule_outage"},
                    {"type": "postback", "title": "Follow-Up Report", "payload": "/follow_up_report"}
                ]
            },
            {
                "title": "Billing & Payment Concerns",
                "subtitle": "Inquire about billing statements and payments",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Online Billing", "payload": "/online_billing"},
                    {"type": "postback", "title": "Payment Option", "payload": "/payment_option"}
                ]
            },
            {
                "title": "Application for New Connection",
                "subtitle": "View requirements and application schedules",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Requirements", "payload": "/requirements_checklist"},
                    {"type": "postback", "title": "Schedule of PMOS", "payload": "/schedule_pmos"},
                    {"type": "postback", "title": "Download Application Forms", "payload": "/download_forms"}
                ]
            },
            {
                "title": "Services / Technical Support",
                "subtitle": "Request meter services and technical support",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Meter Concern", "payload": "/meter_concern"},
                    {"type": "postback", "title": "Transfer of Meter", "payload": "/transfer_of_meter"},
                    {"type": "postback", "title": "Meter Follow-Up", "payload": "/meter_concern_followup"}
                ]
            },
            {
                "title": "General Information",
                "subtitle": "Access important information about our services",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Contact Information", "payload": "/contact_information"},
                    {"type": "postback", "title": "Rates", "payload": "/rates"},
                    {"type": "postback", "title": "Office Location", "payload": "/office_location"}
                ]
            },
            {
                "title": "Chat with Agent",
                "subtitle": "Connect with a live customer service representative",
                "image_url": "https://i.postimg.cc/02qJQ0F6/agentwew.jpg",
                "buttons": [
                    {"type": "postback", "title": "Talk to Agent", "payload": "/talk_to_agent"}
                ]
            }
        ]

        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }

        dispatcher.utter_message(
            text="📋 Please select an option below to continue your transaction:"
        )
        dispatcher.utter_message(json_message=message)

        return []



class ActionResumeConversation(Action):
    def name(self) -> Text:
        return "action_resume_conversation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        
        print(f"🔄 RESUME ACTION TRIGGERED for user: {sender_id}")

        try:
            connection = psycopg2.connect(
                host="localhost",
                database="rasa_db",
                user="postgres",
                password="5227728"
            )
            cursor = connection.cursor()

            # ✅ Remove user from queue completely (any status)
            cursor.execute("""
                DELETE FROM agent_queue WHERE user_id = %s
            """, (sender_id,))
            
            deleted_count = cursor.rowcount
            print(f"✅ Removed {deleted_count} queue entries for user {sender_id}")

            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ RESUME ACTION COMPLETED for user: {sender_id}")

        except Exception as e:
            print(f"❌ Error resuming conversation for {sender_id}: {e}")
            import traceback
            traceback.print_exc()

        # ✅ CHECK IF USER HAS AGREED TO TERMS
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # ❌ User hasn't agreed to terms yet - show terms first
            print(f"⚠️ User {sender_id} has NOT agreed to terms yet")
            dispatcher.utter_message(text=(
                "✅ *Welcome back!*\n\n"
                "Thank you for your patience. Your concern has been addressed by our customer service agent.\n\n"
                "Before we continue, please accept our Terms of Use and Privacy Policy."
            ))
            dispatcher.utter_message(
                text="⚠️ Please accept our Terms of Use and Privacy Policy to continue.",
                buttons=[
                    {
                        "title": "I Agree",
                        "payload": "/accept_terms"
                    }
                ]
            )
            # ✅ CRITICAL: Return ConversationResumed WITHOUT FollowupAction
            return [ConversationResumed()]
        
        # ✅ User already agreed - show welcome + carousel
        print(f"✅ User {sender_id} already agreed to terms - showing carousel")
        dispatcher.utter_message(text=(
            "✅ *Welcome back!*\n\n"
            "Thank you for your patience. Your concern has been addressed by our customer service agent.\n\n"
            "Is there anything else I can help you with today?"
        ))
        
        # ✅ CRITICAL FIX: Call carousel action WITHIN this action, not as FollowupAction
        # This prevents Rasa from continuing to predict more actions
        from rasa_sdk.executor import CollectingDispatcher
        
        # Show carousel elements
        elements = [
            {
                "title": "Report Power Outage",
                "subtitle": "Report an issue",
                "image_url": "https://i.postimg.cc/hP14f5Gz/Power-Outage.jpg",
                "buttons": [
                    {"type": "web_url", "title": "Report Power Interruption", "url": "http://127.0.0.1:5000/report_outage"},
                    {"type": "postback", "title": "Scheduled Power Outage", "payload": "/schedule_outage"},
                    {"type": "postback", "title": "Follow-Up Report", "payload": "/follow_up_report"}
                ]
            },
            {
                "title": "Billing & Payment",
                "subtitle": "Manage your bill",     
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Online Billing", "payload": "/online_billing"},
                    {"type": "postback", "title": "Payment Opiton", "payload": "/payment_option"}
                ]
            },
            {
                "title": "New Connection",
                "subtitle": "Apply for service",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Requirements", "payload": "/requirements_checklist"},
                    {"type": "postback", "title": "Schedule ofPMOS", "payload": "/schedule_pmos"},
                    {"type": "postback", "title": "Application Forms", "payload": "/download_forms"}
                ]
            },
            {
                "title": "Technical Support",
                "subtitle": "Request service",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "web_url", "title": "Meter Concern", "url": "http://127.0.0.1:5000/meter_concern"},
                    {"type": "postback", "title": "Transfer of Meter", "payload": "/transfer_of_meter"},
                    {"type": "postback", "title": "Meter Follow-Up", "payload": "/meter_concern_followup"}
                ]
            },
            {
                "title": "Information",
                "subtitle": "Learn more",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {"type": "postback", "title": "Contact Information", "payload": "/contact_information"},
                    {"type": "postback", "title": "Rates", "payload": "/rates"},
                    {"type": "postback", "title": "Office Location", "payload": "/office_location"}
                ]
            },
            {
                "title": "Chat with Agent",
                "subtitle": "Get help from a live agent",
                "image_url": "https://i.postimg.cc/02qJQ0F6/agentwew.jpg",
                "buttons": [
                    {"type": "postback", "title": "Talk to Agent", "payload": "/talk_to_agent"}
                ]
            }
        ]

        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }

        dispatcher.utter_message(json_message=message)
        
        # ✅ CRITICAL: Return ONLY ConversationResumed - no FollowupAction!
        # This tells Rasa to WAIT for user input instead of predicting more actions
        return [ConversationResumed()]

class ActionSubmitTalkToAgentForm(Action):
    def name(self) -> Text:
        return "action_submit_talk_to_agent_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Get data from slots
        full_name = tracker.get_slot("tta_full_name")
        concern = tracker.get_slot("tta_concern")
        contact_number = tracker.get_slot("tta_contact_number")
        user_id = tracker.sender_id
        timestamp = datetime.now()

        # ✅ REMOVED: The active_loop check - loop is already deactivated at this point
        # Validate required fields instead
        if not full_name or not contact_number or not concern:
            dispatcher.utter_message(text=(
                "⚠️ *Incomplete Information Detected!*\n"
                "Please make sure you've provided your full name, concern, and contact number so we can assist you properly. 😊"
            ))
            return []

        # Get priority from concern
        priority = self.get_priority_from_concern(concern)

        try:
            connection = psycopg2.connect(
                host="localhost",
                database="rasa_db",
                user="postgres",
                password="5227728"
            )
            cursor = connection.cursor()

            # ✅ Check if user is already in queue
            cursor.execute("SELECT id FROM agent_queue WHERE user_id = %s AND status = 'Pending'", (user_id,))
            existing = cursor.fetchone()

            if existing:
                dispatcher.utter_message(text=(
                    "⚠️ *You're already in the queue!*\n"
                    "Please wait for an agent to assist you. 😊"
                ))
                cursor.close()
                connection.close()
                return []

            # ✅ Insert new user into queue with Pending status
            cursor.execute("""
                INSERT INTO agent_queue (user_id, full_name, concern, contact_number, priority, timestamp, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """, (user_id, full_name, concern, contact_number, priority, timestamp))

            # ✅ Get CURRENT queue position (counting only Pending users)
            cursor.execute("""
                SELECT COUNT(*) FROM agent_queue 
                WHERE status = 'Pending' AND timestamp <= %s
            """, (timestamp,))
            
            queue_position = cursor.fetchone()[0]

            connection.commit()
            cursor.close()
            connection.close()

            # ✨ Friendly messages
            dispatcher.utter_message(text=(
                f"✅ *Thank you, {full_name}!* Your concern has been successfully recorded. \n\n"
                f"📌 *Concern:* _{concern}_\n"
                f"📞 *Contact Number:* `{contact_number}`\n"
            ))

            dispatcher.utter_message(text=(
                f"🙏 We appreciate your patience.\n"
                f"You are currently *#{queue_position}* in the queue.\n"
                f"Please stay connected — one of our friendly agents will reach out shortly!"
            ))

            # ✅ Return slot resets and pause conversation
            return [
                SlotSet("tta_full_name", None),
                SlotSet("tta_concern", None),
                SlotSet("tta_contact_number", None),
                ConversationPaused()
            ]

        except Exception as e:
            dispatcher.utter_message(text=(
                "❌ *Oops! Something went wrong while processing your request.*\n"
                f"Error: {str(e)}\n\n"
                "Please try again in a few moments.\n\n"
                "_Our team is working to resolve this as soon as possible!_ 🙏"
            ))
            print(f"Error submitting to agent queue: {e}")
            import traceback
            traceback.print_exc()  # Print full error trace for debugging
            return []

    def get_priority_from_concern(self, concern: Text) -> Text:
        concern = (concern or "").lower()
        if any(word in concern for word in ["emergency", "fire", "fallen", "accident", "hazard"]):
            return "critical"
        elif any(word in concern for word in ["no electricity", "power outage", "blackout"]):
            return "high"
        elif any(word in concern for word in ["billing", "bill", "payment", "follow-up", "follow up"]):
            return "medium"
        elif any(word in concern for word in ["transfer", "new connection", "installation", "application"]):
            return "low"
        else:
            return "low"
class ActionServeNextUser(Action):
    def name(self) -> Text:
        return "action_serve_next_user"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        try:
            connection = psycopg2.connect(
                host="localhost",
                database="rasa_db",
                user="postgres",
                password="5227728"
            )
            cursor = connection.cursor()

            # ✅ Get the first Pending user
            cursor.execute("""
                SELECT id, user_id, full_name 
                FROM agent_queue 
                WHERE status = 'Pending' 
                ORDER BY timestamp ASC 
                LIMIT 1
            """)
            first_user = cursor.fetchone()

            if not first_user:
                dispatcher.utter_message(text="🎉 No more users in the queue.")
                return []

            record_id, user_id, full_name = first_user

            # ✅ Mark them as Resolved instead of deleting
            cursor.execute("UPDATE agent_queue SET status = 'Resolved' WHERE id = %s", (record_id,))
            connection.commit()

            dispatcher.utter_message(text=f"👤 *{full_name}* has now been served and removed from the queue.")

            cursor.close()
            connection.close()
            return []

        except Exception as e:
            dispatcher.utter_message(text="❌ Failed to serve next user.")
            print(f"Error in ActionServeNextUser: {e}")
            return []

class ActionTestDB(Action):
    def name(self) -> Text:
        return "action_test_db"
    
    def run(self, dispatcher, tracker, domain):
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="rasa_db",
                user="postgres",
                password="5227728"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            dispatcher.utter_message(text=f"✅ DB Connection OK: {result}")
        except Exception as e:
            dispatcher.utter_message(text=f"❌ DB Error: {str(e)}")
        return []
    
class ValidateTalkToAgentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_talk_to_agent_form"

    def validate_tta_full_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        full_name = slot_value.strip()
        if len(full_name.split()) >= 2 and all(part.isalpha() or part == '.' for part in full_name.replace(" ", "")):
            return {"tta_full_name": full_name}
        else:
            dispatcher.utter_message(text="❌ Please enter a valid full name (e.g., Juan Dela Cruz).")
            return {"tta_full_name": None}

    def validate_tta_contact_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        if re.fullmatch(r"09\d{9}", slot_value):
            return {"tta_contact_number": slot_value}
        else:
            dispatcher.utter_message(
                text="❌ Invalid contact number.\n📌 It must start with *09* and be 11 digits.\n🔄 Example: *09123456789*"
            )
            return {"tta_contact_number": None}

    def validate_tta_concern(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        concern_map = {
            "1": "no electricity",
            "2": "emergency",
            "3": "billing issue",
            "4": "new connection",
            "5": "follow-up",
            "6": "transfer or disconnection",
            "7": "others"
        }

        value = slot_value.strip().lower()
        mapped = concern_map.get(value)

        if mapped:
            return {"tta_concern": mapped}
        elif len(value) >= 5:
            return {"tta_concern": value}
        else:
            dispatcher.utter_message(
                text="❌ Please describe your concern in more detail (e.g., 'No electricity', 'Billing issue')."
            )
            return {"tta_concern": None}


class ActionDefaultFallback(Action):
    """Handle fallback when bot doesn't understand"""
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # User hasn't accepted terms - show terms
            dispatcher.utter_message(response="utter_greet")
        else:
            # User accepted terms - show helpful message
            dispatcher.utter_message(
                text="🤔 I didn't quite understand that.\n\n"
                     "Please choose an option from the menu or type 'menu' to see all options."
            )
        
        # ✅ IMPORTANT: Return UserUtteranceReverted to stop the loop
        from rasa_sdk.events import UserUtteranceReverted
        return [UserUtteranceReverted()]

class ActionSubmitMeterConcernFollowUp(Action):
    """Follow-up on meter concern using reference number"""
    
    def name(self) -> Text:
        return "action_submit_meter_concern_followup"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        ref_number = tracker.get_slot("mc_reference_number")

        if not ref_number or len(ref_number.strip()) < 5:
            dispatcher.utter_message(
                text="❗ Please provide a valid reference number (e.g., MC-20260123-EA3B68AB)."
            )
            return [SlotSet("mc_reference_number", None)]

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Fetch meter concern by reference number
            cursor.execute("""
                SELECT 
                    reference_number,
                    consumer_name,
                    account_number,
                    barangay,
                    concern_type,
                    status,
                    priority,
                    created_at,
                    updated_at,
                    additional_details,
                    is_critical
                FROM meter_concerns
                WHERE reference_number = %s
                LIMIT 1
            """, (ref_number.strip(),))

            concern = cursor.fetchone()
            cursor.close()
            conn.close()

            if concern:
                (
                    ref_num,
                    consumer_name,
                    account_number,
                    barangay,
                    concern_type,
                    status,
                    priority,
                    created_at,
                    updated_at,
                    details,
                    is_critical
                ) = concern

                # Map concern types to friendly names
                concern_type_map = {
                    'not_working': 'Meter Not Working / Blank Display',
                    'high_consumption': 'High Consumption / High Bill',
                    'running_fast_slow': 'Meter Running Fast / Slow',
                    'noise_burning': 'Noise or Burning Smell ⚠️',
                    'tampered_seal': 'Tampered / Broken Seal',
                    'others': 'Others'
                }

                concern_display = concern_type_map.get(concern_type, concern_type)
                created_str = created_at.strftime('%b %d, %Y %I:%M %p') if created_at else "Unknown"
                status_upper = status.upper() if status else "PENDING"

                # Compose response based on status
                if status_upper == "PENDING":
                    message = (
                        f"📋 *Meter Concern Status*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"📍 Location: {barangay}\n"
                        f"⚠️ Type: {concern_display}\n"
                        f"🔥 Priority: {priority.upper()}\n"
                        f"📅 Reported: {created_str}\n\n"
                        f"⏳ *Status: PENDING*\n"
                        f"Your concern has been received and is awaiting assignment to our technical team.\n\n"
                        f"✅ We'll notify you once a technician has been assigned. Thank you for your patience! 🙏"
                    )

                elif status_upper == "ASSIGNED":
                    message = (
                        f"📋 *Meter Concern Status*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"📍 Location: {barangay}\n"
                        f"⚠️ Type: {concern_display}\n"
                        f"🔥 Priority: {priority.upper()}\n"
                        f"📅 Reported: {created_str}\n\n"
                        f"🔧 *Status: ASSIGNED*\n"
                        f"A technician has been assigned to your case and will visit your location soon.\n\n"
                        f"✅ Thank you for your patience! 🙏"
                    )

                elif status_upper == "IN_PROGRESS":
                    message = (
                        f"📋 *Meter Concern Status*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"📍 Location: {barangay}\n"
                        f"⚠️ Type: {concern_display}\n"
                        f"🔥 Priority: {priority.upper()}\n"
                        f"📅 Reported: {created_str}\n\n"
                        f"🚧 *Status: IN PROGRESS*\n"
                        f"Our technician is currently working on resolving your meter concern.\n\n"
                        f"✅ We'll update you once completed. Thank you! 🙏"
                    )

                elif status_upper == "RESOLVED":
                    # Use updated_at as resolved time if available
                    resolved_str = updated_at.strftime('%b %d, %Y %I:%M %p') if updated_at else "Recently"
                    message = (
                        f"✅ *Meter Concern RESOLVED*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"📍 Location: {barangay}\n"
                        f"⚠️ Type: {concern_display}\n"
                        f"📅 Reported: {created_str}\n"
                        f"✅ Resolved: {resolved_str}\n\n"
                        f"🎉 Good news! Your meter concern has been resolved.\n\n"
                        f"If you're still experiencing issues, please contact our hotline or submit a new report.\n\n"
                        f"📞 Hotline: 09989893028\n"
                        f"💬 Submit new report via the chatbot menu."
                    )

                elif status_upper == "CLOSED":
                    message = (
                        f"📋 *Meter Concern Status*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"⚠️ Type: {concern_display}\n\n"
                        f"📁 *Status: CLOSED*\n"
                        f"This concern has been closed.\n\n"
                        f"If you need further assistance, please submit a new report."
                    )

                else:
                    message = (
                        f"📋 *Meter Concern Details*\n\n"
                        f"🔖 Reference: `{ref_num}`\n"
                        f"👤 Consumer: {consumer_name}\n"
                        f"📍 Location: {barangay}\n"
                        f"⚠️ Type: {concern_display}\n"
                        f"📊 Status: {status}\n"
                        f"🔥 Priority: {priority.upper()}\n"
                        f"📅 Reported: {created_str}\n\n"
                        f"Thank you for checking! 🙏"
                    )

            else:
                message = (
                    f"❌ *Reference Number Not Found*\n\n"
                    f"We couldn't find any meter concern with reference number:\n"
                    f"`{ref_number}`\n\n"
                    f"💡 Please check:\n"
                    f"• Correct reference number format (e.g., MC-20260123-EA3B68AB)\n"
                    f"• No extra spaces or typos\n\n"
                    f"📞 Need help? Call: 09989893028"
                )

        except Exception as e:
            message = (
                f"❌ *System Error*\n\n"
                f"Unable to retrieve meter concern status.\n"
                f"Please try again later.\n\n"
                f"📞 Hotline: 09989893028"
            )
            print(f"Error in meter concern follow-up: {e}")

        dispatcher.utter_message(text=message)

        return [SlotSet("mc_reference_number", None)]


class ValidateMeterConcernFollowUpForm(FormValidationAction):
    """Validates meter concern reference number"""
    
    def name(self) -> Text:
        return "validate_meter_concern_followup_form"
    
    def validate_mc_reference_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate reference number format"""
        
        if not slot_value or len(slot_value.strip()) < 10:
            dispatcher.utter_message(text=(
                "❌ *Invalid Reference Number*\n\n"
                "Please provide your complete reference number.\n\n"
                "📌 *Format:* MC-YYYYMMDD-XXXXXXXX\n"
                "📌 *Example:* MC-20260123-EA3B68AB\n\n"
                "💡 Check your confirmation message."
            ))
            return {"mc_reference_number": None}
        
        # Basic format validation
        ref_num = slot_value.strip().upper()
        
        # Should start with "MC-"
        if not ref_num.startswith("MC-"):
            dispatcher.utter_message(text=(
                "❌ *Invalid Format*\n\n"
                "Reference numbers should start with 'MC-'\n\n"
                "📌 *Example:* MC-20260123-EA3B68AB\n\n"
                "Please check your reference number and try again."
            ))
            return {"mc_reference_number": None}
        
        return {"mc_reference_number": ref_num}
class ActionRequireTerms(Action):
    """Simple action to block services if terms not accepted"""
    
    def name(self) -> Text:
        return "action_require_terms"
    
    def run(self, dispatcher, tracker, domain):
        if not tracker.get_slot("terms_agreed"):
            dispatcher.utter_message(
                text="⚠️ Please accept our Terms of Use first.",
                buttons=[
                    {"title": "I Agree", "payload": "/accept_terms"}
                ]
            )
            return [SlotSet("terms_agreed", False)]
        return []


class ActionCheckTermsBeforeService(Action):
    """Check terms before showing any service response"""
    def name(self) -> str:
        return "action_check_terms_before_service"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # Block service - show terms
            dispatcher.utter_message(response="utter_greet")
            # Stop further actions by returning ActionExecutionRejection
            from rasa_sdk.events import UserUtteranceReverted
            return [UserUtteranceReverted()]
        # Terms accepted - continue to service
        return []
    
class ActionCheckTermsBeforeForm(Action):
    """Check terms before activating any form"""
    def name(self) -> str:
        return "action_check_terms_before_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # Block form - show terms
            dispatcher.utter_message(response="utter_greet")
            # Use UserUtteranceReverted instead of ActionExecutionRejected
            from rasa_sdk.events import UserUtteranceReverted
            return [UserUtteranceReverted()]
        
        # Terms accepted - allow form to proceed
        return []
    
class ActionCheckTermsAndShowMenu(Action):
    """Check terms before showing menu (for greet intent)"""
    def name(self) -> str:
        return "action_check_terms_and_show_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # Show terms again - user must accept first
            dispatcher.utter_message(response="utter_greet")
            # Return UserUtteranceReverted to stop execution
            from rasa_sdk.events import UserUtteranceReverted
            return [UserUtteranceReverted()]
        
        # Terms accepted - show carousel
        return [FollowupAction("action_show_carousel")]
    
    
class ActionHandleFallbackWithTerms(Action):
    """Handle fallback - show terms if not accepted, else show default message"""
    def name(self) -> str:
        return "action_handle_fallback_with_terms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        terms_agreed = tracker.get_slot("terms_agreed")
        
        if not terms_agreed:
            # User hasn't accepted terms - show terms again
            dispatcher.utter_message(response="utter_greet")
            return []
        
        # User accepted terms but typed nonsense - show helpful message
        dispatcher.utter_message(
            text="🤔 I didn't quite understand that.\n\n"
                 "Please choose an option from the menu or type 'menu' to see options."
        )
        return []

from typing import Any, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionHandleGreet(Action):
    """Handle greet intent: check Terms of Use agreement and display main service carousel"""

    def name(self) -> str:
        return "action_handle_greet"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        # Check if user already agreed to the Terms of Use
        terms_agreed = tracker.get_slot("terms_agreed")

        if not terms_agreed:
            # Show greeting + Terms of Use
            dispatcher.utter_message(response="utter_greet")
            return []

        # Optional polite intro message before carousel
        dispatcher.utter_message(
            text=(
                "Thank you for contacting ILECO. "
                "Please select one of the services below so we may assist you promptly."
            )
        )

        # Carousel elements
        elements = [
            {
                "title": "Power Interruption Reports",
                "subtitle": "Report outages or track power concerns",
                "image_url": "https://i.postimg.cc/hP14f5Gz/Power-Outage.jpg",
                "buttons": [
                    {
                        "type": "web_url",
                        "title": "Report a Power Interruption",
                        "url": "http://127.0.0.1:5000/report_outage"
                    },
                    {
                        "type": "postback",
                        "title": "View Scheduled Interruptions",
                        "payload": "/schedule_outage"
                    },
                    {
                        "type": "postback",
                        "title": "Follow Up on a Report",
                        "payload": "/follow_up_report"
                    }
                ]
            },
            {
                "title": "Billing & Payments",
                "subtitle": "View bills and manage payments securely",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "View Online Billing",
                        "payload": "/online_billing"
                    },
                    {
                        "type": "postback",
                        "title": "View Payment Options",
                        "payload": "/payment_option"
                    }
                ]
            },
            {
                "title": "New Service Connection",
                "subtitle": "Apply for a new electric service connection",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "View Requirements Checklist",
                        "payload": "/requirements_checklist"
                    },
                    {
                        "type": "postback",
                        "title": "View PMOS Schedule",
                        "payload": "/schedule_pmos"
                    },
                    {
                        "type": "postback",
                        "title": "Download Application Forms",
                        "payload": "/download_forms"
                    }
                ]
            },
            {
                "title": "Technical Assistance",
                "subtitle": "Request technical support or meter services",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {
                        "type": "web_url",
                        "title": "Report a Meter Concern",
                        "url": "http://127.0.0.1:5000/meter_concern"
                    },
                    {
                        "type": "postback",
                        "title": "Request Meter Transfer",
                        "payload": "/transfer_of_meter"
                    },
                    {
                        "type": "postback",
                        "title": "Follow Up on Meter Concern",
                        "payload": "/meter_concern_followup"
                    }
                ]
            },
            {
                "title": "Customer Information",
                "subtitle": "Access helpful service and company information",
                "image_url": "https://i.postimg.cc/sXt0kNnD/kari-kamo-upod-kita.jpg",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "View Contact Details",
                        "payload": "/contact_information"
                    },
                    {
                        "type": "postback",
                        "title": "View Electricity Rates",
                        "payload": "/rates"
                    },
                    {
                        "type": "postback",
                        "title": "View Office Locations",
                        "payload": "/office_location"
                    }
                ]
            },
            {
                "title": "Speak with a Live Agent",
                "subtitle": "Get personalized assistance from our support team",
                "image_url": "https://i.postimg.cc/02qJQ0F6/agentwew.jpg",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Chat with a Support Agent",
                        "payload": "/talk_to_agent"
                    }
                ]
            }
        ]

        # Facebook Messenger Generic Template payload
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }

        # Send carousel
        dispatcher.utter_message(json_message=message)

        # Return empty list to wait for user input
        return []
