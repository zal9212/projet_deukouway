from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class SupportHomeView(View):
    """
    Standard support page showing help center topics and FAQs.
    """
    def get(self, request):
        return render(request, 'pages/client/chat.html')


class ChatbotWidgetView(View):
    """
    Distraction-free page designed to be embedded in an iframe for the chatbot drawer.
    """
    def get(self, request):
        return render(request, 'support/chatbot_widget.html')


class ChatbotResponseView(View):
    """
    HTMX endpoint analyzing customer query and returning rule-based chatbot messages.
    """
    def post(self, request):
        user_message = request.POST.get('message', '').strip().lower()
        
        # Simple keywords rule-based matching engine
        if any(kw in user_message for kw in ['bonjour', 'salut', 'hello', 'hey', 'hi']):
            bot_reply = (
                "Bonjour ! Je suis l'assistant intelligent de DEKOUWAY. "
                "Je suis là pour vous guider. Que souhaitez-vous savoir ?"
            )
        elif any(kw in user_message for kw in ['réserver', 'reserver', 'reservation', 'réservation', 'louer']):
            bot_reply = (
                "Pour effectuer une réservation sur DEKOUWAY :<br>"
                "1. Connectez-vous à votre compte client.<br>"
                "2. Rendez-vous sur l'onglet 'Explorer les biens'.<br>"
                "3. Choisissez vos dates sur la fiche du logement puis cliquez sur 'Demander à réserver'.<br>"
                "4. Le propriétaire dispose de 24h pour valider. Une fois acceptée, vous pourrez payer en ligne."
            )
        elif any(kw in user_message for kw in ['payer', 'paiement', 'tarif', 'prix', 'wave', 'orange', 'om', 'carte', 'visa', 'mastercard']):
            bot_reply = (
                "Nous supportons les moyens de paiement locaux les plus sécurisés au Sénégal :<br>"
                "- **Mobile Money** : Wave et Orange Money.<br>"
                "- **Cartes Bancaires** : Visa et Mastercard.<br>"
                "Le paiement s'effectue après validation de la demande par le propriétaire."
            )
        elif any(kw in user_message for kw in ['propriétaire', 'proprietaire', 'publier', 'ajouter', 'annonce', 'bien']):
            bot_reply = (
                "En tant que propriétaire sur DEKOUWAY :<br>"
                "1. Créez un compte 'Propriétaire' et chargez votre pièce d'identité.<br>"
                "2. Après validation manuelle par l'admin, vous aurez accès à votre tableau de bord.<br>"
                "3. Vous pourrez alors publier vos logements, insérer des photos et fixer les tarifs."
            )
        elif any(kw in user_message for kw in ['sécurité', 'securite', 'fiable', 'arnaque', 'vérifié', 'verifie']):
            bot_reply = (
                "DEKOUWAY garantit une sécurité optimale :<br>"
                "- Tous les propriétaires doivent soumettre une pièce d'identité officielle.<br>"
                "- Chaque annonce de logement est vérifiée avant publication.<br>"
                "- Les fonds sont séquestrés et sécurisés jusqu'à la réussite de votre séjour."
            )
        else:
            bot_reply = (
                "Je n'ai pas bien compris votre demande. Je peux vous aider sur :<br>"
                "- Comment **réserver** un logement.<br>"
                "- Les options de **paiement** (Wave, Orange Money, Carte).<br>"
                "- Comment publier en tant que **propriétaire**.<br>"
                "N'hésitez pas à reformuler."
            )

        context = {
            'user_message': request.POST.get('message', ''),
            'bot_reply': bot_reply
        }
        return render(request, 'support/partials/chat_message.html', context)
