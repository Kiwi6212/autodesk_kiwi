import os
import imaplib
import email
import ssl
from email.header import decode_header
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

router = APIRouter(prefix="/email", tags=["Email"])

# --- MODÈLES DE DONNÉES ---
class EmailItem(BaseModel):
    subject: str
    sender: str
    date: str

class EmailSummary(BaseModel):
    count_unread: int
    emails: List[EmailItem] = []
    error: str = ""

# --- ROUTE PROTON (VIA BRIDGE) ---

@router.get("/proton/unread", response_model=EmailSummary)
def get_proton_unread():
    """Récupère les emails via IMAP local (Bridge)"""

    # Use environment variables for credentials
    host = os.getenv("PROTON_BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("PROTON_BRIDGE_PORT", "1143"))
    user = os.getenv("PROTON_BRIDGE_USER")
    password = os.getenv("PROTON_BRIDGE_PASS")

    if not all([user, password]):
        return EmailSummary(count_unread=0, error="Configuration .env incomplète (PROTON_BRIDGE_USER/PASS)")

    print(f"🔍 DEBUG: Connexion sur {host}:{port} avec user='{user}'")

    try:
        # 1. Connexion au Bridge
        mail = imaplib.IMAP4(host, port)
        
        # 2. STARTTLS
        try:
            mail.starttls()
        except Exception as e:
            # Continuer sans STARTTLS si échec
            pass
        
        # 3. Authentification
        mail.login(user, password)
        
        # 4. Sélection de la boite de réception
        mail.select("inbox")

        # 5. Recherche des mails non lus
        status, messages = mail.search(None, "(UNSEEN)")
        
        email_ids = messages[0].split()
        count = len(email_ids)
        
        email_list = []
        
        # On récupère les détails des 5 derniers mails non lus
        # reversed() permet d'avoir les plus récents en premier
        for e_id in reversed(email_ids[-5:]):
            try:
                # Récupère seulement l'en-tête (plus rapide)
                _, msg_data = mail.fetch(e_id, "(RFC822.HEADER)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Décodage du Sujet
                        subject_header = msg["Subject"]
                        subject_text = "(Sans sujet)"
                        if subject_header:
                            decoded_list = decode_header(subject_header)
                            subject_text = ""
                            for text, encoding in decoded_list:
                                if isinstance(text, bytes):
                                    subject_text += text.decode(encoding if encoding else "utf-8", errors="ignore")
                                else:
                                    subject_text += str(text)

                        # Décodage de l'Expéditeur
                        from_header = msg.get("From", "Inconnu")
                        
                        # Date
                        date_header = msg.get("Date", "")

                        email_list.append(EmailItem(
                            subject=subject_text,
                            sender=from_header,
                            date=date_header
                        ))
            except Exception as e:
                print(f"Erreur lecture mail {e_id}: {e}")
                continue

        mail.close()
        mail.logout()
        
        return EmailSummary(
            count_unread=count, 
            emails=email_list
        )

    except ConnectionRefusedError:
        return EmailSummary(count_unread=0, error="Proton Bridge n'est pas lancé ou port incorrect")
    except imaplib.IMAP4.error as e:
        return EmailSummary(count_unread=0, error=f"Erreur IMAP (Login?): {str(e)}")
    except Exception as e:
        print(f"Erreur Inconnue: {e}")
        return EmailSummary(count_unread=0, error=f"Erreur: {str(e)}")

# --- ROUTE HISTORIQUE PAGINÉ (Lazy Loading) ---

class EmailHistoryResponse(BaseModel):
    total_count: int
    emails: List[EmailItem] = []
    has_more: bool = False
    error: str = ""

@router.get("/proton/history", response_model=EmailHistoryResponse)
def get_proton_history(page: int = 1, per_page: int = 20):
    """Récupère l'historique des emails avec pagination (style Twitter)"""
    
    host = os.getenv("PROTON_BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("PROTON_BRIDGE_PORT", "1143"))
    user = os.getenv("PROTON_BRIDGE_USER")
    password = os.getenv("PROTON_BRIDGE_PASS")
    
    if not all([user, password]):
        return EmailHistoryResponse(total_count=0, error="Configuration .env incomplète")
    
    try:
        # Connexion
        mail = imaplib.IMAP4(host, port)
        try:
            mail.starttls()
        except:
            pass
        mail.login(user, password)
        mail.select("inbox")
        
        # Recherche TOUS les emails (pas juste UNSEEN)
        status, messages = mail.search(None, "ALL")
        
        if status != "OK":
            return EmailHistoryResponse(total_count=0, error="Erreur recherche emails")
        
        email_ids = messages[0].split()
        total_count = len(email_ids)
        
        # Pagination: calculer les indices
        # IMPORTANT: On garde l'ordre chronologique (ancien → récent)
        # Pas de reversed() ici pour avoir l'historique complet dans l'ordre
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_ids = email_ids[start_idx:end_idx]
        
        email_list = []
        
        for e_id in page_ids:
            try:
                _, msg_data = mail.fetch(e_id, "(RFC822.HEADER)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Décodage du sujet
                        subject_header = msg["Subject"]
                        subject_text = "(Sans sujet)"
                        if subject_header:
                            decoded_list = decode_header(subject_header)
                            subject_text = ""
                            for text, encoding in decoded_list:
                                if isinstance(text, bytes):
                                    subject_text += text.decode(encoding if encoding else "utf-8", errors="ignore")
                                else:
                                    subject_text += str(text)
                        
                        from_header = msg.get("From", "Inconnu")
                        date_header = msg.get("Date", "")
                        
                        email_list.append(EmailItem(
                            subject=subject_text,
                            sender=from_header,
                            date=date_header
                        ))
            except Exception as e:
                print(f"Erreur lecture mail {e_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        has_more = end_idx < total_count
        
        return EmailHistoryResponse(
            total_count=total_count,
            emails=email_list,
            has_more=has_more
        )
        
    except ConnectionRefusedError:
        return EmailHistoryResponse(total_count=0, error="Proton Bridge non lancé")
    except imaplib.IMAP4.error as e:
        return EmailHistoryResponse(total_count=0, error=f"Erreur IMAP: {str(e)}")
    except Exception as e:
        print(f"Erreur historique: {e}")
        return EmailHistoryResponse(total_count=0, error=f"Erreur: {str(e)}")

# --- ROUTE ENVOI EMAIL (SMTP) ---

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/proton/send")
def send_proton_email(email_data: SendEmailRequest):
    """Envoie un email via SMTP Proton Bridge"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_host = os.getenv("PROTON_BRIDGE_SMTP_HOST", "127.0.0.1")
    smtp_port = int(os.getenv("PROTON_BRIDGE_SMTP_PORT", "1025"))
    smtp_user = os.getenv("PROTON_BRIDGE_SMTP_USER")
    smtp_pass = os.getenv("PROTON_BRIDGE_SMTP_PASS")
    
    if not all([smtp_user, smtp_pass]):
        return {"success": False, "error": "Configuration SMTP incomplète"}
    
    try:
        # Créer le message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_data.to
        msg['Subject'] = email_data.subject
        msg.attach(MIMEText(email_data.body, 'plain'))
        
        # Connexion SMTP
        server = smtplib.SMTP(smtp_host, smtp_port)
        try:
            server.starttls()
        except:
            pass
        server.login(smtp_user, smtp_pass)
        
        # Envoi
        server.send_message(msg)
        server.quit()
        
        return {"success": True, "message": "Email envoyé avec succès"}
        
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return {"success": False, "error": str(e)}

# --- ROUTE RÉSUMÉ GLOBAL (Pour compatibilité future) ---
@router.get("/summary")
def get_summary():
    # Pour l'instant, on ne renvoie que Proton car Outlook est désactivé
    proton_data = get_proton_unread()
    return {
        "outlook": 0,
        "proton": proton_data.count_unread,
        "total": proton_data.count_unread
    }